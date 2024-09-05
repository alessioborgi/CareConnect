import streamlit as st 
import pandas as pd
from langchain_openai import ChatOpenAI
from pandasai import SmartDataframe
from openai import OpenAI

#TODO: import engine and retrieve data from the rooms

st.set_page_config(page_title="Talk to Your Data", page_icon="🦾", layout="centered")
st.title("Talk to JUNO 🦾")
st.markdown("###### Rooms: MOMO 🤺, DORO💻, ROOF 🏠, ROB 🤖, HANS 🛠️, RITA 🥽, and FOYER 🛋️")

st.sidebar.image("assets/CareConnetLogo.png", use_column_width=True)
st.sidebar.markdown("_________________________")

#write description
st.sidebar.write("This is a data analysis tool that allows you to interact with your data using natural language. connecting your sensor data and ask questions about your data.")
#add contact
#st.sidebar.write("Contact: it-u" + " " + "careconnet.com")

st.sidebar.markdown(" ")
#add line in markdown
#add group members
#st.sidebar.write("Group 8 : the best team")
#add group members
st.sidebar.markdown("**Group Members** 💂‍♂️🥷🕵️‍♂️👩‍💻🧙")
st.sidebar.markdown("Oliver, Amina, Simone, Alissio, Hamed")
st.sidebar.markdown(" ")

st.sidebar.markdown("**Mentors:** 🫅")
st.sidebar.markdown("Dr. T from TU Graz")
st.sidebar.markdown(" ")
st.sidebar.markdown(" ")
st.sidebar.markdown(" ")
st.sidebar.markdown(" ")


#add line in markdown
st.sidebar.markdown("_________________________")
#add logo
st.sidebar.image("assets/itulogo.png", use_column_width=True)

data = pd.read_csv("assets/precipitation.csv")
#st.write(data.head(3))

openai_api_key = "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"

if not openai_api_key.startswith("sk-"):
    st.warning("Please enter your OpenAI API key!", icon="⚠️")
    



#st.image("temp_chart.png", use_column_width=True)
                

#add reset button

    
#make options and reset in the same row tow columns
col1, col2 = st.columns([4, 1])
with col1:
    options = st.multiselect("Select a room", ["DORO", "MOMO", "ROOF", "ROB", "HANS", "RITA", "FOYER"], default=["DORO"], help="Select a room to query data from")
with col2:
    if st.button("Reset", help="Reset the selected rooms", key="reset",use_container_width=True):
        st.write(" ")
        st.session_state.messages = [{"role": "assistant", "content": "How can I help you?"}]
    


if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    client = OpenAI(api_key=openai_api_key)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    response = client.chat.completions.create(model="gpt-3.5-turbo", messages=st.session_state.messages)
    msg = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)

