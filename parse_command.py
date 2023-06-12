import re, shlex, discord

def set_interval(time_window: str = "w"):
    def inner(**kwargs):
        kwargs['returnval']["time_window"] = time_window
    return inner

def set_role(**kwargs):
    
    args_list = kwargs['args_list'][2:]
    returnval = kwargs['returnval']
    
    role_option_index = args_list.index("--role")
    
    if len(args_list) <= role_option_index + 1:
        returnval["error"] = "Invalid role: `--role` must be followed by a role name, in quotes (without @)"
    else:
        role_to_add = str(args_list[role_option_index + 1])
        returnval["role"] = role_to_add

def set_ignore_cache(**kwargs):
    kwargs['returnval']["ignore_cache"] = True

options_map = {
    "-d": set_interval("d"),
    "-w": set_interval("w"),
    "-m": set_interval("m"),
    "--role": set_role,
    "--ignore-cache": set_ignore_cache,
}

def smart_parse_collect_command(msg: discord.Message) -> dict:
    msgcontent = msg.content.strip()
    
    args = shlex.split(msgcontent)[1:]
    if len(args) <= 1: 
        return {"error": "Invalid cmd: use `::collect <channel_id|here> <query|empty> [-d/-w/-m] [--role \"<target_role>\"] [--ignore-cache]`"}
    
    try:
        channel_id = int(args[0])
    except:
        if args[0] == "here":
            channel_id = msg.channel.id
        else:
            return {"error": "Invalid cmd: use `::collect <channel_id|here> <query|empty> [-d/-w/-m] [--role \"<target_role>\"] [--ignore-cache]`"}
    
    returnval = {
        "channel_id": channel_id,
        "query": args[1],
        "time_window": "m",
        "role": None,
        "ignore_cache": False
    }
    
    # get args
    for arg_ind in range(2, len(args)):
        if args[arg_ind] in options_map:
            options_map[args[arg_ind]](
                args_list=args,
                returnval=returnval
            )
        else:
            # check if --role is before it
            try:
                if args[arg_ind-1] == "--role":
                    options_map["--role"](args_list=args, returnval=returnval)
                    continue
            except:
                pass
            
            return {"error": f"Invalid option: `{args[arg_ind]}`. Use `::collect <channel_id|here> <query> [-d/-w/-m] [--role \"<target_role>\"] [--ignore-cache]`"}

    return returnval

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
    if len(args) <= 1: 
        return {"error": "Invalid cmd: use `::collect <channel_id>|here <query> [-d/-w/-m] [--role \"<target_role>\"] [--ignore-cache]`"}
    
    try:
        channel_id = int(args[0])
    except:
        if args[0] == "here":
            channel_id = msg.channel.id
        else:
            return {"error": "Invalid cmd: use `::collect <channel_id>|here <query> [-d/-w/-m] [--role \"<rolename>\"]`"}
    
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
            return {"error": f"Invalid args: `{args[3]} {args[4]}`. Please use `--role \"<rolename>\"` (without @)"}
    
    return returnval