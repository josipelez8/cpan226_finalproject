import socket
import threading

HOST = input("Enter IP or leave blank for 127.0.0.1: ") or '127.0.0.1'
PORT = input("Enter PORT or leave blank for 5555: ") or 5555

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

username = input("Choose a username: ")

# Receive messages from server
def receive():
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if message == 'USERNAME':
                client.send(username.encode('utf-8'))
            else:
                print(message)
        except:
            print("[ERROR] Connection lost.")
            client.close()
            break

# Send messages to server
def write():
    while True:
        message = input()
        if message.strip() == "":
            continue
        full_message = f"{username}: {message}"
        try:
            client.send(full_message.encode('utf-8'))
        except:
            break

receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()