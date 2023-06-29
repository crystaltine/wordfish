import discord

async def send_error_embed(send_to_channel: discord.TextChannel, exception: Exception = None, details: str = None):
    """
    `details` is visually on top of `exception` in the embed
    """
    embed = discord.Embed(
        title=":x: Error", 
        description=f"{details if details else ''}{('```' + str(exception) + '```') if exception else ''}\n",
        color=0xff0000
    )
    
    await send_to_channel.send(embed=embed)

async def send_warning_embed(send_to_channel: discord.TextChannel, details: str = ''):    
    embed = discord.Embed(
        title=":warning: Warning", 
        description=details,
        color=0xffff00
    )
    
    await send_to_channel.send(embed=embed)
