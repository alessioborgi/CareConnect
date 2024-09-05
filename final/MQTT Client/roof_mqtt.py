import requests
import pandas as pd
from io import StringIO
import os

# Define the URL and parameters
url = 'https://zentracloud.eu/api/v3/get_readings/'
params = {
    'device_sn': 'A4100209',
    'start_date': '2023-05-01 00:00',
    'end_date': '2024-09-03 00:00',
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
    
    # Remove the first 7 lines in response.text and parse the CSV
    clean_response = response.text.split('\n', 8)[8]  # Adjust for first 7 lines
    df = pd.read_csv(StringIO(clean_response))

    # Group the data by timestamp, sensor, measurement, and unit, summing the values
    grouped_df = df.groupby(['timestamp_utc', 'sensor_sn', 'measurement', 'units']).agg({
        'value': 'sum'
    }).reset_index()

    # Pivot the data so that each timestamp has measurements as columns and values as rows
    pivot_df = grouped_df.pivot_table(
        index=['timestamp_utc', 'sensor_sn'],
        columns='measurement',
        values='value'
    ).reset_index()

    # Rename columns to include units in the column names
    for measurement in pivot_df.columns[2:]:
        unit = grouped_df.loc[grouped_df['measurement'] == measurement, 'units'].iloc[0]
        pivot_df.rename(columns={measurement: f'{measurement} ({unit})'}, inplace=True)
        
    
    # Rename columns to remove spaces and units from the column names
    pivot_df.columns = pivot_df.columns.str.replace(' ', '_')  # Replace spaces with underscores
    pivot_df.columns = pivot_df.columns.str.replace(r'_[\(\[].*?[\)\]]', '', regex=True)  # Remove units in parentheses



    # Save the pivoted data to a new CSV file
    output_file_path = 'data/roof/pivoted_data.csv'
    pivot_df.to_csv(output_file_path, index=False)

    print(f"Data fetched and stored in {output_file_path}")
