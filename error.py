import discord

async def send_error_embed(send_to_channel: discord.TextChannel, exception: Exception = None, details: str = None):    
    embed = discord.Embed(
        title=":x: Error", 
        description=f"{details if details else ''}{('```' + str(exception) + '```') if exception else ''}\n",
        color=0xff0000
    )
    
    await send_to_channel.send(embed=embed)
