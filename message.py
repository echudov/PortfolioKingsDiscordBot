import datetime
import os
from dotenv import load_dotenv


class Strategy:
    def __init__(self, id, messages, status, users_reacted):
        self.id = id
        self.messages = messages
        self.reacted = users_reacted
        self.status = status

    def contains(self, message):
        if message.content in self.messages:
            return True
        else:
            return False

    def same_strategy(self, message):
        if self.id in message.content.lower():
            return True
        else:
            return False

    def add_message(self, message):
        self.messages.append(message.content)

    # Must be called every time a user reacts to a message for this strategy
    def react(self, user_react):
        if user_react.id in self.reacted:
            return
        else:
            self.reacted.append(user_react)