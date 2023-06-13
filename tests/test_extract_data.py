from extract_data import extract_data
import json

raw_json_filename = 'activityfiles/activity-general-weekly-0c02aa21.json'

with open(raw_json_filename, 'r') as f:
    extracted = extract_data(json.load(f))

print(extracted[0])
for i in extracted[1]:
    print(*i)
print(extracted[2])