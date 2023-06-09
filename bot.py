import datetime
import uuid
import json # debug
import shlex

# pls no steal (idk why)
TOKEN = "MTA5NDQ1MzIyMzI3ODAwMjI1OQ.GJ9G7R.9VzkSdEYxLk8YPMEyHVA_GZkvDkiZeRDp6Dvdc"

import discord
from parse_command import parse_collect_command
client = discord.Client(intents=discord.Intents.all())

async def send_msg(channel: discord.TextChannel, message: str = "", replyto: discord.Message = None, embed: discord.Embed = None):
    if replyto:
        await channel.send(message, reference=replyto)
    else:
        await channel.send(message)

"""
Collect occurences of string in a channel.
- Be able to sort based on name (for small servers) or by role
- Sort occurences by time (custom time setting, default 1 wk)

Outputs stacked barchart
sample cmd: 
`::collect 234791234687892394891610304 hmmmmmmmmm -w`
           ^channel id                 ^query

`::collect 234791234687892394891610304 hmmmmmmmmm -m --role role`
"""

def _advance_one_month(d: datetime.datetime):
    if d.month == 12:
        return d.replace(year=d.year+1, month=1)
    return d.replace(month=d.month+1)

def _match_day(d: datetime.datetime, dtarget: datetime.datetime) -> bool:
    return d.day == dtarget.day and d.month == dtarget.month and d.year == dtarget.year

def run_discord_bot():
    @client.event
    async def on_ready():
        print(f"{client.user} is now running!")
          
    @client.event
    async def on_message(message: discord.Message):
        
        # Ignore messages from self
        if message.author == client.user:
            return

        if message.content.startswith("::help"):
            await send_msg(
            message.channel,
            "Help coming soon, but at least bot is working",
            replyto=message
        )      

        # Command run       
        if message.content.startswith("::collect"):
            
            cmdargs = parse_collect_command(message)
            
            if cmdargs.get("error"):
                await send_msg(message.channel, cmdargs["error"], replyto=message)
                return
            
            query = cmdargs["query"]
            channel = client.get_channel(cmdargs["channel_id"])
            role = cmdargs["role"]
                      
            await send_msg(
                message.channel,
                f"Collecting `'{query}'` in `{channel.name}`, window size: `{cmdargs['time_window']}`, surveying messages from `{'role: ' + role if role else 'everyone'}`...",
                replyto=message            
            )
                      
            data = await collect(channel, query, unique=False, role=role, time=cmdargs["time_window"])
            
            randhex = uuid.uuid4().hex[0:8]
            timeintervalname = "monthly" if cmdargs["time_window"] == "m" else "weekly" if cmdargs["time_window"] == "w" else "daily"
            filename = f"datafiles/{channel.name}-{timeintervalname}-{randhex}.json"
            with open(filename, "w") as f:
                json.dump(data, f)
                f.close()
            await send_msg(message.channel, f"Data saved to `{filename}`", replyto=message)
            
    client.run(TOKEN)

# TODO
async def collect(channel: discord.TextChannel, query: str, unique = False, role: str = None, time: str = "w"):
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
    
    # Separate loop for month, so that other one doesnt have to check if time == "m" every time
    async for message in channel.history(limit=None, oldest_first=True):
        sender = message.author
        timestamp = message.created_at
        
        # If role is specified, skip if sender does not have role
        if role and role not in set([r.name for r in sender.roles]):
            # Check for role is not none, in case for some reason a server
            # has a role with name None
            continue
        
        new_start = _check_advance_window(time, timestamp, curr_timewindow_start, data, curr_data)
        
        # if new time window, data has been updated and curr_data is empty
        if new_start:
            curr_timewindow_start = new_start # Move to new window, keep updating as usual
            curr_data = {}
        
        ct = _search_queries(message, query)
        curr_data[sender.name] = curr_data.get(sender.name, 0) + ct
    
    # Save last time window
    data[str(curr_timewindow_start)] = curr_data
    return data

def _search_queries(msg: discord.Message | str, target: str, get_count = True) -> int | bool:
    """
    + If `get_count` is `False`, returns `True` if `target` is in `msg`, `False` otherwise.
    + If `get_count` is `True` (default), returns the number of occurences of `target` in `msg`.
    """
    string: str = msg
    if type(msg) == discord.Message:
        string = msg.content
        
    return string.lower().count(target.lower()) if get_count else target in string



#def check_for_hmmm(msg: discord.Message | str) -> int:
#    """
#    Returns the length of the first 'hmmmm' in a `discord.Message` or `str` object. Returns len of hmm string:
#    i.e. 'hmm' -> 3, 'hm' -> 2, etc. Returns 0 (which can be interpreted as `False`) if no hmmmm
#    """
#    string: str = msg
#    if type(msg) == discord.Message:
#        string = msg.content
#    
#    try: ind = string.index('hm')
#    except: return 0
#    ind += 2; hm_len = 2
#    while ind < len(string) and string[ind] == 'm':
#        ind += 1
#        hm_len += 1
#    return hm_len