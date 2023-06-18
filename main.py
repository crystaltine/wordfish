import discord
from xlsxwriter.exceptions import EmptyChartSeries

import _CONSTANTS
TOKEN = _CONSTANTS.TOKEN

from functions.commands.handle_command import handle_msg
from functions.parse_command import smart_parse_collect_command
client = discord.Client(intents=discord.Intents.all())
    
f"""
See docstring for smart_parse_collect_command in parse_command.py for details on how to use the command
{smart_parse_collect_command.__doc__}
"""
        
def run_discord_bot():
    @client.event
    async def on_ready():
        print(f"{client.user} is now running!")
          
    @client.event
    async def on_message(message: discord.Message):
        # Ignore messages from self
        if message.author == client.user:
            return
        
        await handle_msg(message, client)        

    client.run(TOKEN)