from typing import Optional
import random


class User:
    def __init__(self):
        self.counter = 0

    def log_message(self, user: str, msg: str) -> None:
        print(f"<<< [{user}] {msg}")

    def decide_message(self) -> Optional[str]:
        if random.uniform(0, 1) < 0.1:
            self.counter += 1
            msg = f"Hau {self.counter}. mezua da jeje"
            print(f">>> Sending message: '{msg}'")

        else:
            print("=== Not sending")
            msg = None

        return msg



class UserMonitor:
    def __init__(self, user: User, cpm: int = 280, cpm_std: int = 1.75):
        self.counter = 0

        self.user = user
        self.cpm = cpm # keystrokes per minute
        self.cpm_std = cpm_std # standard deviation of keystrokes per minute
    
    def check_history(self, history: list[dict[str, str]]) -> None:
        for entry in history:
            user = entry["user"]
            msg = entry["msg"]
            self.user.log_message(user, msg)

    def decide_message(self, history: list[dict[str, str]]) -> Optional[str]:
        if random.uniform(0, 1) < 0.1:
            self.counter += 1
            msg = f"Hau {self.counter}. mezua da jeje"
            print(f">>> Sending message: '{msg}'")
        else:
            print("=== Not sending")
            msg = None

        return msg

    def delay_message(self, msg: str) -> float:

        delay = random.gauss(len(msg) * 60 / self.cpm, self.cpm_std)
        print(f"=== Delaying message '{msg}' for {delay:.2f} seconds")

        # Minimum delay of 0.1 seconds
        return max(0.1, delay)



if __name__ == "__main__":
    user = User()
    monitor = UserMonitor(user)

    history = [
        {"user": "Alice", "msg": "Hello!"},
        {"user": "Bob", "msg": "Hi there!"}
    ]

    monitor.check_history(history)
    delay_time = monitor.delay_message("This is a test message. This is a test message. This is a test message.")
    print(f"Delay time: {delay_time:.2f} seconds")