import json, sys

CONCERENED_USERS = set(["grr", "gqds", "Sescenti", "hiiiiiiii"])

file_to_convert = 'retirement-home.json'
newfile = 'retirement-home-tabular2.csv'

# Convert to csv
with open(file_to_convert, 'r') as f:
    data = json.load(f)
    f.close()

# In this dict:
# Key: name, value is a list of frequencies of the target word. Each index represents a time window (e.g. month)
occurences = {}

# Clean data to only include concerned users
cleaned_data = {username: ([0]*len(data)) for username in CONCERENED_USERS}
curr_index = 0
for timewindow in data:
    messages_count_dict: dict = data[timewindow]
    for user in messages_count_dict.keys():
        if user in CONCERENED_USERS:
            cleaned_data[user][curr_index] = messages_count_dict[user]
    curr_index += 1
            
#print(cleaned_data)

# Write to csv
with open(newfile, 'w') as out:
    for user in cleaned_data.keys():
        out.write(f"{user},{','.join([str(x) for x in cleaned_data[user]])}\n")