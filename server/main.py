import socket
from message import send_whatsapp_notification, MESSAGE_WAIT_MINS
from datetime import datetime, timedelta
import json

HOST = "192.168.1.65"
PORT = 65432

last_message_sent_at = datetime.now()
list_events = []
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"server listening on PORT {PORT}")

    try:
        while 1:
            client, clientInfo = s.accept()
            print("server recv from: ", clientInfo)
            data = client.recv(1024) 
            print("received data: ", data)
            event = data.decode("ascii")
            list_events.append(json.loads(event))
            print(list_events)

            time_now = datetime.now()
            should_send_message_at = last_message_sent_at + timedelta(
                minutes=MESSAGE_WAIT_MINS
            )

            if len(list_events) > 0 and (time_now >= should_send_message_at):
                send_whatsapp_notification(list_events)
                list_events = []
                last_message_sent_at = datetime.now()

    except SystemError:
        print("Closing socket")
        client.close()
        s.close()
