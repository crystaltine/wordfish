import discord
from error import send_error_embed
from functions.write_cache import _write_cache

from _CONSTANTS import COLOR_CODE_MAGENTA, COLOR_CODE_YELLOW, COLOR_CODE_RESET
_cm = COLOR_CODE_MAGENTA
_cy = COLOR_CODE_YELLOW
_reset = COLOR_CODE_RESET

async def __read_cache_msg(message: discord.Message, client: discord.Client) -> None:
    if message.content.replace('\n', "").startswith("::cache"):
        print(f"In {_cm}{message.channel.guild}{_reset} > {_cy}{message.channel.name}{_reset}: {message.content} ({_cm}{message.channel.guild.id}{_reset} > {_cy}{message.channel.id}{_reset})")
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
                await send_error_embed(
                    message.channel,
                    details=f"Channel with id `{message.content.split(' ')[1]}` was not found. Double check the channel ID and make sure Wordfish is present in the specified channel's server."
                )
                return
            
            # user specified a valid channel
            filename = f"cache/{_channel.id}.json"
            await _write_cache(_channel, filename, send_embed_to=message.channel)
            return
        
        # no specified channel, use current channel
        filename = f"cache/{message.channel.id}.json"
        await _write_cache(message.channel, filename)