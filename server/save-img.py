import socket
from datetime import datetime

HOST = "192.168.1.65"
PORT = 65430


def save_image(file_path, data):
    with open(file_path, "wb") as file:
        file.write(data)
    print(f"Image saved to {file_path}")


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"server listening on PORT {PORT}...")

    try:
        while 1:
            client, clientInfo = s.accept()
            img_size_data = client.recv(4)
            img_size = int.from_bytes(img_size_data, "big")

            img_data = b""
            while len(img_data) < img_size:
                packet = client.recv(4096)
                if not packet:
                    break
                img_data += packet

            # Step 3: Save the received image
            save_image(f"images/{str(datetime.now())}", img_data)

    except SystemError:
        print("Closing socket")
        client.close()
        s.close()
