import discord
import asyncio
import datetime
from datetime import timezone
from time import sleep
from error import send_error_embed

async def _send_msg(channel: discord.TextChannel, message: str = "", replyto: discord.Message = None, embed: discord.Embed = None):
    # return the sent message
    return await channel.send(message, reference=replyto, embed=embed)

def _get_progress_string(progress: float, length: int = 49, blinked = False) -> str:
    big_block = "█"
    empty_block = "░"
    half_block = "▒"
    
    num_blocks = int(round(progress * length))
    num_empty = length - num_blocks
    if not blinked:
        return big_block * num_blocks + empty_block * num_empty
    if num_blocks == length: # so that there is no extra half block if the progress is 100%
        return big_block * num_blocks
    return big_block * num_blocks + half_block + empty_block * (num_empty - 1)    

class ProgressBar():
    """
    `details` should include the following:
    - target_channel (channel Object) the channel being scanned
    - query (emptystr if activity)
    - interval (sentence case like 'Day')
    - role (optional)
    - proportional_chart (T/F)
    - original_channel (the channel [channel Object] where the command was sent)
    """
    def __init__(self, trigger_message: discord.Message, length: int = 40, **details):
        self.message = trigger_message
        self.blinked = False
        self.length = length
        self.embed = discord.Embed(
            title=":stopwatch: Search in progress... 0.0%", 
            description=_get_progress_string(0, self.length, True), 
            color=0x00ff00
        )
        if details.get('details'):
            self.details = details['details']
        else:
            self.details = details
        
        # Should be included in details:
        # query (emptystr if activity), interval (sentence case like 'Day'), role (optional), proportional_chart (T/F)
        self.prefix_description = f"**Activity scan**\n" if self.details.get("query") is None else f"**Query: ** `{self.details.get('query')}` \n"
        self.prefix_description += f"**Channel: ** {self.details.get('target_channel').mention}\n"
        self.prefix_description += f"**Interval: ** `{self.details.get('interval')}` \n"
        
        __role_param: list[discord.Role] | discord.Role = self.details.get('role')
        
        if type(__role_param) == discord.Role:
            role_mention = f"<@&{__role_param.id}>"
            # check if the role is from another server
            if __role_param.guild.id != self.message.guild.id:
                role_mention = f"`{__role_param.guild.name}> @{__role_param.name}`"
            self.prefix_description += f"**Filtered to: **{role_mention}\n"
        elif type(__role_param) == list:
            role_mentions = [f"<@&{role.id}>" for role in __role_param]
            
            if __role_param[0].guild.id != self.message.guild.id: # from different server, make blue
            
                for i in range(len(__role_param)):
                    role_mentions[i] = f"{__role_param[i].guild.name}> @{__role_param[i].name}"
            
                self.prefix_description += f"**Filtered to: **`{', '.join(role_mentions)}`\n"
            else: self.prefix_description += f"**Filtered to: **{', '.join(role_mentions)}\n"
        else:
            self.prefix_description += f"**Filtered to: **@everyone\n"
        
        self.prefix_description += f"**Chart type: **`{'Proportional' if self.details.get('proportional_chart') else 'Absolute frequency'}` \n" 
        self.prefix_description += f"**Include bots: **`{'Yes' if self.details.get('include_bots') else 'No'}`\n"
        self.prefix_description += "\n Progress: \n"
        self._last_update_time = ...
        
    async def initialize_message(self):

        original_channel = self.details.get("original_channel")
        
        self.embed.description = self.prefix_description + _get_progress_string(0, self.length)
        self.embed.set_image(url="attachment://image2.png")
        self.sent = await _send_msg(original_channel, embed=self.embed)
        self._last_update_time = datetime.datetime.now(timezone.utc)

    async def update(self, new_progress: float):
        
        if not self.sent:
            return False
        
        if new_progress >= 1:
            if datetime.datetime.now(timezone.utc) - self._last_update_time < datetime.timedelta(seconds=1):
                # wait and then do the final update
                sleep_time = 1 - (datetime.datetime.now(timezone.utc) - self._last_update_time).total_seconds()
                sleep(sleep_time + 0.1)

            self.embed.title = f":white_check_mark: Done!"
            self.embed.description = self.prefix_description
            
            # delete text 'Progress: '
            self.embed.description = self.embed.description[:-12]
            
            # add 'Loading graph...'
            self.embed.description += "## Loading image..."
            
            await self.sent.edit(embed=self.embed)
            self._last_update_time = datetime.datetime.now(timezone.utc)
            # return the embed and message obj
            return self.embed, self.sent
        
        if datetime.datetime.now(timezone.utc) - self._last_update_time < datetime.timedelta(seconds=1):
            # don't update too often
            return False
        
        self.embed.title = f":stopwatch: Search in progress... {round(new_progress * 100, 1)}%"
        self.embed.description = self.prefix_description + _get_progress_string(new_progress, self.length, self.blinked)
        self.blinked = not self.blinked
        await self.sent.edit(embed=self.embed)
        self._last_update_time = datetime.datetime.now(timezone.utc)
        
        return True
