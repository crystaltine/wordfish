import json, sys
from datetime import datetime
from datetime import timezone, timedelta

"""
This file isn't used anymore since I don't need to manually create the excel files anymore.
I spent too long making this tho so im keeping it :)
"""

def convert_raw_json(filename: str = None, raw_json_data: dict = None) -> dict[str, list]:
    """
        Takes a raw timestamped JSON file with date keys and frequency (based on users) values (stored in a dict)
        and converts it into a dictionary with keys usernames and values lists. Each list is a series of frequencies
        for each time interval
    """
    if filename is not None:
        with open(filename, 'r') as f:
            data = json.load(f)
            f.close()
            
            cleaned_data = {} # when coming across a new user, add a series to this dict
            curr_index = 0
            for timewindow in data:
                messages_count_dict: dict = data[timewindow]
                for user in messages_count_dict.keys():
                    if user not in cleaned_data.keys():
                        cleaned_data[user] = [0] * len(data.keys())
                    cleaned_data[user][curr_index] = messages_count_dict[user]
                curr_index += 1
                
            return cleaned_data
    elif raw_json_data is not None:
        cleaned_data = {} # when coming across a new user, add a series to this dict
        curr_index = 0
        for timewindow in raw_json_data:
            messages_count_dict: dict = raw_json_data[timewindow]
            for user in messages_count_dict.keys():
                if user not in cleaned_data.keys():
                    cleaned_data[user] = [0] * len(raw_json_data.keys())
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
        
def convert(raw_json_filename: str = None, raw_json_data: dict = None, newfilename: str = None):
    if raw_json_filename is not None:
        with open(raw_json_filename, 'r') as f:
            original_timestamps = list(json.load(f).keys())
            for i in range(len(original_timestamps)):
                original_timestamps[i] = original_timestamps[i].split(' ')[0]
            f.close()

        newfilename = raw_json_filename[:-5] + '.csv'
        
        write_cleaned_data_to_csv(
            convert_raw_json(
                raw_json_filename,
            ),
            newfilename,
            original_timestamps
        )
    elif raw_json_data is not None:
        
        original_timestamps = list(raw_json_data.keys())
        for i in range(len(original_timestamps)):
                original_timestamps[i] = original_timestamps[i].split(' ')[0]
        
        write_cleaned_data_to_csv(
            convert_raw_json(
                raw_json_data=raw_json_data,
            ),
            newfilename,
            original_timestamps
        )