import socket
import threading

# fixes cmd colors looking wrong
import colorama
colorama.init()

# ---- init + get ip and port ---- 
HOST = input("Enter IP or leave blank for 127.0.0.1: ") or '127.0.0.1'
PORT = int(input("Enter PORT or leave blank for 5555: ") or 5555)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()
server.settimeout(1)

clients = []
usernames = []
commands = {}
running = True
user_colors = {}

# ANSI Color Codes
COLORS = {
    'red': '\033[91m', 'green': '\033[92m', 'yellow': '\033[93m',
    'blue': '\033[94m', 'magenta': '\033[95m', 'cyan': '\033[96m',
    'white': '\033[97m', 'reset': '\033[0m'
}

print("[SERVER] Started!! Waiting for connections...")

# Broadcast message to all clients
def broadcast(message):
    for client in clients[:]:
        try:
            client.send(message)
        except:
            remove_client(client)

# Remove client on disconnect
def remove_client(client):
    if client in clients:
        index = clients.index(client)
        clients.remove(client)
        username = usernames[index]
        usernames.remove(username)
        broadcast(f"[SERVER] {username} has left the chat.".encode('utf-8'))
        client.close()

# Handle individual client (MODIFIED to intercept client commands)
def handle_client(client):
    while running:
        try:
            message = client.recv(1024)
            if message:
                decoded = message.decode('utf-8')
                
                # Check for Server-bound Client Commands
                if decoded.startswith('/list'):
                    user_list = "Connected users:\n" + "\n".join([f" - {u}" for u in usernames])
                    client.send(f"[SERVER] {user_list}".encode('utf-8'))

                elif decoded.startswith('/setcolor'):
                    parts = decoded.split(" ", 1)
                    if len(parts) > 1:
                        color_name = parts[1].strip()
                        if client in clients:
                            idx = clients.index(client)
                            username = usernames[idx]
                            user_colors[username] = COLORS.get(color_name, COLORS['reset'])
                    
                elif decoded.startswith('/changename'):
                    parts = decoded.split(" ", 1)
                    if len(parts) > 1:
                        new_name = parts[1].strip()
                        if new_name in usernames:
                            client.send("[SERVER] Username already taken.".encode('utf-8'))
                        else:
                            if client in clients:
                                index = clients.index(client)
                                old_name = usernames[index]
                                usernames[index] = new_name
                                broadcast(f"[SERVER] {old_name} changed their name to {new_name}".encode('utf-8'))
                    else:
                        client.send("[SERVER] Usage: /changename <newname>".encode('utf-8'))
                        
                else:
                    # Normal broadcast
                    broadcast(message)
            else:
                remove_client(client)
                break
        except:
            remove_client(client)
            break

# Accept connections
def receive():
    global running
    while running:
        try:
            client, address = server.accept()
        except socket.timeout:
            continue
        except OSError:
            break

        print(f"[SERVER] {str(address)} started connecting...")

        try:
            client.send("USERNAME".encode('utf-8'))
            username = client.recv(1024).decode('utf-8')

            if username in usernames:
                client.send("Username already taken. Disconnecting.".encode('utf-8'))
                client.close()
                continue

            usernames.append(username)
            clients.append(client)
            user_colors[username] = COLORS['reset']

            #print(f"[USERNAME] {username}")
            broadcast(f"[SERVER] {username} joined the chat!".encode('utf-8'))

            thread = threading.Thread(target=handle_client, args=(client,), daemon=True)
            thread.start()

        except:
            client.close()

def kick_user(username):
    if username in usernames:
        index = usernames.index(username)
        client = clients[index]

        try:
            client.send("[SERVER] You have been kicked.".encode('utf-8'))
        except:
            pass

        remove_client(client)
        print(f"[SERVER] Kicked {username}")
    else:
        print("[SERVER] User not found.")

# -------------- Command handler (server console input) --------------
def register_command(name, func, description=""):
    commands[name] = {
        "func": func,
        "description": description
    }

def command_listener():
    global running
    while running:
        cmd = input().strip()

        if not cmd:
            continue

        parts = cmd.split(" ", 1)
        command_name = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command_name in commands:
            try:
                commands[command_name]["func"](args)
            except Exception as e:
                print(f"[SERVER] Error executing command: {e}")
        else:
            print("[SERVER] Unknown command. Type 'help' for a list of commands.")

# ---- COMMANDS ----
def cmd_quit(args):
    global running
    print("[SERVER] Shutting down...")
    shutdown_server()
    running = False

def cmd_list(args):
    print("[SERVER] Connected users:")
    for user in usernames:
        print(f" - {user}")

def cmd_kick(args):
    if not args:
        print("[SERVER] Usage: kick <username>")
        return
    kick_user(args)

def cmd_help(args):
    print("[SERVER] Available commands:")
    for name, data in commands.items():
        desc = data["description"]
        print(f" - {name}: {desc}")

# ---- REGISTER COMMANDS ----
register_command("quit", cmd_quit, "Shut down the server")
register_command("list", cmd_list, "List connected users")
register_command("kick", cmd_kick, "Kick a user: kick <username>")
register_command("help", cmd_help, "Show this help message")

# ---- Loop & Shutdown logic ----
def shutdown_server():
    global running
    running = False
    for client in clients:
        try:
            client.send("[SERVER] Server is shutting down.".encode('utf-8'))
            client.close()
        except:
            pass
    server.close()

# Start threads
threading.Thread(target=receive, daemon=True).start()
threading.Thread(target=command_listener, daemon=True).start()

# Handle Ctrl+C
try:
    while running:
        threading.Event().wait(0.5)
except KeyboardInterrupt:
    print("\n[SERVER] Ctrl+C detected.")
    shutdown_server()