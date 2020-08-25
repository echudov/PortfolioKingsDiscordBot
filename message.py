import datetime
import os
from dotenv import load_dotenv


class Strategy:
    def __init__(self, id, role, messages, status, users_reacted):
        self.id = id
        self.messages = messages
        self.reacted = users_reacted
        self.status = status
        self.role = role

    def contains(self, message):
        if message in self.messages:
            return True
        else:
            return False

    def same_strategy(self, message):
        if self.id in message.content.lower():
            return True
        else:
            return False

    def add_message(self, message):
        self.messages.append(message)

    # Must be called every time a user reacts to a message for this strategy
    def react(self, user_react):
        if user_react in self.users_reacted:
            return
        else:
            self.users_reacted.append(user_react)