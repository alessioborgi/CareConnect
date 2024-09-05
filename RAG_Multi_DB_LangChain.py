import os
import ast
import datetime
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, Float, text
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI  # Use ChatOpenAI for chat models
from langchain_community.agent_toolkits import create_sql_agent
from sqlalchemy import DateTime
from openai import OpenAI
from langchain.schema import HumanMessage, AIMessage  # Use HumanMessage instead of UserMessage


def load_openai_key():
    with open('oaikey.txt') as keyfile:
        oaikey = keyfile.read().strip()
    os.environ["OPENAI_API_KEY"] = oaikey
    return oaikey

# Step 2: Create an SQLite database and load CSV data
def create_and_load_database():
    # Set up SQLite in memory
    engine = create_engine('sqlite:///./DataBase/CareConnect.db')  # This will create the SQLite DB in the desired location
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


def check_response_type(response_str):
    try:
        # Try converting the string to a Python object
        response_obj = ast.literal_eval(response_str)
        
        # Check if it's a list
        if isinstance(response_obj, list):
            return "list"
        else:
            return "string"
    except (ValueError, SyntaxError):
        return "string"

def build_dataframe_from_response(response_str):
    
    try:
        # Convert the string to a Python object (list of tuples)
        data = ast.literal_eval(response_str)
        
        # Extract column names from the first tuple
        columns = data[0]
        
        # Extract the actual data (excluding the first tuple with column names)
        data_values = data[1:]
        
        # Create a pandas DataFrame
        df = pd.DataFrame(data_values, columns=columns)
        
        return df
    except (ValueError, SyntaxError):
        return "Invalid response format."
    
def generate_img_visualization(df_img_visualization, oaikey, input_query):
    
    client = OpenAI(api_key=oaikey)
    chat_completion = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'user', 
                'content': f'Here it is the user query: {input_query}.'
                'Generate python code that prints a line chart of the full data. #The chart should include timestamp on the x axis and the other value on the y-axis'
                f'For the data use the following dataframe: {df_img_visualization}.'
                'Only print the python code. Do not include comments.'
                'Do not output any other text before or after the code.'
                }])
    
    code = chat_completion.choices[0].message.content[9:-3]
    
    # Search for plt.show() in the code and insert plt.savefig before it
    if 'plt.show()' in code:
        
        # Get the current timestamp and format it.
        current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        img_path = f"'./saved_imgs/img_{current_time}.png'"
        
        # Insert the savefig line right before plt.show()
        code = code.replace('plt.show()', f"plt.savefig({img_path})")

    # Execute the modified code
    exec(code)
    
    return img_path


class DescriberAgent:
    def __init__(self, llm):
        """
        Initialize the describer agent with an LLM instance.
        
        Args:
            llm (object): The LLM object (e.g., ChatOpenAI) used for generating descriptions.
        """
        self.llm = llm
    
    def invoke(self, prompt_data):
        """
        Invokes the LLM to generate a description based on the input prompt.
        
        Args:
            prompt_data (dict): Dictionary containing the input prompt with the key 'input'.
        
        Returns:
            dict: Dictionary containing the output response from the LLM.
        """
        # Extract the prompt from the prompt_data
        prompt = prompt_data["input"]

        # Prepare the prompt as a HumanMessage for the LLM
        message = [HumanMessage(content=prompt)]

        # Generate the response using the LLM
        response = self.llm.invoke(input=message)  # Using the correct method `invoke`
        print(response.content) 
        return response.content
    
def generate_dynamic_description(input_query, output):
    """
    Generates a description of the upcoming visualization by feeding the input and output to an LLM,
    based on a predefined schema for the description.
    
    Args:
        input_query (str): The original query made by the user.
        output (str): The response generated from the query.
    
    Returns:
        str: A dynamically generated explanation of what the image visualization will represent,
        following the predefined schema.
    """
    
    # Set up the LLM (e.g., OpenAI or ChatOpenAI)
    llm = ChatOpenAI(temperature=0.1, model="gpt-4o-mini")

    # Create an instance of the describer_agent
    describer_agent = DescriberAgent(llm)

    # Predefined schema for the description
    schema = """
    Please generate a description for the upcoming visualization following this structure:
    
    1. **Overview**: A brief overview of what the visualization is showing.
    2. **X-Axis Description**: Explain what the X-axis represents.
    3. **Y-Axis Description**: Explain what the Y-axis represents.
    4. **Key Metrics/Trends**: Mention any important metrics or trends that might be visualized.
    5. **Insights**: Provide potential insights or conclusions that can be drawn from the data visualization.
    
    Use concise language and focus on what the user will be able to learn from this visualization.
    """

    # Create the prompt for the LLM to explain what the output represents, using the schema
    prompt = f"""
    You are in charge of describing the output obtained from the following input query.
    
    Input query: {input_query}
    Output: {output}
    
    {schema}
    """

    # Use the describer_agent to generate the description
    explanation = describer_agent.invoke({"input": prompt})
    print(explanation)
    
    return explanation

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
    timestep_request = 'Please include together also the corresponding timestamps and format the response as a list of tuples. The first tuple should contain the name of the columns we are returning.'
    
    # 5.1: QRITA Health Values.
    room_choice = "QRITA"
    input_query = f"Please provide me the entire set of health values."    
    query_result = query_room(room_choice, input_query, agent_executor, timestep_request)
    
    # 5.2: QRITA Air Temperature Values.
    # room_choice = "QRITA"
    # input_query = "Please provide me the entire set of air temperature values in the room."
    # query_result = query_room(room_choice, input_query, agent_executor, timestep_request)
    
    # 5.3: ROOF Solar Radiation data.
    # room_choice = "ROOF"
    # input_query = "What was the solar radiation recently?"
    # query_result = query_room(room_choice, input_query, agent_executor, timestep_request)
    
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
    
    print(type(query_result['output']))
    
    ##### 6: VISUALIZATION #####
    response_type = check_response_type(query_result['output'])
    print(response_type)
    if response_type == 'list':
        df_img_visualization = build_dataframe_from_response(query_result['output'])
        print(df_img_visualization)
        img_path = generate_img_visualization(df_img_visualization, oaikey, input_query)
        response = {
        "response_message": generate_dynamic_description(input_query, query_result['output']),
        "includes_image": True,
        "image_path": img_path
    }
        return response
    
    elif response_type == 'string':
        response = {
        "response_message": query_result['output'],        
        "includes_image": False,
        "image_path": False
    }
        return response

    
    else:
        print("There should be an error in the type of response you're getting in output.")
    

if __name__ == "__main__":
    query_result = main()  