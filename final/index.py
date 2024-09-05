import subprocess

# Run the data retriever from the rooms to fetch the csv files
subprocess.run(["python", "script3.py"])

# Run the data retriever from the roof to fetch the csv files
subprocess.run(["python", "script3.py"])

# Run the first Python script the engine
subprocess.run(["python", "script1.py"])

# Run the FE Streamlit app
subprocess.run(["python", "-m", "streamlit", "run", "fe.py"])

