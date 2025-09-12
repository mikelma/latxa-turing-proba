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
