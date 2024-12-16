import socket
import json

HOST = "192.168.1.65"  # IP address of server
PORT = 65432  # Port to listen


def send_event_to_server(event):
    print("Sending event")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print("connection established...")
        data = json.dumps(event)
        s.send(str.encode(data))
        print(f"message sent: {data}")
