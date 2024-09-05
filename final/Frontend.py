import streamlit as st
import pandas as pd
import requests

# Streamlit app configuration
st.set_page_config(page_title="Talk to Your Data", page_icon="🦾", layout="centered")
st.title("Talk to JUNO 🦾")
st.markdown("###### Rooms: MOMO 🤺, DORO💻, ROOF 🏠, ROB 🤖, HANS 🛠️, RITA 🥽, and FOYER 🛋️")

st.sidebar.image("assets/CareConnetLogo.png", use_column_width=True)
st.sidebar.markdown("_________________________")

# Write description
st.sidebar.write("This is a data analysis tool that allows you to interact with your data using natural language, connecting your sensor data and asking questions about your data.")
# Add group members
st.sidebar.markdown("**Group Members** 💂‍♂️🥷🕵️‍♂️👩‍💻🧙")
st.sidebar.markdown("Oliver, Amina, Simone, Alissio, Hamed")
st.sidebar.markdown(" ")
st.sidebar.markdown("**Mentors:** 🫅")
st.sidebar.markdown("Dr. T from TU Graz")
st.sidebar.markdown("_________________________")
st.sidebar.image("assets/itulogo.png", use_column_width=True)

data = pd.read_csv("assets/precipitation.csv")

# Make options and reset button
col1, col2 = st.columns([4, 1])
with col1:
    options = st.multiselect(
        "Select a room", ["DORO", "MOMO", "ROOF", "ROB", "HANS", "RITA", "FOYER"],
        default=["DORO"], help="Select a room to query data from"
    )
with col2:
    if st.button("Reset", help="Reset the selected rooms", key="reset", use_container_width=True):
        st.session_state.messages = [{"role": "assistant", "content": "How can I help you?"}]

# Chat interface setup
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Handle user input and request data
if prompt := st.chat_input():
    # Append user's message to the session state
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Use the selected room or default to "ROOF"
    selected_room = options[0] if options else "ROOF"

    # Make the GET request to your local service
    url = "http://127.0.0.1:5000/get_data"
    params = {
        "room_choice": selected_room,
        "input_query": prompt
    }

    try:
        # Send request
        response = requests.get(url, params=params)
        print(response.json())
        if response.status_code == 200:
            # Process and display the response
            msg = response.json().get("response_message", "No data returned.")
            #add image to the body of msg
            path = response.json().get("image_path")
            if not path:
                st.image(path, use_column_width=True)
            st.session_state.messages.append({"role": "assistant", "content": msg})
         #   st.chat_message("assistant").write(msg)
          #  st.chat_message("assistant").image(path, use_column_width=True)
        else:
            st.error(f"Request failed with status code {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred: {e}")
