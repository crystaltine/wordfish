import json
import datetime

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

def extract_data(data: dict) -> tuple[list[str], list[list[int]], list[str]]:
    """
    Returns timestamps, datalist, users in a tuple
    
    Extract data from a dict of the format:
    {
        "2020-01-01": {
            "user1": 10,
            "user2": 20,
            "user3": 30,
        },
        "2020-01-02": {
            "user1": 11,
            "user2": 21,
            "user3": 31,
        },
        "2020-01-03": {
            "user1": 12,
            "user2": 22,
            "user3": 32,
        },
    }
    
    into a tuple of the format:
    (
        ["user1", "user2", "user3"],
        [
            [10, 11, 12],
            [20, 21, 22],
            [30, 31, 32],
        ],
        ["2020-01-01", "2020-01-02", "2020-01-03"],
    )
    """
    users: list[str] = []
    data_list: list[list[int]] = []
    timestamps: list[str] = list(data.keys())
    
    cleaned_data = convert_raw_json(raw_json_data=data)
    users = list(cleaned_data.keys())
    data_list = list(cleaned_data.values())
    
    def _remove_time_from_timestamp(timestamp: str) -> str:
        """
        Returns a timestamp with the time removed
        """
        return timestamp.split(' ')[0]
    
    return (list(map(_remove_time_from_timestamp, timestamps)), data_list, users)