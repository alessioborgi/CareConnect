import os
import sys
import logging
import pandas as pd
from IPython.display import Markdown, display
import re
from openai import OpenAI
from llama_index.core import StorageContext
from llama_index.core import Settings
from llama_index.core import SimpleDirectoryReader
from llama_index.experimental.query_engine import PandasQueryEngine
from llama_index.embeddings.openai import OpenAIEmbedding



def load_openai_key():
    # first, load and set openaikey from a txt file I stored it in
    with open('oaikey.txt') as keyfile:
        oaikey = keyfile.read().strip()
    
    os.environ["OPENAI_API_KEY"] = oaikey
    return oaikey

def load_data():
    # File paths for each room
    room_files = {
        'QDORO': './MQTT Client/Room MQTT Client/data/airQDORO.csv',
        'QFOYER': './MQTT Client/Room MQTT Client/data/airQFOYER.csv',
        'QHANS': './MQTT Client/Room MQTT Client/data/airQHANS.csv',
        'QMOMO': './MQTT Client/Room MQTT Client/data/airQMOMO.csv',
        'QRITA': './MQTT Client/Room MQTT Client/data/airQRITA.csv',
        'QROB': './MQTT Client/Room MQTT Client/data/airQROB.csv'
    }

    # Load each room's data into separate DataFrames
    df_QDORO = pd.read_csv(room_files['QDORO'])
    df_QFOYER = pd.read_csv(room_files['QFOYER'])
    df_QHANS = pd.read_csv(room_files['QHANS'])
    df_QMOMO = pd.read_csv(room_files['QMOMO'])
    df_QRITA = pd.read_csv(room_files['QRITA'])
    df_QROB = pd.read_csv(room_files['QROB'])

    df_rooftop = pd.read_csv('./MQTT Client/Roof MQTT Client/data/pivoted_data.csv')
    
    # Optionally, convert timestamp to datetime if needed
    df_QDORO['timestamp'] = pd.to_datetime(df_QDORO['timestamp'])
    df_QFOYER['timestamp'] = pd.to_datetime(df_QFOYER['timestamp'])
    df_QHANS['timestamp'] = pd.to_datetime(df_QHANS['timestamp'])
    df_QMOMO['timestamp'] = pd.to_datetime(df_QMOMO['timestamp'])
    df_QRITA['timestamp'] = pd.to_datetime(df_QRITA['timestamp'])
    df_QROB['timestamp'] = pd.to_datetime(df_QROB['timestamp'])

    df_rooftop['timestamp'] = pd.to_datetime(df_rooftop['timestamp_utc'])
    
    return df_QDORO, df_QFOYER, df_QHANS, df_QMOMO, df_QRITA, df_QROB, df_rooftop

def setup_query_engine(room_choice):
    
    ### Loading Data ###
    df_QDORO, df_QFOYER, df_QHANS, df_QMOMO, df_QRITA, df_QROB, df_rooftop = load_data()
    
    ### Query Engine Choice
    # Set query_engine_choice based on the internal/external choice and the room choice
    if room_choice == "QDORO":
        query_engine_DORO = PandasQueryEngine(df=df_QDORO, verbose=True)
        query_engine_choice = query_engine_DORO
    elif room_choice == "QFOYER":
        query_engine_FOYER = PandasQueryEngine(df=df_QFOYER, verbose=True)
        query_engine_choice = query_engine_FOYER
    elif room_choice == "QHANS":
        query_engine_HANS = PandasQueryEngine(df=df_QHANS, verbose=True)
        query_engine_choice = query_engine_HANS
    elif room_choice == "QMOMO":
        query_engine_MOMO = PandasQueryEngine(df=df_QMOMO, verbose=True)
        query_engine_choice = query_engine_MOMO
    elif room_choice == "QRITA":
        query_engine_RITA = PandasQueryEngine(df=df_QRITA, verbose=True)
        query_engine_choice = query_engine_RITA
    elif room_choice == "QROB":
        query_engine_ROB = PandasQueryEngine(df=df_QROB, verbose=True)
        query_engine_choice = query_engine_ROB
    elif room_choice == "ROOFTOP":
        query_engine_rooftop = PandasQueryEngine(df=df_rooftop, verbose=True)
        query_engine_choice = query_engine_rooftop
    else:
        raise ValueError(f"Unknown Room choice: {room_choice}")
    
    return query_engine_choice

def build_dataframe(actual_response):
    # Split the string into lines
    lines = actual_response.split('\n')

    # Extract the column names from the first line
    column_names = lines[0].strip().split()

    # Filter out lines that contain '..' or are empty
    filtered_lines = [line for line in lines[1:] if line.strip() and '..' not in line]

    # Use regex to extract health and timestamp values
    parsed_data = []
    for line in filtered_lines:
        match = re.match(r'\s*(\d+)\s+(\d+)\s+([\d-]+ [\d:.]+)', line)
        if match:
            health = int(match.group(2))  # The first column (health)
            timestamp = match.group(3)  # The second column (timestamp)
            parsed_data.append((health, timestamp))

    # Convert to DataFrame using the column names from the first line
    df_response = pd.DataFrame(parsed_data, columns=column_names)

    # Remove the last row
    df_response = df_response.iloc[:-1]

    df_response['timestamp'] = pd.to_datetime(df_response['timestamp'], errors='coerce')

    # # Display the resulting DataFrame
    print(df_response)
    
    return df_response




def main():
    
    ##### 1) LOADING OpenAI KEY #####
    oaikey = load_openai_key()
    
    ##### 2) LOADING DATA, BUILDING PANDAS QUERY ENGINES and SET UP CHOICES #####
    room_choice = "QRITA"
    query_engine_choice = setup_query_engine(room_choice)

    ##### 3) QUERYING DATA #####
    ''' Either you run 3.1 or 3.2. You can't run both.'''
    
    # 3.1) Single Query (one value returned)
    # query = f"Please provide me the set of air temperature values during last day in {room_choice}"
    # response = query_engine_choice.query(query)   
    # actual_response = response.response
    # print(actual_response)
    
    # 3.2) Multiple Query (multiple value returned)
    timestep_request = 'and the timestamp'
    # query = f"Please provide me all the Air Temperature {timestep_request} values during first day in the room {room_choice}."
    query = f"Please provide me all the health {timestep_request} values during first day in the room {room_choice}."
    
    response = query_engine_choice.query(
        query,
    )
       
    actual_response = response.response
    print(actual_response)
    
    # Additional step needed for the multi-data answers. 
    df_response = build_dataframe(actual_response)
    
    client = OpenAI(api_key=oaikey)
    chat_completion = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'user', 
                'content': f'Here it is the user query: {query}.'
                'Generate python code that prints a line chart of the full data. The chart should include timestamp on the x axis and the other value on the y-axis'
                #'For the plotting, about the timestamp, take into consideration for the labels only the day, hours, minutes and seconds information.'
                f'For the data use the following dataframe: {df_response}.'
                'The dataframe df_response only contains results about the room the user is interested in.'
                'Only print the python code. Do not include comments.'
                'Do not output any other text before or after the code.'}])
    code = chat_completion.choices[0].message.content[9:-3]
    exec(code)
    
if __name__ == "__main__":
    main()