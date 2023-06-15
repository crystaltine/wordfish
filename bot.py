import datetime
import uuid
import json # debug
import shlex
import apikey
import sys, os
from dateutil import parser
import json_to_csv
from extract_data import extract_data
from data_to_graph import data_to_graph
from time import sleep
from progress_bar import ProgressBar
from xlsxwriter.exceptions import EmptyChartSeries

# pls no steal (idk why)

TOKEN = apikey.TOKEN

import discord
from parse_command import smart_parse_collect_command
client = discord.Client(intents=discord.Intents.all())

async def send_msg(
    channel: discord.TextChannel, 
    message: str = "", 
    replyto: discord.Message = None, 
    embed: discord.Embed = None,
    file: discord.File = None
):
    # return the sent message
    return await channel.send(message, reference=replyto, embed=embed, file=file)
    
f"""
See docstring for smart_parse_collect_command in parse_command.py for details on how to use the command
{smart_parse_collect_command.__doc__}
"""

INTERVAL_NAMES = {
    "d": "Day",
    "w": "Week",
    "m": "Month",
}

def _advance_one_month(d: datetime.datetime):
    if d.month == 12:
        return d.replace(year=d.year+1, month=1)
    return d.replace(month=d.month+1)

def _match_day(d: datetime.datetime, dtarget: datetime.datetime) -> bool:
    return d.day == dtarget.day and d.month == dtarget.month and d.year == dtarget.year

async def _write_cache(channel: discord.TextChannel, filename: str, send_embed_to: discord.TextChannel = None):   
    
    if not send_embed_to:
        send_embed_to = channel
        
    # if cache file already exists, only get messasges after the last timestamp
    messages = []
    after = None
    orig_len = None

    if os.path.exists(filename):
        with open(filename, "r", encoding='UTF-8') as f:
            messages = list(json.load(f))
            after = parser.isoparse(messages.pop())
            orig_len = len(messages)
    
    init_desc = \
        f"Scanned messages: 0\nRate: N/A" if not after else \
        f"Adding to cache dated {after} with {len(messages)} messages...\n\nScanned messages: 0\nRate: N/A"
    info_embed = discord.Embed(title=f":notepad_spiral: Caching {channel.mention}", description=init_desc, color=0x00ff00)
    last_info_update = datetime.datetime.now()
    sent = await send_msg(send_embed_to, embed=info_embed)
    
    init_timestamp = datetime.datetime.now()
    async for msg in channel.history(limit=None, oldest_first=True,after=after):
        messages.append({
            "content": msg.content, 
            "timestamp": msg.created_at.isoformat(), 
            "author": msg.author.name,
            "author_id": msg.author.id,
        })
        
        _timestamp = datetime.datetime.now()
        if _timestamp - last_info_update > datetime.timedelta(seconds=1):
            rate = len(messages) / (_timestamp - init_timestamp).total_seconds() # messages per second
            hours_taken = (_timestamp - init_timestamp).total_seconds() // 3600
            minutes_taken = ((_timestamp - init_timestamp).total_seconds() % 3600) // 60
            seconds_taken = round(((_timestamp - init_timestamp).total_seconds() % 3600) % 60, 2)
            
            elapsed_time_str = f"{hours_taken}h {minutes_taken}m {seconds_taken}s"
            info_embed.description = f"Adding to cache dated {after} with {len(messages)} messages...\n\n" if after \
                else ""
            info_embed.description += f"**Scanned messages:** {'{:,}'.format(len(messages))}\n**Rate:** {rate:.2f} messages/sec\n**Elapsed Time:** {elapsed_time_str}"
            await sent.edit(embed=info_embed)
            last_info_update = _timestamp
    final_timestamp = datetime.datetime.now()
    # write timestamp at end
    sleep(max(0, (final_timestamp - last_info_update).total_seconds())) # to prevent editing failing
    info_embed.description = f"Writing cached messages to `{filename}`..."
    await sent.edit(embed=info_embed)
    messages.append(init_timestamp.isoformat())
    with open(filename, "w") as f:
        f.write(json.dumps(messages))
        f.close()
    
    # edit embed to show completion
    info_embed.title = ":white_check_mark: Done!"
    
    _init_iso_split = init_timestamp.isoformat().split("T")
    readable_timestamp = _init_iso_split[0] + " " + _init_iso_split[1].split(".")[0]
    
    hours_taken = (final_timestamp - init_timestamp).total_seconds() // 3600
    minutes_taken = ((final_timestamp - init_timestamp).total_seconds() % 3600) // 60
    seconds_taken = round(((final_timestamp - init_timestamp).total_seconds() % 3600) % 60, 2)
    
    elapsed_time_str = f"{hours_taken}h {minutes_taken}m {seconds_taken}s"
    
    avg_rate = round(len(messages) / (final_timestamp - init_timestamp).total_seconds(), 2)
    info_embed.description = f"**{'{:,}'.format(len(messages))} messages** in `{channel.name}` saved as of **{readable_timestamp}**\n\n**Total Time:** {elapsed_time_str}\n**Average Rate**: {avg_rate} messages/sec"
    if after:
        avg_rate = round((len(messages) - orig_len) / (final_timestamp - init_timestamp).total_seconds(), 2)
        info_embed.description = f"**{'{:,}'.format(len(messages) - orig_len)} messages** in `{channel.name}` added as of **{readable_timestamp}**\n\n**Total Time:** {elapsed_time_str}\n**Average Rate**: {avg_rate} messages/sec"
    await sent.edit(embed=info_embed)
        
