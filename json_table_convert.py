import json, sys
from datetime import datetime, timedelta

def convert_raw_json(filename: str, concerned_users: set = None) -> dict[str, list]:
    """
        Takes a raw timestamped JSON file with date keys and frequency (based on users) values (stored in a dict)
        and converts it into a dictionary with keys usernames and values lists. Each list is a series of frequencies
        for each time interval
    """
    with open(filename, 'r') as f:
        data = json.load(f)
        f.close()
    
    # Clean data to only include concerned users
    cleaned_data = {username: ([0]*len(data)) for username in concerned_users}
    curr_index = 0
    for timewindow in data:
        messages_count_dict: dict = data[timewindow]
        for user in messages_count_dict.keys():
            if user in concerned_users:
                cleaned_data[user][curr_index] = messages_count_dict[user]
        curr_index += 1
        
    return cleaned_data

def write_cleaned_data_to_csv(data: dict, filename: str, original_timestamps: list = None):
    with open(filename, 'w') as out:
        
        # First write timestamps
        if original_timestamps is not None:
            out.write("," + ",".join([str(x) for x in original_timestamps]) + "\n")
        
        for username in data.keys():
            out.write(f'{username},{",".join([str(x) for x in data[username]])}\n')
        out.close()
        
name = "datafiles/retirement-home-weekly-0c17a0a6.json"

with open(name, 'r') as f:
    original_timestamps = list(json.load(f).keys())
    for i in range(len(original_timestamps)):
        original_timestamps[i] = original_timestamps[i].split(' ')[0]
    f.close()
    
write_cleaned_data_to_csv(
    convert_raw_json(
        name,
        set(['grr', 'gqds', 'hiiiiiiii', 'Sescenti'])
    ),
    'datafiles/retirement-home-weekly-0c17a0a6.csv',
    original_timestamps
)