import discord
import traceback

from error import send_error_embed
from _CONSTANTS import COLOR_CODE_MAGENTA, COLOR_CODE_YELLOW, COLOR_CODE_RED, COLOR_CODE_RESET
_y = COLOR_CODE_YELLOW
_r = COLOR_CODE_RED
_m = COLOR_CODE_MAGENTA
_x = COLOR_CODE_RESET

async def __read_mywords_msg(message: discord.Message, client: discord.Client):
    """
    Commands formatted as such:
    ```
    ::mywords [number]
    ```
    TODO - allow channel selecting
    Creates a chart of the most commonly used words by the sender. [number] controls how many words are reported, up to 100.
    If number is not specified, defaults to 20.
    FUTURE: add autocorrect-ish option
    """
    if message.content.replace('\n', "").startswith("::mywords"):
        print(f"In {_m}{message.channel.guild}{_x} > {_y}{message.channel.name}{_x}: {message.content} ({_m}{message.channel.guild.id}{_x} > {_y}{message.channel.id}{_x})")      
        __exception = None
        
        # Get potential argument
        split_command = message.content.split(" ")
        num_words = 20
        if len(split_command) > 1:
            try:
                num_words = int(split_command[1])
                if num_words < 1 or num_words > 100:
                    await send_error_embed(
                        message.channel,
                        details=f"The amount of words to search for must be an integer between 2 and 100 inclusive."
                    )
                    return
            except:
                await send_error_embed(
                    message.channel,
                    details=f"Invalid argument `{split_command[1]}`. Argument must be an integer."
                )
                return
        
        # Get all messages from the channel
        # TODO
        