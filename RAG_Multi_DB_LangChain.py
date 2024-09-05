import os
import datetime
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, Float, text
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI  # Use ChatOpenAI for chat models
from langchain_community.agent_toolkits import create_sql_agent
from sqlalchemy import DateTime

def load_openai_key():
    with open('oaikey.txt') as keyfile:
        oaikey = keyfile.read().strip()
    os.environ["OPENAI_API_KEY"] = oaikey
    return oaikey

# Step 2: Create an SQLite database and load CSV data
def create_and_load_database():
    # Set up SQLite in memory
    engine = create_engine('sqlite:///CareConnect.db')  # This will create a file-based SQLite DB
    metadata_obj = MetaData()

    # Define table schema for rooms with DateTime for timestamp
    room_tables = {
        'room_QRITA': './MQTT Client/Room MQTT Client/data/airQRITA.csv',
        'room_QFOYER': './MQTT Client/Room MQTT Client/data/airQFOYER.csv',
        'room_QDORO': './MQTT Client/Room MQTT Client/data/airQDORO.csv',
        'room_QHANS': './MQTT Client/Room MQTT Client/data/airQHANS.csv',
        'room_QMOMO': './MQTT Client/Room MQTT Client/data/airQMOMO.csv',
        'room_QROB': './MQTT Client/Room MQTT Client/data/airQROB.csv'
    }

    # Load room data into SQLite
    for room, file_path in room_tables.items():
        room_table = Table(
            room, metadata_obj,
            Column('timestamp', DateTime, primary_key=True),  # Use DateTime instead of String
            autoload_with=engine
        )
        metadata_obj.create_all(engine)
        
        # Load data from CSV and convert timestamp to DateTime
        df_room = pd.read_csv(file_path)
        df_room['timestamp'] = pd.to_datetime(df_room['timestamp'], unit='ms')  # Convert to datetime

        # Save to the SQLite database
        df_room.to_sql(room, con=engine, if_exists='replace', index=False)

    # Load rooftop data into SQLite
    rooftop_file = './MQTT Client/Roof MQTT Client/data/pivoted_data.csv'
    df_rooftop = pd.read_csv(rooftop_file)
    df_rooftop['timestamp'] = pd.to_datetime(df_rooftop['timestamp'], unit='s')  # Convert to datetime
    df_rooftop.to_sql('rooftop', con=engine, if_exists='replace', index=False)

    return engine

def setup_langchain_sql_database(engine):
    # Use ChatOpenAI for chat-based models
    llm = ChatOpenAI(temperature=0.1, model="gpt-4o-mini")

    # Define the SQLDatabase to include all room tables and rooftop
    sql_database = SQLDatabase(engine, include_tables=[
        "room_QRITA", "room_QFOYER", "room_QDORO", "room_QHANS", "room_QMOMO", "room_QROB", "rooftop"
    ])

    return llm, sql_database


def query_room(room_choice, input_query, agent_executor, timestep_request=''):
    """
    Queries a specific room using the provided input query and an optional timestep request.
    
    Args:
        room_choice (str): The room to query (e.g., "QRITA").
        input_query (str): The base query input string.
        agent_executor (obj): The LangChain agent executor object.
        timestep_request (str, optional): Additional query modifier (e.g., 'Please include the corresponding timestamps'). Defaults to an empty string.
    
    Returns:
        str: The query result or an error message if the data is not present.
    """
    
    # Append timestep request if provided
    
    input_query += f" Room: {room_choice}."
    
    if timestep_request:
        input_query += f" {timestep_request}"
    
    # Execute the query using the agent executor
    query_result = agent_executor.invoke({"input": input_query})
    
    # Handle cases where the result is empty
    return query_result

# Main function to tie everything together
def main():
    ##### 1: Set up OpenAI API key. #####
    oaikey = load_openai_key()

    ##### 2: Create an SQLite database and load CSV data. #####
    engine = create_and_load_database()

    ##### 3: Define the SQLDatabase in LangChain. #####
    llm, sql_database = setup_langchain_sql_database(engine)

    ##### 4: Creating the Agent Executor llm (ChatOpenAI) for chat-based models. #####
    agent_executor = create_sql_agent(llm, db=sql_database, verbose=True)

    ##### 5: Querying the Agent Executor llm (ChatOpenAI). #####
    timestep_request = 'Please include together also the corresponding timestamps and format the response as a list of tuples'
    
    # 5.1: QRITA Health Values.
    # room_choice = "QRITA"
    # input_query = f"Please provide me the entire set of health values."    
    # query_result = query_room(room_choice, input_query, agent_executor, timestep_request)
    
    # 5.2: QRITA Air Temperature Values.
    # room_choice = "QRITA"
    # input_query = "Please provide me the entire set of air temperature values in the room."
    # query_result = query_room(room_choice, input_query, agent_executor, timestep_request)
    
    # 5.3: ROOF Solar Radiation data.
    room_choice = "ROOF"
    input_query = "What was the solar radiation recently?"
    query_result = query_room(room_choice, input_query, agent_executor, timestep_request)
    
    # 5.4: ROOF Solar Radiation data.
    # room_choice = "ROOF"
    # input_query = "What was the average solar radiation during last year?"
    # query_result = query_room(room_choice, input_query, agent_executor)
    
    
    # 5.error: QFOYER air temperature. (Not present, gives you error!)
    # room_choice = "QFOYER"
    # input_query = f"What is the air temperature in {room_choice} room during the last 24 hours?"
    # input_query += timestep_request
    # query_result = agent_executor.invoke({"input": input_query})
    
    # Print the result if needed
    print("\nQuery Result:")
    print(query_result)
    
    
    print(query_result['output'])

    return query_result  # Return the result if needed for further processing

if __name__ == "__main__":
    query_result = main()  