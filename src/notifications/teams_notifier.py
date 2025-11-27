
"""Teams Notifier Stub"""
import requests

class TeamsNotifier:
    def __init__(self, webhook):
        self.webhook = webhook

    def send(self, msg):
        requests.post(self.webhook, json={"text": msg})
