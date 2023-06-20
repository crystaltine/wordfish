import discord, re

def set_interval(time_window: str = "w"):
    def inner(**kwargs):
        kwargs['returnval']["time_window"] = time_window
    return inner

def set_role(**kwargs):
    
    args_list = kwargs['args_list'][2:] # remove the first two elements, which are required ones
    returnval = kwargs['returnval']
    
    role_option_index = args_list.index("--roles")
    
    if len(args_list) <= role_option_index + 1:
        returnval["error"] = "Invalid role: `--roles` must be followed by a role name, in quotes (without @) or a list of quoted role names, in square brackets ([]). Run ::help for more info."
    else:
        role_params: str = args_list[role_option_index + 1]
        
        if role_params.startswith('[') and role_params.endswith(']'): # if list of roles
            _raw_list = role_params.strip('[]').split(',')
            rolenames = []
            for string in _raw_list:
                rolenames.append(string.strip(" \"")) # remove quotes and spaces

            returnval["role"] = rolenames
            return
        role_to_add = str(role_params)
        returnval["role"] = role_to_add

def set_param(option, value):
    def __set(**kwargs):
        kwargs['returnval'][option] = value
    return __set

options_map = {
    "-d": set_interval("d"),
    "-w": set_interval("w"),
    "-m": set_interval("m"),
    "--roles": set_role,
    "--proportional": set_param("proportional", True),
    "--include-bots": set_param("include_bots", True)
}

def smart_parse_collect_command(msg: discord.Message) -> dict:
    msgcontent = msg.content.strip().replace('\n', " ")
    
    pattern = r'(\[.*?\]|\".*?\"|\S+)'
    result: list[str] = re.findall(pattern, msgcontent)
    for _ in range(len(result)):
        result[_] = result[_].strip("\"")
    args = result[1:]

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
            # check if --roles is before it
            try:
                if args[arg_ind-1] == "--roles":
                    options_map["--roles"](args_list=args, returnval=returnval)
                    continue
            except:
                pass
            
            return {"error": f"Invalid option: `{args[arg_ind]}`. Run `::help` for more info."}

    return returnval