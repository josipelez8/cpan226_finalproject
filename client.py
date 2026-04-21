import socket
import threading
import sys
import select

# fixes cmd colors looking wrong
import colorama
colorama.init()

# input valid username
while True:
    username = input("Choose a username: ").strip()
    if len(username) >= 1:
        break
    print("[CLIENT] Username must be at least 1 character.")

client_socket = None
connected = False
running = True
current_color = '\033[0m' # Default reset
commands = {}

# ANSI Color Codes
COLORS = {
    'red': '\033[91m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'magenta': '\033[95m',
    'cyan': '\033[96m',
    'white': '\033[97m',
    'reset': '\033[0m'
}

# Receive messages from server
def receive():
    global connected
    while connected:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break
                
            if message == 'USERNAME':
                client_socket.send(username.encode('utf-8'))
            else:
                print(message)
        except:
            if connected: # Only print error if we didn't intentionally disconnect
                print("[ERROR] Connection lost.")
                connected = False
            break

# -------------- Command handler --------------
def register_command(name, func, description=""):
    commands[name] = {
        "func": func,
        "description": description
    }

def cmd_quit(args):
    global running
    print("[CLIENT] Exiting application...")
    cmd_disconnect("")
    running = False
    sys.exit(0)

def cmd_connect(args):
    global client_socket, connected
    if connected:
        print("[CLIENT] You are already connected!")
        return
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        HOST = input("Enter IP or leave blank for 127.0.0.1: ") or '127.0.0.1'
        PORT = int(input("Enter PORT or leave blank for 5555: ") or 5555)

        client_socket.connect((HOST, PORT))
        connected = True
        threading.Thread(target=receive, daemon=True).start()
        print(f"[CLIENT] Connected to {HOST}:{PORT}")
    except Exception as e:
        print(f"[CLIENT] Connection failed: {e}")

def cmd_disconnect(args):
    global connected, client_socket
    if not connected:
        print("[CLIENT] You are not currently connected.")
        return
    connected = False
    try:
        client_socket.close()
    except:
        pass
    print("[CLIENT] Disconnected from server.")

def cmd_color(args):
    global current_color
    color_name = args.lower()
    if color_name in COLORS:
        current_color = COLORS[color_name]
        print(f"{current_color}[CLIENT] Username color changed to {color_name}!{COLORS['reset']}")
    
    if connected:
        client_socket.send(f"/setcolor {color_name}".encode('utf-8'))
    else:
        print(f"[CLIENT] Available colors: {', '.join(COLORS.keys())}")

def cmd_list(args):
    if connected:
        client_socket.send("/list".encode('utf-8'))
    else:
        print("[CLIENT] You must be connected to list users.")

def cmd_changename(args):
    global username
    if not args:
        print("[CLIENT] Usage: /changename <newname>")
        return
    if connected:
        client_socket.send(f"/changename {args}".encode('utf-8'))
    username = args # Update locally so newer messages use the new name
    print(f"[CLIENT] Local username set to {username}.")

def cmd_help(args):
    print("[CLIENT] Available commands (prefix with '/'):")
    for name, data in commands.items():
        print(f" - /{name}: {data['description']}")

# Register Client Commands
register_command("quit", cmd_quit, "Exit the chat application")
register_command("connect", cmd_connect, "Connect to the server")
register_command("disconnect", cmd_disconnect, "Disconnect from the server")
register_command("color", cmd_color, "Change username color: /color <color>")
register_command("list", cmd_list, "Ask server for a list of connected users")
register_command("changename", cmd_changename, "Change your username: /changename <newname>")
register_command("help", cmd_help, "Show this help message")

# Send messages or process commands
def write():
    while running:
        try:
            message = input()
            if not message.strip():
                continue
                
            # Check if it's a command
            if message.startswith('/'):
                parts = message[1:].split(" ", 1)
                cmd = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if cmd in commands:
                    commands[cmd]["func"](args)
                else:
                    print("[CLIENT] Unknown command. Type /help for a list of commands.")
            else:
                # Normal chat message
                if connected:
                    full_message = f"{current_color}{username}{COLORS['reset']}: {message}"
                    client_socket.send(full_message.encode('utf-8'))
                else:
                    print("[CLIENT] Not connected to server. Type /connect")
        except EOFError:
            break
        except Exception as e:
            if running:
                print(f"[ERROR] {e}")

# Initial auto-connect
print("Type /help to see available commands.")
#cmd_connect("")

# Start input loop on main thread
write()