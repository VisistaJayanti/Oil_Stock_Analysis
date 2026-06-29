import json
import csv

#loading the json file
with open ("brent_clean.json","r") as f:
    data = json.load(f)

#writing data to csv
with open ("brent_clean.csv","w", newline="") as f:
    writer = csv.DictWriter(f,fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)

print("CSV file created")