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
    
def set_proportional(**kwargs):
    kwargs['returnval']["proportional"] = True

options_map = {
    "-d": set_interval("d"),
    "-w": set_interval("w"),
    "-m": set_interval("m"),
    "--role": set_role,
    "--ignore-cache": set_ignore_cache,
    "--proportional": set_proportional
}

def smart_parse_collect_command(msg: discord.Message) -> dict:
    msgcontent = msg.content.strip()
    
    args = shlex.split(msgcontent)[1:]
    if len(args) <= 1: 
        return {"error": "Invalid cmd: use `::collect <channel_id|here> <query|\"\"> [-d/-w/-m] [--role \"<target_role>\"] [--ignore-cache] [--proportional]`"}

    try:
        channel_id = int(args[0])
    except:
        if args[0] == "here":
            channel_id = msg.channel.id
        else:
            return {"error": "Invalid cmd: use `::collect <channel_id|here> <query|\"\"> [-d/-w/-m] [--role \"<target_role>\"] [--ignore-cache] [--proportional]`"}
    
    returnval = {
        "channel_id": channel_id,
        "query": args[1],
        "time_window": "m",
        "role": None,
        "ignore_cache": False,
        "proportional": False
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
            
            return {"error": f"Invalid option: `{args[arg_ind]}`. Use `::collect <channel_id|here> <query> [-d/-w/-m] [--role \"<target_role>\"] [--ignore-cache] [--proportional]`"}

    return returnval