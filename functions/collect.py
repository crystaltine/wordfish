import traceback
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
        # No need to throw a top level error here, no issues with the bot
    
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
        
        # Month is different because we want to start a new month when the month changes, not in increments after the first message
        if time == "m" and timestamp.month != curr_timewindow_start.month:            
            data[str(curr_timewindow_start)] = curr_data.copy()
            
            #print(f"Message with timestamp {timestamp} has started a new (monthly) timewindow")

            curr_data = {}
            
            # Add any skipped months to data as empty
            while not _match_day(curr_timewindow_start, timestamp.replace(day=1)): # As long as curr hasnt reached timestamp's month
                curr_timewindow_start = _advance_one_month(curr_timewindow_start)
                data[str(curr_timewindow_start)] = {}
                
            return curr_timewindow_start.replace(year=timestamp.year, month=timestamp.month)
        
        # for day and week, we want to start a new time window when the timestamp is more than-
        # 1 day or 1 week after the current time window start instead of when the day or week changes
        elif time != "m":
            _timedel = datetime.timedelta(days=1) if time == "d" else datetime.timedelta(weeks=1)
            if timestamp > curr_timewindow_start + _timedel:
                #print(f"Message with timestamp {timestamp} has started a new timewindow.")
                data[str(curr_timewindow_start)] = curr_data.copy()                
                curr_data = {}
                
                # Keep going up by 1 week/day until we reach timestamp (before we hit)
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
    except FileNotFoundError: # Write a new cache file if it doesnt exist yet
        filename = f"cache/{channel.id}.json"
        await _write_cache(channel, filename, send_embed_to=__orig_msg.channel)
    
    with open(f"cache/{channel.id}.json", "r", encoding='UTF-8') as f:
        loaded_data = list(json.load(f))
        loaded_data.pop() # remove the temporary timestamp at the end
        
        # progress bar stuff
        progress = 0
        total_messages = len(loaded_data)-1
        
        # if no role specified keep it at "temp-no-role" while sorting out invalid roles  
        if type(role) == list: # multiple roles were specified
            _role = []
            for _r in role:
                newrole = discord.utils.get(channel.guild.roles, name=_r)
                if newrole is None:
                    await send_error_embed(__orig_msg.channel, details=f"Role '{_r}' does not exist in server '{channel.guild.name}'. Make sure the parameter is the name of a role (not its @mention) in double quotes.")
                    return
                _role.append(newrole)

        else: # only one role was specified
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
        
        __num_skipped = num_members_tracked = 0 # (once over 50, stop tracking members since graph runs out of space)
        
        member_overflow_warning_flag = False
        for message in loaded_data: # message should be dict loaded from the cache json
            progress += 1
            await pbar.update(progress / total_messages)
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
                
                member_roles = set([r.name for r in sender_as_member.roles])
                
                if (type(role) == str and (role not in member_roles)) or \
                (type(role) == list and not all([r in member_roles for r in role])):
                    continue
                
                new_start = _check_advance_window(time, timestamp, curr_timewindow_start, data, curr_data)
    
                if new_start:
                    curr_timewindow_start = new_start
                    curr_data = {}
                
                ct = _search_queries(message["content"], query)
                try:
                    curr_data[sender] = curr_data.get(sender) + ct
                except TypeError: # if curr_data[sender] is None
                    if num_members_tracked < 50:
                        curr_data[sender] = ct
                    elif not member_overflow_warning_flag:
                        # send warning embed
                        await send_warning_embed(
                            send_to_channel=__orig_msg.channel,
                            details=f"Stopped tracking new users after 50 unique detections. Use `--roles` (see `::help`) to filter to specific role groups.",
                        )
                        member_overflow_warning_flag = True
            except Exception as e:
                print("-"*40 + "> Error <" + "-"*40)
                print(f"Error while parsing message in collect: {e}")
                traceback.print_exc()
                print("-"*40 + "> Error <" + "-"*40)
                __num_skipped += 1
                continue
        _embed, _msg = await pbar.update(1)
    # save last time window
    data[str(curr_timewindow_start)] = curr_data
    
    return data, _embed, _msg
