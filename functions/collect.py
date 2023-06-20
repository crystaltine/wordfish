import discord
import datetime
from datetime import timezone
import json
from dateutil import parser

from error import send_error_embed, send_warning_embed
from functions.progress_bar import ProgressBar
from functions.utils import _advance_one_month, _match_day, INTERVAL_NAMES, _search_queries
from functions.write_cache import _write_cache

async def collect(
    channel: discord.TextChannel, 
    query: str, 
    __orig_msg: discord.Message,
    unique = False, 
    role: str | list = None, 
    time: str = "w", 
    _for_prop_chart = False,
    include_bots = False
    ):
    # If d or w, start based on exact time of first message; m based on calendar month of first message
    _timestamp_0 = None
    async for message in channel.history(limit=1, oldest_first=True):
        _timestamp_0 = message.created_at
        break
    
    if _timestamp_0 is None:
        send_error_embed(
            __orig_msg.channel,
            details=f"No messages found in channel {channel.mention}!"
        )
    
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
    
    runtime_timestamp = datetime.datetime.now(timezone.utc)
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

    # ---------------------#
    # MAIN DATA COLLECTION #
    # ---------------------#

    try: open(f"cache/{channel.id}.json", "r")
    except FileNotFoundError: 
        filename = f"cache/{channel.id}.json"
        await _write_cache(channel, filename, send_embed_to=__orig_msg.channel)
    
    with open(f"cache/{channel.id}.json", "r", encoding='UTF-8') as f:
        loaded_data = list(json.load(f))
        loaded_data.pop() # remove timestamp
        
        # progress bar stuff
        progress = 0
        total_messages = len(loaded_data)-1
        
        # if no role specified keep it at temp while sorting out invalid roles
        
        if type(role) == list:
            _role = []
            for _r in role:
                newrole = discord.utils.get(channel.guild.roles, name=_r)
                if newrole is None:
                    await send_error_embed(__orig_msg.channel, details=f"Role '{_r}' does not exist in server '{channel.guild.name}'. Make sure the parameter is the name of a role (not its @mention) in double quotes.")
                    return
                _role.append(newrole)

        else:
            _role = "temp-no-role" if not role else discord.utils.get(channel.guild.roles, name=role)
            if _role is None: # Role was provided but does not exist
                await send_error_embed(__orig_msg.channel, details=f"Role '{role}' does not exist in server '{channel.guild.name}'. Make sure the parameter is the name of a role (not its @mention) in double quotes.")
                return
        if not role: _role = None # If no role specified, set to None
        
        details = {
            "target_channel": channel,
            "query": query,
            "interval": INTERVAL_NAMES[time],
            "proportional_chart": _for_prop_chart,
            "role": _role,
            "original_channel": __orig_msg.channel,
            "include_bots": include_bots
        }
        pbar = ProgressBar(__orig_msg, details=details)
        await pbar.initialize_message()
        
        num_skipped = 0
        num_members_tracked = 0 # once over 100, stop tracking members
        for message in loaded_data: # message is dict
            try:
                sender = message["author"]
                sender_id = message["author_id"]
                
                # parse timestamp
                timestamp = parser.parse(message["timestamp"])
                
                sender_as_member = channel.guild.get_member(sender_id)
                if not sender_as_member:
                    continue
                
                # if include_bots is true, skip if sender is bot
                if sender_as_member.bot and not include_bots:
                    continue
                
                if type(role) == "str" and role not in set([r.name for r in sender_as_member.roles]) or \
                type(role) == list and not any([r in set([r.name for r in sender_as_member.roles]) for r in role]):
                    continue
                
                new_start = _check_advance_window(time, timestamp, curr_timewindow_start, data, curr_data)
    
                if new_start:
                    curr_timewindow_start = new_start
                    curr_data = {}
                
                ct = _search_queries(message["content"], query)
                try:
                    curr_data[sender] = curr_data.get(sender) + ct
                except TypeError:
                    if num_members_tracked < 100:
                        curr_data[sender] = ct
                    else:
                        # send warning embed
                        await send_warning_embed(
                            send_to_channel=__orig_msg.channel,
                            details=f"Stopped tracking new users after 100 unique detections. Use `--roles` (see `::help`) to filter to specific users.",
                        )
                
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
