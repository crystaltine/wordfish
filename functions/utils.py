import discord
import datetime
from datetime import timezone


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

async def send_msg(
    channel: discord.TextChannel, 
    message: str = "", 
    replyto: discord.Message = None, 
    embed: discord.Embed = None,
    file: discord.File = None
    ):
    # return the sent message
    return await channel.send(message, reference=replyto, embed=embed, file=file)

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