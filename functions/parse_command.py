import shlex, discord

def set_interval(time_window: str = "w"):
    def inner(**kwargs):
        kwargs['returnval']["time_window"] = time_window
    return inner

def set_role(**kwargs):
    
    args_list = kwargs['args_list'][2:]
    returnval = kwargs['returnval']
    
    role_option_index = args_list.index("--role")
    
    if len(args_list) <= role_option_index + 1:
        returnval["error"] = "Invalid role: `--role` must be followed by a role name, in quotes (without @). Run ::help for more info."
    else:
        role_to_add = str(args_list[role_option_index + 1])
        returnval["role"] = role_to_add

def set_proportional(**kwargs):
    kwargs['returnval']["proportional"] = True
    
def set_include_bots(**kwargs):
    kwargs['returnval']["include_bots"] = True

options_map = {
    "-d": set_interval("d"),
    "-w": set_interval("w"),
    "-m": set_interval("m"),
    "--role": set_role,
    "--proportional": set_proportional,
    "--include-bots": set_include_bots
}

def smart_parse_collect_command(msg: discord.Message) -> dict:
    msgcontent = msg.content.strip()
    
    args = shlex.split(msgcontent)[1:]
    if len(args) <= 1: 
        return {"error": "Invalid command: not enough arguments. Run `::help` for more info."}

    try:
        channel_id = int(args[0])
    except:
        if args[0] == "here":
            channel_id = msg.channel.id
        else:
            return {"error": "Invalid command: first argument must be a channel id or `here`. Run `::help` for more info."}
    
    returnval = {
        "channel_id": channel_id,
        "query": args[1],
        "time_window": "m",
        "role": None,
        "proportional": False,
        "include_bots": False
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
            
            return {"error": f"Invalid option: `{args[arg_ind]}`. Run `::help` for more info."}

    return returnval