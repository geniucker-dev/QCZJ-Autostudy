import json

import telebot
from telebot import apihelper

class TGBot:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.bot = telebot.TeleBot(token)

    def send_message(self, message):
        self.bot.send_message(self.chat_id, message)


if __name__ == "__main__":
    apihelper.proxy = {'https': 'socks5://localhost:7890', 'http': 'socks5://localhost:7890'}

    # get token from push.json
    with open('tgpush.json', 'r') as f:
        data = json.load(f)
        token = data['token']
        chat_id = data['chat_id']

    bot = TGBot(token, chat_id)

    bot.send_message("test")
