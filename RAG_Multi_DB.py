import os
import datetime
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, Float, text
from llama_index.core import SQLDatabase
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.llms.openai import OpenAI
import duckdb

def load_openai_key():
    with open('oaikey.txt') as keyfile:
        oaikey = keyfile.read().strip()
    os.environ["OPENAI_API_KEY"] = oaikey
    return oaikey

# Step 2: Create an SQLite database and load CSV data
def create_and_load_database():
    # Set up DuckDB in memory
    engine = create_engine('duckdb:///:memory:')
    metadata_obj = MetaData()

    # Define table schema for rooms
    room_tables = {
        'room_QRITA': './MQTT Client/Room MQTT Client/data/airQRITA.csv',
        'room_QFOYER': './MQTT Client/Room MQTT Client/data/airQFOYER.csv',
        'room_QDORO': './MQTT Client/Room MQTT Client/data/airQDORO.csv',
        'room_QHANS': './MQTT Client/Room MQTT Client/data/airQHANS.csv',
        'room_QMOMO': './MQTT Client/Room MQTT Client/data/airQMOMO.csv',
        'room_QROB': './MQTT Client/Room MQTT Client/data/airQROB.csv'
    }

    # Define table schema for rooftop
    rooftop_file = './MQTT Client/Roof MQTT Client/data/pivoted_data.csv'
    rooftop_table = Table(
        'rooftop', metadata_obj,
        Column('timestamp', String, primary_key=True),
    )

    # Load room data into SQLite
    for room, file_path in room_tables.items():
        room_table = Table(
            room, metadata_obj,
            Column('timestamp', String, primary_key=True),
            # Column('temperature', Float),
            # Column('humidity', Float),
            # Column('health', Integer),
        )
        metadata_obj.create_all(engine)

        # Load data from CSV and insert into SQLite
        df_room = pd.read_csv(file_path)
        df_room.to_sql(room, con=engine, if_exists='replace', index=False)

    # Load rooftop data into SQLite
    metadata_obj.create_all(engine)
    df_rooftop = pd.read_csv(rooftop_file)
    df_rooftop.to_sql('rooftop', con=engine, if_exists='replace', index=False)

    return engine

# Step 3: Define the SQLDatabase in LlamaIndex
def setup_llamaindex_sql_database(engine):
    # Create an OpenAI LLM instance
    llm = OpenAI(temperature=0.1, model="gpt-4o-mini")

    # Define the SQLDatabase to include all room tables and rooftop
    sql_database = SQLDatabase(engine, include_tables=[
        "room_QRITA", "room_QFOYER", "room_QDORO", "room_QHANS", "room_QMOMO", "room_QROB", "rooftop"
    ])

    return llm, sql_database

# Step 4: Set up the Natural Language SQL Query Engine
def setup_query_engine(llm, sql_database):
    query_engine = NLSQLTableQueryEngine(llm=llm, sql_database=sql_database)
    return query_engine

# Step 6: Query the SQL database with natural language
def run_query(query_engine, query):
    response = query_engine.query(query)
    print("Query Result: ")
    print(response)

# Main function to tie everything together
def main():
    # Load OpenAI API key
    load_openai_key()

    # Create and load data into DuckDB database
    engine = create_and_load_database()

    # Display data from the tables (optional)
    display_table_data(engine)

    ##### 3: Display data from the tables (optional). #####
    # display_table_data(engine)

    ##### 4: Define the SQLDatabase in LlamaIndex. #####
    llm, sql_database = setup_llamaindex_sql_database(engine)

    ###### 5: Set up the Natural Language SQL Query Engine. #####
    query_engine = setup_query_engine(llm, sql_database)

    # Example query - fetch health values from QRITA during the first day
    query = "What are the health values in QRITA room during the first day?"
    run_query(query_engine, query)

    # Example Query 2- fetch temperature data from QFOYER for the last 24 hours
    # room_choice = "QFOYER"
    # query = f"What is the air temperature in {room_choice} room during the last 24 hours?"
    # response = run_query(query_engine, query)

    # Example Query 3 - fetch rooftop data
    # room_choice = "rooftop"
    # query = f"What was the solar radiation on the {room_choice} recently?"
    # query = f"What was the entire set of solar radiation on the {room_choice} recently"
    # query += timestep_request
    # response = run_query(query_engine, query)
    
    # client = OpenAI(api_key=oaikey)
    chat_completion = openai.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'user', 
                'content': f'Here it is the user query: {query}.'
                'Generate python code that prints a line chart of the full data.' 
                'The chart should include timestamp on the x axis and the other value on the y-axis.'
                f'The response coming from the retrieval augmented engine is: {response}'
                #'For the plotting, about the timestamp, take into consideration for the labels only the day, hours, minutes and seconds information.'
                # f'For the data use the following dataframe: {df_response}.'
                # 'The dataframe df_response only contains results about the room the user is interested in.'
                'Only print the python code. Do not include comments.'
                'Do not output any other text before or after the code.'
                }])
        
    code = chat_completion.choices[0].message.content[9:-3]
    
    # Get the current timestamp and format it
    current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

    # Search for plt.show() in the code and insert plt.savefig before it
    if 'plt.show()' in code:
        # Insert the savefig line right before plt.show()
        code = code.replace('plt.show()', f"plt.savefig('./saved_imgs/img_{current_time}.png')\nplt.show()")

    # Execute the modified code
    exec(code)

if __name__ == "__main__":
    main()