
# MQTT Broker Client Documentation

This documentation provides setup, usage, and configuration details for a Python-based MQTT client that subscribes to specific topics and logs received data into CSV files, organized by topic.

## Features

- **Topic-Specific CSV Logging**: Logs incoming MQTT messages into CSV files, with one file per topic.
- **Automatic File Management**: Automatically creates and manages CSV files for each topic.
- **Robust Logging**: Utilizes Python's `logging` library for detailed and configurable logging of operational status and errors.

## Prerequisites

Before using this script, you should have:

- **Python 3.x**: Ensure Python 3.x is installed on your system.
- **paho-mqtt**: This script uses the `paho-mqtt` library for handling MQTT communications.

## Installation

### Install Python

Download and install Python 3.x from the official Python website:

[Python Downloads](https://www.python.org/downloads/)

### Install paho-mqtt

Install the `paho-mqtt` library using pip:

```sh
pip install paho-mqtt
```

## Configuration

### Broker Details

Set the MQTT broker's address and port in the script:

```python
broker_address = "192.168.1.233"  # Replace with your broker's IP address
port = 1883                       # Replace with your broker's port
```

### Topic Subscriptions

Modify the list of topics to which the client subscribes:

```python
topics = [
    "envsensors/airQ/airQROB",
    "envsensors/airQ/airQRITA",
    "envsensors/airQ/airQMOMO",
    "envsensors/airQ/airQHANS",
    "envsensors/airQ/airQDORO",
    "envsensors/airQ/airQFOYER"
]
```

## Usage

To run the script, navigate to its directory in your command line interface and execute:

```sh
python mqtt_client.py
```

This command will start the MQTT client, which will connect to the configured broker, subscribe to the specified topics, and begin logging received data into CSV files.

## Logging

Logs are written both to the console and to a file named `mqtt_client.log`. The logging level and format can be adjusted by modifying the `logging.basicConfig` setup in the script:

```python
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("mqtt_client.log"),
                        logging.StreamHandler()
                    ])
```

## Troubleshooting

- **Connection Issues**: Ensure the broker's IP address and port are correctly set and that the broker is accessible from the network.
- **File Permissions**: Check if the script has the necessary permissions to create directories and files, especially on Linux and macOS systems.

## Further Assistance

For further support or queries, consult the `paho-mqtt` documentation or contact your network administrator for help with MQTT broker settings.

## Author 

- Hamed KShiem
- Email: keshim95@yahoo.com
- Linz Austria
