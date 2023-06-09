import re, shlex, discord

def parse_collect_command(msg: discord.Message) -> dict:
    """
    Assume `msgcontent` begins with `::collect`.
    
    Sample discord message command:
    
    `::collect 234791234687892394891610304 hmmmmmmmmm -w`
           ^channel id                 ^query

    ex 2:
    `::collect 234791234687892394891610304 hmmmmmmmmm -d --role role`
    
    Returns dict of the form:
    ```
    {
        "channel_id": <channel_id>,
        "query": <search_for_this>,
        "time_window": <time (d, w, m)> # optional, default 'w',
        "role": <rolename without @> # optional, default None (sort by users)
    }
    ```
    Returns dict with key `error` if there is an error.
    """
    msgcontent = msg.content.strip()
    
    args = shlex.split(msgcontent)[1:]
    if len(args) == 1: 
        return {"error": "Invalid cmd: use `::collect <channel_id>|here <query> [-d/-w/-m] [--role \"<target_role>\"]`"}
    
    try:
        channel_id = int(args[0])
    except:
        if args[0] == "here":
            channel_id = msg.channel.id
        else:
            return {"error": "Invalid cmd: use `::collect <channel_id>|here <query> [-d/-w/-m] [--role \"<target_role>\"]`"}
    
    returnval = {
        "channel_id": channel_id,
        "query": args[1],
        "time_window": "m",
        "role": None,   
    }
    
    if len(args) >= 3:
        if re.search(r"-[dwm]", args[2]):
            returnval["time_window"] = args[2][1]
        else:
            return {"error": f"Invalid time window: `{args[2]}`"}
        
    if len(args) == 4:
        return {"error": "Invalid role: `--role` must be followed by a role name, in quotes (without @)"}
    
    if len(args) > 4:
        if args[3] == "--role":
            if len(args) >= 6: # role name was probably not delimited by quotes so it got split
                return {"error": "Invalid role: Put quotes (\") around the role name to prevent splitting"}
            returnval["role"] = args[4]        
        else:
            return {"error": f"Invalid args: `{args[3]} {args[4]}`. Please use `--role <target_role>` (without @)"}
    
    return returnval
    
    
