import serial
import requests
import numpy as np
import cv2

# Configure the serial port
ser = serial.Serial('COM5', '2000000')

# Set up the HTTP endpoint
url = 'http://example.com/upload'  # Replace with your actual URL


def send_data(file_data):
    # Create the form data payload
    # Modify if you need additional form data parameters
    payload = {'File': file_data}

    # Send the HTTP request
    response = requests.post(url, files=payload)

    # Check the response
    if response.status_code == 200:
        print("Data sent successfully.")
    else:
        print("Failed to send data. Error code:", response.status_code)


def read_serial():
    image_data = ser.read(ser.in_waiting)
    send_data(image_data)


try:
    # Main program loop
    while True:
        read_serial()

except KeyboardInterrupt:
    # Clean up and exit on Ctrl+C
    ser.close()
    print("Exiting the program.")
