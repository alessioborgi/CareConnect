import os
import csv
import json
import logging
import paho.mqtt.client as mqtt

# Setup logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("mqtt_client.log"),
                        logging.StreamHandler()
                    ])

# Define the path for data storage
data_dir = "data"
if not os.path.exists(data_dir):
    os.makedirs(data_dir)
    logging.info(f"Created directory {data_dir}")

# List of topics to subscribe to
topics = [
    "envsensors/airQ/airQROB",
    "envsensors/airQ/airQRITA",
    "envsensors/airQ/airQMOMO",
    "envsensors/airQ/airQHANS",
    "envsensors/airQ/airQDORO",
    "envsensors/airQ/airQFOYER"
]

# Callback when a message is received
def on_message(client, userdata, message):
    topic = message.topic
    payload = message.payload.decode()
    logging.info(f"Received message on topic: {topic}")
    logging.debug(f"Payload: {payload}")

    # Determine filename based on the topic
    filename = topic.split("/")[-1] + ".csv"
    filepath = os.path.join(data_dir, filename)

    # Convert string payload to dictionary
    data = json.loads(payload)

    # Check if file exists and append data or write header
    file_exists = os.path.exists(filepath)
    with open(filepath, 'a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(data.keys())
            logging.info(f"Created new file {filename} and wrote header")
        writer.writerow(data.values())
        logging.info(f"Appended data to {filename}")

# Callback when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to the broker!")
        # Subscribe to all specified topics
        for topic in topics:
            client.subscribe(topic)
            logging.info(f"Subscribed to {topic}")
    else:
        logging.error(f"Failed to connect, return code {rc}")

# Callback when the client disconnects from the broker
def on_disconnect(client, userdata, rc):
    if rc != 0:
        logging.warning("Unexpected disconnection.")

# Setup the MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

# Connect to the MQTT broker
broker_address = "192.168.1.233"
port = 1883
client.connect(broker_address, port=port)
logging.info(f"Attempting to connect to MQTT broker at {broker_address}:{port}")

# Start the loop to process MQTT events
client.loop_start()

# Keep the main thread running
try:
    while True:
        pass
except KeyboardInterrupt:
    logging.info("Exiting gracefully")
finally:
    client.loop_stop()
    client.disconnect()
    logging.info("MQTT client disconnected and loop stopped")
