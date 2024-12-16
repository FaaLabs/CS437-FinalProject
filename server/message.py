import os
from twilio.rest import Client
from dotenv import main
from datetime import datetime

main.load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
FROM_WHATSAPP_NUMBER = os.getenv("TWILIO_FROM_NUM")
TO_WHATSAPP_NUMBER = os.getenv("TWILIO_TO_NUM")

# Minutes to send message
MESSAGE_WAIT_MINS = 1
HOURS_FORMAT = "%H:%M:%S %p"
date_str = '2023-02-28 14:30:00'
date_format = '%Y-%m-%d %H:%M:%S.%f'


client = Client(ACCOUNT_SID, AUTH_TOKEN)

def client_send_message(message):
    print("Sending message...")
    print(message)
    client.messages.create(
        body=message, from_=FROM_WHATSAPP_NUMBER, to=TO_WHATSAPP_NUMBER
    )
    print("Message successfully sent.")


def send_whatsapp_notification(list_events):
    print("Sending notification...")
    # Build message from events list
    message = "Your cat has been seen in the following spots: \n"
    for event in list_events:
        timestamp = datetime.strptime(event.get("timestamp"), date_format)
        location = event.get("location")

        if location:
            message += f"* {timestamp.strftime(HOURS_FORMAT)} - {location} \n"
    client_send_message(message)


