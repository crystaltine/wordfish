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

# pls no steal (idk why)

TOKEN = apikey.TOKEN

import discord
from parse_command import smart_parse_collect_command
client = discord.Client(intents=discord.Intents.all())

async def send_msg(channel: discord.TextChannel, message: str = "", replyto: discord.Message = None, embed: discord.Embed = None):
    # return the sent message
    return await channel.send(message, reference=replyto, embed=embed)
    
f"""
See docstring for smart_parse_collect_command in parse_command.py for details on how to use the command
{smart_parse_collect_command.__doc__}
"""

def _advance_one_month(d: datetime.datetime):
    if d.month == 12:
        return d.replace(year=d.year+1, month=1)
    return d.replace(month=d.month+1)

def _match_day(d: datetime.datetime, dtarget: datetime.datetime) -> bool:
    return d.day == dtarget.day and d.month == dtarget.month and d.year == dtarget.year

async def _write_cache(message: discord.Message, filename: str):            
    timestamp = datetime.datetime.now()
    messages = []
    async for message in message.channel.history(limit=None, oldest_first=True):
        messages.append({
            "content": message.content, 
            "timestamp": message.created_at.isoformat(), 
            "author": message.author.name,
            "author_id": message.author.id,
        })
    # write timestamp at end
    messages.append(timestamp.isoformat())
    with open(filename, "w") as f:
        f.write(json.dumps(messages))
        f.close()

def run_discord_bot():
    @client.event
    async def on_ready():
        print(f"{client.user} is now running!")
          
    @client.event
    async def on_message(message: discord.Message):
        
        # Ignore messages from self
        if message.author == client.user:
            return
        
        if message.content.startswith("::testprogressbar"):
            embed = discord.Embed(title="Title", description="Description", color=0x00ff00)
            sent = await send_msg(message.channel, embed=embed)

            for i in range(10):
                embed.description = f"Description {i}"
                await sent.edit(embed=embed)
        
        # Reserved for admins
        if message.content.startswith("::cache") and message.author.guild_permissions.administrator:
            filename = f"cache/{message.channel.id}.json"
            await send_msg(
                message.channel,
                "ok",
                replyto=message
            )
            await _write_cache(message, filename)
                           
            await send_msg(
                message.channel,
                f"Saved messages in channel `{message.channel.name}` to file `{filename}`",
                replyto=message
            )

        if message.content.startswith("::help"):
            await send_msg(
                message.channel,
                "Help coming soon, but at least bot is working",
                replyto=message
            )      

        # Command run       
        if message.content.startswith("::collect"):
            
            # init progress bar
            # TODO
            # for now, only do this if cache is already created
            
            _pbar_len: int # number of messages to scan
            # majority of time spent is on scanning messages
            _curr_progress: int = 0 # current progress
            _prev_progress: int = 0 # previous progress (Will be 0.001,0.002,...)
            
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
                await send_msg(
                    message.channel,
                    f"Scanning activity in `{channel.name}`, interval: `{cmdargs['time_window']}`, messages from `{'role: ' + role if role else 'everyone'}`, proportional chart: `{proportional_chart}`...",
                    replyto=message            
                )
                        
                data = await collect(channel, query=None, __orig_msg=message, unique=False, role=role, time=cmdargs["time_window"])
                
                extracted_data: tuple = extract_data(data)   
                
                randhex = uuid.uuid4().hex[0:8]
                timeintervalname = "monthly" if cmdargs["time_window"] == "m" else "weekly" if cmdargs["time_window"] == "w" else "daily"
                _filename = f"graphimgs/ACTIVITY_{channel.name}-{timeintervalname}-{randhex}.png"
                
                try:
                    data_to_graph(*extracted_data, "", cmdargs["time_window"], imgfilename=_filename, proportional_chart=proportional_chart)
                except Exception as e:
                    print(e)
                    await message.channel.send(f"Error: Copying the graph failed too many times. Try again soon.")
                
                file = discord.File(_filename, filename='image.png')
                embed = discord.Embed()
                embed.set_image(url='attachment://image.png')
                await message.channel.send(file=file, embed=embed)      
                return            
                      
            await send_msg(
                message.channel,
                f"Collecting `'{query}'` in `{channel.name}`, interval: `{cmdargs['time_window']}`, messages from `{'role: ' + role if role else 'everyone'}`, proportional chart: `{proportional_chart}`...",
                replyto=message            
            )
            
            data: ...
            if cmdargs.get("ignore_cache"):
                filename = f"cache/{message.channel.id}.json"
                await send_msg(
                    message.channel,
                    f"Writing new cache for `{message.channel.name}` to file `{filename}`",
                )
                await _write_cache(message, filename)
            
            
            data = await collect(channel, query, __orig_msg=message, unique=False, role=role, time=cmdargs["time_window"])
            
            extracted_data: tuple = extract_data(data)   
                
            randhex = uuid.uuid4().hex[0:8]
            timeintervalname = "monthly" if cmdargs["time_window"] == "m" else "weekly" if cmdargs["time_window"] == "w" else "daily"
            _filename = f"graphimgs/{query}-{channel.name}-{timeintervalname}-{randhex}.png"
            
            data_to_graph(*extracted_data, cmdargs["query"], cmdargs["time_window"], imgfilename=_filename, proportional_chart=proportional_chart)
            
            file = discord.File(_filename, filename='image.png')
            embed = discord.Embed()
            embed.set_image(url='attachment://image.png')
            await message.channel.send(file=file, embed=embed)    
    client.run(TOKEN)

async def collect(
    channel: discord.TextChannel, 
    query: str, 
    __orig_msg: discord.Message,
    unique = False, 
    role: str = None, 
    time: str = "w", 
    use_cache = True,
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
            
            print(f"Message with timestamp {timestamp} has started a new (monthly) timewindow")

            curr_data = {}
            
            # Add any skipped months to data as empty
            while not _match_day(curr_timewindow_start, timestamp.replace(day=1)): # As long as curr hasnt reached timestamp's month
                curr_timewindow_start = _advance_one_month(curr_timewindow_start)
                data[str(curr_timewindow_start)] = {}
                
            return curr_timewindow_start.replace(year=timestamp.year, month=timestamp.month)
        
        elif time != "m":
            _timedel = datetime.timedelta(days=1) if time == "d" else datetime.timedelta(weeks=1)
            if timestamp > curr_timewindow_start + _timedel:
                print(f"Message with timestamp {timestamp} has started a new timewindow.")
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
        except FileNotFoundError: await _write_cache(__orig_msg, f"cache/{channel.id}.json")
        
        with open(f"cache/{channel.id}.json", "r") as f:
            loaded_data = list(json.load(f))
            
            _pbar_len = len(loaded_data)
            
            file_timestamp = loaded_data.pop()
            await send_msg(
                __orig_msg.channel,
                f"Using cache for this channel dated `{file_timestamp}`. Run with `--ignore-cache` to write a new cache. Note that rescanning is slow and can only cover ~95 messages per second.",
            )
            
            for message in loaded_data: # message is dict
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
                
                #_curr_progress += 1
                # edit embed if delta _curr_progress/len(loaded_data) > 0.001 (every 0.1%)
                #if _curr_progress/_pbar_len - _prev_progress > 0.001:
    
    # save last time window
    data[str(curr_timewindow_start)] = curr_data
    
    return data

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