def run_discord_bot():
    @client.event
    async def on_ready():
        print(f"{client.user} is now running!")
          
    @client.event
    async def on_message(message: discord.Message):
        
        # Ignore messages from self
        if message.author == client.user:
            return

        if message.content.startswith("::cache") and message.author.guild_permissions.administrator:
            _channel = None
            if len(message.content.split(" ")) >= 2:
                
                _param = message.content.split(" ")[1]
                
                if _param == "here":
                    _channel = message.channel
                else:
                    try:
                        _channel = client.get_channel(int(_param))
                    except:
                        pass
                    
                if not _channel: # user specified an invalid channel
                    info_embed = discord.Embed(title=":x: Error", description=f"Channel with id {message.content.split(' ')[1]}` was not found. Double check the channel ID and make sure Wordfish is present in the specified channel's server.", color=0xff0000)
                    await send_msg(message.channel, embed=info_embed, replyto=message)
                    return
                
                # user specified a valid channel
                filename = f"cache/{_channel.id}.json"
                await _write_cache(_channel, filename, send_embed_to=message.channel)
                return
            
            # no specified channel, use current channel
            filename = f"cache/{message.channel.id}.json"
            await _write_cache(message.channel, filename)

        if message.content.startswith("::help"):
            await send_msg(
                message.channel,
                "Help coming soon, but at least bot is working",
                replyto=message
            )      

        # Command run       
        if message.content.startswith("::collect"):
            
            __exception = None

            cmdargs = smart_parse_collect_command(message)
            
            if cmdargs.get("error"):
                await send_msg(message.channel, cmdargs["error"], replyto=message)
                return
            
            query = cmdargs["query"]            
            channel = client.get_channel(cmdargs["channel_id"])
            role = cmdargs["role"]
            proportional_chart = cmdargs["proportional"]
                      
            # If query is empty, then we are collecting activity
            if query == "":
                
                # confirmation message removed; progress bar embed is sent instead
                #await send_msg(
                #    message.channel,
                #    f"Scanning activity in `{channel.name}`, interval: `{cmdargs['time_window']}`, messages from `{'role: ' + role if role else 'everyone'}`, proportional chart: `{proportional_chart}`...",
                #    replyto=message            
                #)
                        
                data, _embed, _msg = await collect(
                    channel, 
                    query=None, 
                    __orig_msg=message, 
                    unique=False, 
                    role=role, 
                    time=cmdargs["time_window"], 
                    _for_prop_chart=proportional_chart
                )
                
                extracted_data: tuple = extract_data(data)   
                
                randhex = uuid.uuid4().hex[0:8]
                timeintervalname = "monthly" if cmdargs["time_window"] == "m" else "weekly" if cmdargs["time_window"] == "w" else "daily"
                _filename = f"graphimgs/ACTIVITY_{channel.name}-{timeintervalname}-{randhex}.png"
                
                try:
                    data_to_graph(*extracted_data, "", cmdargs["time_window"], imgfilename=_filename, proportional_chart=proportional_chart)
                except(EmptyChartSeries) as empty_chart_except:
                    await _msg.delete()
                    _role = discord.utils.get(channel.guild.roles, name=role) if role else None
                    _embed.title = f":jar: No users found under {_role.mention}"
                    _embed.description = _embed.description[:-16]
                    await send_msg(channel=message.channel, embed=_embed)             
                    return 
                except Exception as e:
                    await _msg.delete()
                    _embed.title = f":x: Error"
                    _embed.description = f"An error occurred while generating the graph:\n```{e}```"
                    await send_msg(channel=message.channel, embed=_embed)             
                    return 
                
                file = discord.File(_filename, filename='image.png')
                _embed.set_image(url="attachment://image.png")
                await _msg.delete()
                _embed.description = _embed.description[:-16]
                await send_msg(channel=message.channel, embed=_embed, file=file)                   
                return            
        
            # confirmation replaced by progress bar     
            #await send_msg(
            #    message.channel,
            #    f"Collecting `'{query}'` in `{channel.name}`, interval: `{cmdargs['time_window']}`, messages from `{'role: ' + role if role else 'everyone'}`, proportional chart: `{proportional_chart}`...",
            #    replyto=message            
            #)
            
            data: ...
            if cmdargs.get("ignore_cache"):
                filename = f"cache/{message.channel.id}.json"
                #await send_msg(
                #    message.channel,
                #    f"Writing new cache for `{message.channel.name}` to file `{filename}`",
                #)
                await _write_cache(message, filename)
            
            
            data, _embed, _msg = await collect(
                channel, 
                query, 
                __orig_msg=message, 
                unique=False, 
                role=role, 
                time=cmdargs["time_window"], 
                _for_prop_chart=proportional_chart
            )
            
            extracted_data: tuple = extract_data(data)   
                
            randhex = uuid.uuid4().hex[0:8]
            timeintervalname = "monthly" if cmdargs["time_window"] == "m" else "weekly" if cmdargs["time_window"] == "w" else "daily"
            _filename = f"graphimgs/{query}-{channel.name}-{timeintervalname}-{randhex}.png"
            
            try:
                data_to_graph(*extracted_data, cmdargs["query"], cmdargs["time_window"], imgfilename=_filename, proportional_chart=proportional_chart)
            except(EmptyChartSeries) as empty_chart_except:
                await _msg.delete()
                print(f"LOoking for role {role} in server {channel.guild.name}")
                _role = discord.utils.get(channel.guild.roles, name=role) if role else None
                _embed.title = f":jar: {f'No users found under {_role.mention}' if _role else f'@{role} does not exist!'}"
                _embed.description = _embed.description[:-16]
                await send_msg(channel=message.channel, embed=_embed)             
                return 
                
            file = discord.File(_filename, filename='image.png')            
            _embed.set_image(url="attachment://image.png")
            await _msg.delete()
            _embed.description = _embed.description[:-16]
            
            await send_msg(channel=message.channel, embed=_embed, file=file)                   
            return     
    client.run(TOKEN)

