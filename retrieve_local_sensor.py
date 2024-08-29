import base64
import json
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad as crypto_unpad
import http.client

########################
airqIP = '192.168.1.232'
airqpass = 'airqsetup'
#########################

# Function to unpad the decrypted data (assuming PKCS7 padding)
def unpad(data):
    return crypto_unpad(data, AES.block_size)

# Function to decode the base64 encoded message and decrypt it using AES
def decodeMessage(msgb64):
    # Base64 decode
    encrypted_data = base64.b64decode(msgb64)

    # Use the airqpass as the AES key and derive the IV (Initialization Vector)
    key = airqpass.encode('utf-8')  # Ensure the password is bytes
    iv = encrypted_data[:AES.block_size]  # Extract the first 16 bytes as IV
    cipher = AES.new(key, AES.MODE_CBC, iv)

    # Decrypt the message
    decrypted_data = cipher.decrypt(encrypted_data[AES.block_size:])

    # Unpad the decrypted data
    decrypted_data = unpad(decrypted_data)

    # Convert bytes to string (UTF-8)
    return decrypted_data.decode('utf-8')

# Open connection to air-Q
connection = http.client.HTTPConnection(airqIP)

# Request data
connection.request("GET", "/data")
contents = connection.getresponse()

# Decrypt and print data
msg = json.loads(contents.read())
msg['content'] = json.loads(decodeMessage(msg['content']))
print(json.dumps(msg['content']))

# Close connection
connection.close()