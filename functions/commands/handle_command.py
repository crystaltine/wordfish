import discord

from functions.commands.command_cache import __read_cache_msg
from functions.commands.command_collect import __read_collect_msg
from functions.commands.command_help import __read_help_msg

async def handle_msg(message: discord.Message, __client: discord.Client) -> None:
    await __read_cache_msg(message, __client)
    await __read_collect_msg(message, __client)
    await __read_help_msg(message, __client)