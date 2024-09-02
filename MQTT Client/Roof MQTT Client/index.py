import requests
import pandas as pd
from io import StringIO
import os

# Define the URL and parameters
url = 'https://zentracloud.eu/api/v3/get_readings/'
params = {
    'device_sn': 'A4100209',
    'start_date': '2024-07-01 00:00',
    'end_date': '2024-07-03 00:00',
    'start_mrid': '3500',
    'end_mrid': '3800',
    'output_format': 'csv',  # or 'json'
    'page_num': '1',
    'per_page': '1000',
    'device_depth': 'true',
    'sort_by': 'descending'
}

# Define the headers
headers = {
    'accept': 'application/json',
    'Authorization': 'Token 3e6095af039d9277f6e15871e8497980384a6b46'
}

# Make the GET request
response = requests.get(url, headers=headers, params=params)

# Check the response
if response.status_code != 200:
    print("Request not successful")
    print(response.text)
else:
    # Create the directory if it doesn't exist
    os.makedirs('MQTT Client/Roof MQTT Client/data/', exist_ok=True)
    data = StringIO(response.text)
    # store response in a csv file without pandas
    with open('MQTT Client/Roof MQTT Client/data/data.csv', 'w') as f:
        # remove the first 7 lines in response.text
        clean_response = response.text.split('\n', 8)[8]
        # now seperate data in diffrent csv
        # f.write(clean_response)
        df = pd.read_csv(StringIO(clean_response))
        # write data to csv file
        df.to_csv('MQTT Client/Roof MQTT Client/data/data.csv')
        # filter data in files based on column measurement
        important_measurements = ['Air Temperature', 'Atmospheric Pressure', 'Wind Speed',
                                  'Wind Direction', 'Precipitation', 'Solar Radiation', 'VPD', 'Vapor Pressure']
        for measurement in important_measurements:
            df[df['measurement'] == measurement].to_csv(
                f'MQTT Client/Roof MQTT Client/data/{measurement}.csv', index=False)

print("Data fetched and stored in data.csv")