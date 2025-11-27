
"""Slack Notifier Stub"""
import requests

class SlackNotifier:
    def __init__(self, webhook):
        self.webhook = webhook

    def send(self, msg):
        requests.post(self.webhook, json={"text": msg})
