import discord
import uuid
import traceback
from xlsxwriter.exceptions import EmptyChartSeries

from error import send_error_embed
from _CONSTANTS import COLOR_CODE_MAGENTA, COLOR_CODE_YELLOW, COLOR_CODE_RED, COLOR_CODE_RESET
_y = COLOR_CODE_YELLOW
_r = COLOR_CODE_RED
_m = COLOR_CODE_MAGENTA
_x = COLOR_CODE_RESET

from functions.utils import send_msg
from functions.parse_command import smart_parse_collect_command
from functions.data_to_graph import data_to_graph
from functions.collect import collect
from functions.extract_data import extract_data

async def __read_collect_msg(message: discord.Message, client: discord.Client):
    if message.content.replace('\n', "").startswith("::collect "):
        print(f"In {_m}{message.channel.guild}{_x} > {_y}{message.channel.name}{_x}: {message.content} ({_m}{message.channel.guild.id}{_x} > {_y}{message.channel.id}{_x})")      
        __exception = None

        cmdargs = smart_parse_collect_command(message)
        if cmdargs.get("error"):
            await send_error_embed(
                message.channel,
                details=cmdargs["error"]
            )
            return
        
        query = cmdargs["query"]
        if cmdargs["channel_id"] == 532899347234:
            await send_error_embed(
                message.channel,
                details="nice try nerd"
            )
            return                         
        channel = client.get_channel(cmdargs["channel_id"])
        role = cmdargs["role"]
        
        proportional_chart = cmdargs["proportional"]
        include_bots = cmdargs["include_bots"]
                
        # If query is empty, then we are collecting activity
        if query == "":
            
            # confirmation message removed; progress bar embed is sent instead
            #await send_msg(
            #    message.channel,
            #    f"Scanning activity in `{channel.name}`, interval: `{cmdargs['time_window']}`, messages from `{'role: ' + role if role else 'everyone'}`, proportional chart: `{proportional_chart}`...",
            #    replyto=message            
            #)
                    
            try:
                data, _embed, _msg = await collect(
                    channel, 
                    query=None, 
                    __orig_msg=message, 
                    unique=False, 
                    role=role, 
                    time=cmdargs["time_window"], 
                    _for_prop_chart=proportional_chart,
                    include_bots=include_bots
                )
            except Exception as e:
                traceback.print_exc()
                return
            
            extracted_data: tuple = extract_data(data)   
            
            randhex = uuid.uuid4().hex[0:8]
            timeintervalname = "monthly" if cmdargs["time_window"] == "m" else "weekly" if cmdargs["time_window"] == "w" else "daily"
            _filename = f"graphimgs/ACTIVITY_{channel.name}-{timeintervalname}-{randhex}.png"
            
            try:
                data_to_graph(*extracted_data, "", cmdargs["time_window"], imgfilename=_filename, proportional_chart=proportional_chart)
            except(EmptyChartSeries) as empty_chart_except:
                await _msg.delete()
                traceback.print_exc()
                _role = discord.utils.get(channel.guild.roles, name=role) if role else None
                _embed.title = f":jar: No data found for the given parameters!"
                _embed.description = _embed.description[:-16]
                _embed.color = 0xffff00
                await send_msg(channel=message.channel, embed=_embed)             
                return 
            except Exception as e:
                print(f"-" * 40 + "> Error <" + "-" * 40)
                traceback.print_exc()
                print(f"The above occured in server {_m}{message.guild.name}{_x} in channel {_y}{message.channel.name}{_x}")
                print(f"Command sent: {_r}{message.content}{_x}")
                print(f"-" * 40 + "> Error <" + "-" * 40)
                await send_error_embed(message.channel, e, "An error occured while generating the graph:\n")         
                return 
            
            file = discord.File(_filename, filename='image.png')
            _embed.set_image(url="attachment://image.png")
            await _msg.delete()
            _embed.description = _embed.description[:-16]
            await send_msg(channel=message.channel, embed=_embed, file=file)                   
            return            

        data, _embed, _msg = await collect(
            channel, 
            query, 
            __orig_msg=message, 
            unique=False, 
            role=role, 
            time=cmdargs["time_window"], 
            _for_prop_chart=proportional_chart,
            include_bots=include_bots
        )
        
        extracted_data: tuple = extract_data(data)   
            
        randhex = uuid.uuid4().hex[0:8]
        timeintervalname = "monthly" if cmdargs["time_window"] == "m" else "weekly" if cmdargs["time_window"] == "w" else "daily"
        _filename = f"graphimgs/{query}-{channel.name}-{timeintervalname}-{randhex}.png"
        
        try:
            data_to_graph(*extracted_data, cmdargs["query"], cmdargs["time_window"], imgfilename=_filename, proportional_chart=proportional_chart)
        except(EmptyChartSeries) as empty_chart_except:
            await _msg.delete()
            _role = discord.utils.get(channel.guild.roles, name=role) if role else None
            _embed.title = f":jar: {f'No data found for the given parameters!'}"
            _embed.description = _embed.description[:-16]
            _embed.color = 0xffff00
            await send_msg(channel=message.channel, embed=_embed)             
            return 
            
        file = discord.File(_filename, filename='image.png')            
        _embed.set_image(url="attachment://image.png")
        await _msg.delete()
        _embed.description = _embed.description[:-16]
        
        await send_msg(channel=message.channel, embed=_embed, file=file)                   
        return