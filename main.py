import discord
from xlsxwriter.exceptions import EmptyChartSeries
import traceback

from _CONSTANTS import COLOR_CODE_MAGENTA, COLOR_CODE_YELLOW, COLOR_CODE_RED, COLOR_CODE_RESET, TOKEN
_y = COLOR_CODE_YELLOW
_r = COLOR_CODE_RED
_m = COLOR_CODE_MAGENTA
_x = COLOR_CODE_RESET


from functions.commands.handle_command import handle_msg
from functions.parse_command import smart_parse_collect_command
from error import send_error_embed
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
        try:
            await handle_msg(message, client)
        except Exception as e:        
            print(f"-" * 40 + "> Error <" + "-" * 40)
            traceback.print_exc()
            print(f"The above occured in server {_m}{message.guild.name}{_x} in channel {_y}{message.channel.name}{_x}")
            print(f"Command sent: {_r}{message.content}{_x}")
            print(f"-" * 40 + "> Error <" + "-" * 40)
            await send_error_embed(message.channel, e, "The following error occured:\n")    

    client.run(TOKEN)