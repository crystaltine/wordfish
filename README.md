# Wordfish (beta)

Interesting insights and charts about the usage of certain words/phrases/topics or activity in a discord channel over time.
Flexible options like only including specific roles, proportional charts, changing time intervals. More features hopefully coming soon!

## Examples
*(for obvious reasons, the legend (usernames) are hidden in these examples)*

An example for monthly activity from (mostly) 5 people:
![Example graph](https://i.imgur.com/YeLQDcI.png)

Searching for the word "bad" by week:
![Example query graph](https://i.imgur.com/OqLbR1U.png)

Proportional graph of activity, sorted by day:
![Example proportional graph](https://i.imgur.com/EUGK1xh.png)

## Invite:

https://discord.com/api/oauth2/authorize?client_id=1094453223278002259&permissions=117760&scope=bot

**Permissions:**
+ Read Messages / View Channels (Only public)
+ Send Messages
+ Embed Links (needed for the message format)
+ Attach Files (needed for the images)
+ Read Message History (needed to access channel data)

Once added, if Wordfish is online (I'm currently hosting on a home laptop lmao), run `::help` in your server!

*To scan channels invisible to `@everyone` Wordfish must be manually given those permissions.*

## Upcoming features

*In no particular order - this is mostly a todo list for me*
+ Better command format that doesn't look like a nuclear launch code lol
+ Ensured compatibility with megathreads and not just channels
+ A queue for channel cache (Discord API has a really low rate limit when it comes to scanning channels, and it gets split among everyone using the bot)
+ Ability to concatenate by role group (total activity/word usage from all @Moderators, @Level 10, etc. combined into one group on the chart)
+ Customizable chart themes (colors, fonts, etc.)
+ Hopefully more efficient message scanning (Currently it can scan about 8,000 cached messages per second).
+ Ability to exclude roles from the chart
+ Ability to include/exclude users by username (maybe once all users get unique usernames)
+ Searching by sentiment/topic (this will probably take a long time and also suck because it requires AI)

## Issues

**This bot is still in beta - report any issues with GitHub's issues feature. (or dm me on discord you probably know me since this is a beta release)**
