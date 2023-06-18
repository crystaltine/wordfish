import discord
from functions.utils import send_msg
from _CONSTANTS import COLOR_CODE_MAGENTA, COLOR_CODE_YELLOW, COLOR_CODE_RESET, HELP_EMBED
_cm = COLOR_CODE_MAGENTA
_cy = COLOR_CODE_YELLOW
_reset = COLOR_CODE_RESET

async def __read_help_msg(message: discord.Message, client: discord.Client) -> None:
    if message.content.replace('\n', "").startswith("::help"):
        print(f"In {_cm}{message.channel.guild}{_reset} > {_cy}{message.channel.name}{_reset}: {message.content} ({_cm}{message.channel.guild.id}{_reset} > {_cy}{message.channel.id}{_reset})")
        await send_msg(
            message.channel,
            embed=HELP_EMBED,
            replyto=message
        )