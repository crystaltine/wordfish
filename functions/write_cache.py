import discord
import os
import json
import datetime
from datetime import timezone
from time import sleep
from dateutil import parser
from error import send_error_embed
from functions.utils import send_msg

async def _write_cache(channel: discord.TextChannel, filename: str, send_embed_to: discord.TextChannel = None):
    
    # if wordfish isnt in the server, send error message
    if not channel.guild.me:
        await send_error_embed(
            send_to_channel=send_embed_to,
            details=f"Wordfish is not in server `{channel.guild.name}`!",
        )
        return
    
    # Check if Wordfish has permission to read messages in the channel
    if not channel.permissions_for(channel.guild.me).read_message_history:
        # Send error message
        if channel.guild.id != send_embed_to.guild.id:
            await send_error_embed(
                send_to_channel=send_embed_to,
                details=f"Wordfish does not have permission to read `{channel.guild.name}> #{channel.name}`!",
            )
            return
        await send_error_embed(
            send_to_channel=send_embed_to,
            details=f"Wordfish does not have permission to read {channel.mention}!",
        )
        return
    
    if not send_embed_to:
        send_embed_to = channel
        
    # if cache file already exists, only get messasges after the last timestamp
    messages = []
    after = None
    orig_len = None

    if os.path.exists(filename):
        with open(filename, "r", encoding='UTF-8') as f:
            messages = list(json.load(f))
            after = parser.isoparse(messages.pop())
            orig_len = len(messages)
    
    init_desc = \
        f"Scanned messages: 0\nRate: N/A" if not after else \
        f"Adding to cache dated {after} with {len(messages)} messages...\n\nScanned messages: 0\nRate: N/A"
    info_embed = discord.Embed(title=f":notepad_spiral: Caching {channel.mention}", description=init_desc, color=0x00aaff)
    last_info_update = datetime.datetime.now(timezone.utc)
    sent = await send_msg(send_embed_to, embed=info_embed)
    
    init_timestamp = datetime.datetime.now(timezone.utc)
    async for msg in channel.history(limit=None, oldest_first=True,after=after):
        messages.append({
            "content": msg.content, 
            "timestamp": msg.created_at.isoformat(), 
            "author": msg.author.name,
            "author_id": msg.author.id,
        })
        
        _timestamp = datetime.datetime.now(timezone.utc)
        if _timestamp - last_info_update > datetime.timedelta(seconds=1):
            rate = len(messages) / (_timestamp - init_timestamp).total_seconds() # messages per second
            hours_taken = int((_timestamp - init_timestamp).total_seconds() // 3600)
            minutes_taken = int(((_timestamp - init_timestamp).total_seconds() % 3600) // 60)
            seconds_taken = round(((_timestamp - init_timestamp).total_seconds() % 3600) % 60, 2)
            
            elapsed_time_str = f"{hours_taken}h {minutes_taken}m {seconds_taken}s"
            info_embed.description = f"Adding to cache dated {after} with {len(messages)} messages...\n\n" \
                if after else ""
            info_embed.description += f"**Scanned messages:** {'{:,}'.format(len(messages))}\n**Rate:** {rate:.2f} messages/sec\n**Elapsed Time:** {elapsed_time_str}"
            await sent.edit(embed=info_embed)
            last_info_update = _timestamp
    final_timestamp = datetime.datetime.now(timezone.utc)
    # write timestamp at end
    sleep(max(0, (final_timestamp - last_info_update).total_seconds())) # to prevent editing failing
    info_embed.description = f"Writing cached messages to `{filename}`..."
    await sent.edit(embed=info_embed)
    messages.append(init_timestamp.isoformat())
    with open(filename, "w") as f:
        f.write(json.dumps(messages))
        f.close()
    
    # edit embed to show completion
    info_embed.title = f":white_check_mark: Successfully cached {channel.mention}!"
    
    _init_iso_split = init_timestamp.isoformat().split("T")
    
    readable_timestamp = _init_iso_split[0] + " " + _init_iso_split[1].split(".")[0]
    
    hours_taken = int((final_timestamp - init_timestamp).total_seconds() // 3600)
    minutes_taken = int(((final_timestamp - init_timestamp).total_seconds() % 3600) // 60)
    seconds_taken = round(((final_timestamp - init_timestamp).total_seconds() % 3600) % 60, 2)
    
    elapsed_time_str = f"{hours_taken}h {minutes_taken}m {seconds_taken}s"
    
    avg_rate = round(len(messages) / (final_timestamp - init_timestamp).total_seconds(), 2)
    info_embed.description = f"**{'{:,}'.format(len(messages))} messages** in `{channel.name}` saved as of **{readable_timestamp} (UTC)**\n\n**Total Time:** {elapsed_time_str}\n**Average Rate**: {avg_rate} messages/sec"
    if after:
        avg_rate = round((len(messages) - orig_len) / (final_timestamp - init_timestamp).total_seconds(), 2)
        info_embed.description = f"**{'{:,}'.format(len(messages) - orig_len)} new messages** in {channel.mention} added as of **{readable_timestamp} (UTC)**\n\n**Total Time:** {elapsed_time_str}\n**Average Rate**: {avg_rate} messages/sec"
    info_embed.color = 0x00ff00
    await sent.edit(embed=info_embed)