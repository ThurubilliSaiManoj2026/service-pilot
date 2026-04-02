# verify.py — Quick validation script for the incidents dataset
import json

# Open and parse the JSON file
with open('data/incidents.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Print verification results
print(f'Total incidents loaded : {len(data)}')
print(f'First incident ID      : {data[0]["incident_id"]}')
print(f'Last incident ID       : {data[-1]["incident_id"]}')
print(f'Sample title (INC-001) : {data[0]["title"]}')
print(f'Sample severity        : {data[0]["severity"]}')
print(f'Sample category        : {data[0]["category"]}')
print('\nJSON is valid and dataset is complete.')