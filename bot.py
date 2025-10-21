import socket
import time
import selectors
from argparse import ArgumentParser
import yaml

from user import User, UserMonitor


def parse_args():
    parser = ArgumentParser()

    # fmt: off
    parser.add_argument("--server", type=str, default="irc.libera.chat")
    parser.add_argument("--port", type=int, default=6667)
    parser.add_argument("--user-config", type=str, default="latxa_behaviours/default.yaml")
    parser.add_argument("-n", "--nick", type=str, default="latxa")
    parser.add_argument("-c", "--channel", type=str, default="#latxa-turing")
    parser.add_argument("-w", "--init-wait", type=int, default=1,
        help="waiting time from joining the channel to first msg decission",
    )
    # fmt: on

    return parser.parse_args()


# Function to send data to the IRC server
def send_data(irc_socket, data):
    irc_socket.send((data + "\r\n").encode("utf-8"))


# Function to send a message to the channel
def send_message(irc_socket, channel, message):
    send_data(irc_socket, f"PRIVMSG {channel} :{message}")


args = parse_args()

# Load user configuration
with open(args.user_config) as stream:
    try:
        user_config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        exit(0)

user = User(user_config=user_config)
user_monitor = UserMonitor(user=user, config=user_config)


sel = selectors.DefaultSelector()

# Create a socket and connect to the IRC server
irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
irc.connect((args.server, args.port))

# Send user information to the server
send_data(irc, f"NICK {args.nick}")
send_data(irc, f"USER {args.nick} {args.nick} {args.nick} :{args.nick}")

# Wait for the welcome message from the server before joining the channel
while True:
    data = irc.recv(4096).decode("utf-8", "ignore")
    print("\x1b[34m" + data + "\x1b[0m", end="")
    if "Welcome" in data:
        break
    time.sleep(1)

# Join the specified channel
send_data(irc, f"JOIN {args.channel}")
print(f"Joined {args.channel}")

# Set socket to non-blocking
irc.setblocking(False)
# Register socket for "writable" events so we know when the connection finishes
sel.register(irc, selectors.EVENT_WRITE)

time_last_message = time.time()
time_wait = args.init_wait
msg_recieved = False

while True:
    if time.time() - time_last_message >= time_wait or msg_recieved:
        msg_recieved = False
        # Decide whether to write to the channel or not
        result = user_monitor.decide_message()
        if result is not None:
            send_message(irc, args.channel, result)
            if user_config["proactivity"]["enable_trigger_after_own_msg"]:
                msg_recieved = True
        time_wait = user_monitor.wait_until_next_decision()
        time_last_message = time.time()

    events = sel.select(timeout=1)

    for key, mask in events:
        # Socket is writeable
        if mask & selectors.EVENT_WRITE:
            # Switch to reading mode
            sel.unregister(irc)
            sel.register(irc, selectors.EVENT_READ)

        elif mask & selectors.EVENT_READ:
            data = irc.recv(4096).decode("utf-8", "ignore")
            print("\x1b[34m" + data + "\x1b[0m", end="")

            # Respond to server PING to avoid disconnection
            if data.startswith("PING"):
                send_data(irc, data.replace("PING", "PONG"))

            # Check for messages in the channel
            if "PRIVMSG" in data:
                try:
                    # Parse the message
                    message_parts = data.split("PRIVMSG")[1].strip().split(":", 1)
                    sender_nick = data.split("!")[0][1:]
                    target_channel = message_parts[0].strip()
                    message_text = message_parts[1].strip()

                    user.log_message(sender_nick, message_text)
                    if user_config["proactivity"]["enable_trigger_after_msg"]:
                        if sender_nick != args.nick:
                            time_last_message = time.time()
                            msg_recieved = True

                    # Check for the debug command "!test"
                    if message_text == "!test":
                        send_message(
                            irc,
                            target_channel,
                            f"Hello, {sender_nick}! I'm still alive!",
                        )

                except IndexError:
                    # Handle malformed messages without crashing
                    pass