async def collect(
    channel: discord.TextChannel, 
    query: str, 
    __orig_msg: discord.Message,
    unique = False, 
    role: str = None, 
    time: str = "w", 
    use_cache = True,
    _for_prop_chart = False
    ):
    
    # If d or w, start based on exact time of first message; m based on calendar month of first message
    _timestamp_0 = 0
    async for message in channel.history(limit=1, oldest_first=True):
        _timestamp_0 = message.created_at
        break
    
    if time == "m":
        _timestamp_0 = _timestamp_0.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    _dtime = datetime.timedelta(days=1) if time == "d" else datetime.timedelta(weeks=1)
    
    data = {}
    curr_data = {}
    
    # Setup return
    # Series of time 'buckets'
    # For d and w, index 0 begins at first message and goes exactly 1d or 1w onwards. For m, it is the calendar month of the first message
    # For d and w, that means the last bucket might be incomplete, but for m, the first bucket might be incomplete   
    curr = _timestamp_0
    
    runtime_timestamp = datetime.datetime.now()
    # Prepopulate data with empty buckets, so collapse doesnt occur when messages are sparse
    if time != "m":
        while curr.timestamp() < runtime_timestamp.timestamp():
            data[str(curr)] = {}
            curr += _dtime
            
    else:
        while curr.month <= runtime_timestamp.month:
            _start_of_month = curr.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            data[str(_start_of_month)] = {}
            curr = _advance_one_month(curr)
            
    def _check_advance_window(
        time: str,
        timestamp: datetime.datetime,
        curr_timewindow_start: datetime.datetime,
        data: dict,
        curr_data: dict
        ) -> datetime.datetime:
        
        """
        Returns `datetime.datetime` of new time window start, if `timestamp` is in a new time window.
        Otherwise, returns None
        """
        
        loaded_data: ...
        
        if time == "m" and timestamp.month != curr_timewindow_start.month:            
            data[str(curr_timewindow_start)] = curr_data.copy()
            
            #print(f"Message with timestamp {timestamp} has started a new (monthly) timewindow")

            curr_data = {}
            
            # Add any skipped months to data as empty
            while not _match_day(curr_timewindow_start, timestamp.replace(day=1)): # As long as curr hasnt reached timestamp's month
                curr_timewindow_start = _advance_one_month(curr_timewindow_start)
                data[str(curr_timewindow_start)] = {}
                
            return curr_timewindow_start.replace(year=timestamp.year, month=timestamp.month)
        
        elif time != "m":
            _timedel = datetime.timedelta(days=1) if time == "d" else datetime.timedelta(weeks=1)
            if timestamp > curr_timewindow_start + _timedel:
                #print(f"Message with timestamp {timestamp} has started a new timewindow.")
                data[str(curr_timewindow_start)] = curr_data.copy()                
                curr_data = {}
                
                # Keep going up by 1 week until we reach timestamp (before we hit)
                while timestamp > curr_timewindow_start + _timedel:
                    curr_timewindow_start += _timedel
                    data[str(curr_timewindow_start)] = {}
                
                return curr_timewindow_start
        
        return None
    
    curr_timewindow_start = _timestamp_0

    if use_cache: # always use cache lol, too lazy to reformat
        try: open(f"cache/{channel.id}.json", "r")
        except FileNotFoundError: 
            filename = f"cache/{channel.id}.json"
            await send_msg(
                message.channel,
                f"Writing new cache for `{message.channel.name}` to file `{filename}`",
            )
            await _write_cache(__orig_msg, filename)
        
        with open(f"cache/{channel.id}.json", "r") as f:
            loaded_data = list(json.load(f))
            loaded_data.pop() # remove timestamp
            
            # progress bar stuff
            progress = 0
            total_messages = len(loaded_data)-1
            
            _role = discord.utils.get(channel.guild.roles, name=role) if role else None
            
            details = {
                "target_channel": channel,
                "query": query,
                "interval": INTERVAL_NAMES[time],
                "proportional_chart": _for_prop_chart,
                "role": _role,
                "original_channel": __orig_msg.channel,
            }
            pbar = ProgressBar(__orig_msg, details=details)
            await pbar.initialize_message()
            
            #file_timestamp = loaded_data.pop()
            #await send_msg(
            #    __orig_msg.channel,
            #    f"Using cache for this channel dated `{file_timestamp}`. Run with `--ignore-cache` to write a new cache. Note that rescanning is slow and can only cover ~95 messages per second.",
            #)
            
            num_skipped = 0
            for message in loaded_data: # message is dict
                try:
                    sender = message["author"]
                    sender_id = message["author_id"]
                    
                    # parse timestamp
                    timestamp = parser.parse(message["timestamp"])
                    
                    sender_as_member = channel.guild.get_member(sender_id)
                    if not sender_as_member:
                        continue
                    
                    if role and role not in set([r.name for r in sender_as_member.roles]):
                        continue
                    
                    new_start = _check_advance_window(time, timestamp, curr_timewindow_start, data, curr_data)
        
                    if new_start:
                        curr_timewindow_start = new_start
                        curr_data = {}
                    
                    ct = _search_queries(message["content"], query)
                    curr_data[sender] = curr_data.get(sender, 0) + ct
                    
                    progress += 1
                    await pbar.update(progress / total_messages)
                except Exception as e:
                    print(f"Error while parsing message in collect: {e}")
                    num_skipped += 1
                    continue
            _embed, _msg = await pbar.update(1)
    # save last time window
    data[str(curr_timewindow_start)] = curr_data
    
    return data, _embed, _msg

def _search_queries(msg: discord.Message | str, target: str, get_count = True) -> int | bool:
    """
    + If `get_count` is `False`, returns `True` if `target` is in `msg`, `False` otherwise.
    + If `get_count` is `True` (default), returns the number of occurences of `target` in `msg`.
    
    + If `target` is `None`, return 1 (for 1 message)
    """
    
    if target is None: return 1
    
    string: str = msg
    if type(msg) == discord.Message:
        string = msg.content
        
    return string.lower().count(target.lower()) if get_count else target in string