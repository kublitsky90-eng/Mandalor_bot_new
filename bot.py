import telebot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
import requests
import re
import random
import time
from typing import List

TOKEN = "8295503667:AAEHfdeLyL158BE1qcRTLCpp0ya5BbzSFe4"
bot = telebot.TeleBot(TOKEN)

ADMIN_USERNAME = "KuBiK90"
GUILD_ID = "j16DZ27ZQWe7UqWJP90zjg"
API_URL = f"https://swgoh.gg/api/guild-profile/{GUILD_ID}/"
DATA_FILE = "guild_data.json"

ROLES = ["Манд'алор", "Офицер", "Воин", "Неизвестный воин"]

class GuildBot:
    def __init__(self):
        self.players = {}
        self.load_data()
    
    def parse_swgoh_gg_api(self) -> List[str]:
        try:
            response = requests.get(API_URL, timeout=15)
            response.raise_for_status()
            data = response.json()
            members = data.get('data', {}).get('members', [])
            players = [m.get('player_name', '').strip() for m in members if m.get('player_name')]
            print(f"Найдено игроков: {len(players)}")
            return players
        except Exception as e:
            print(f"Ошибка API: {e}")
            return []
    
    def initialize_from_website(self):
        website_players = self.parse_swgoh_gg_api()
        if not website_players:
            return False
        
        for player in website_players:
            if player not in self.players:
                self.players[player] = {"tg_nick": None, "role": "Неизвестный воин"}
        
        self.save_data()
        return True
    
    def format_player_list(self) -> str:
        if not self.players:
            return "Список воинов пуст."
        
        lines = ["🛡 СПИСОК ВОИНОВ 🛡", ""]
        for i, (name, info) in enumerate(sorted(self.players.items()), 1):
            tg = info["tg_nick"] if info["tg_nick"] else "❌ не указан"
            lines.append(f"{i}. {name} - {tg}")
        lines.append(f"\nВсего: {len(self.players)}")
        return "\n".join(lines)
    
    def save_data(self):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.players, f, ensure_ascii=False, indent=2)
    
    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                self.players = json.load(f)

guild_bot = GuildBot()

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🛡 Бот гильдии Mandalorians Kryze запущен! Используй /list")

@bot.message_handler(commands=['list'])
def show_list(message):
    bot.reply_to(message, guild_bot.format_player_list())

@bot.message_handler(commands=['update'])
def update(message):
    msg = bot.reply_to(message, "Обновляю...")
    if guild_bot.initialize_from_website():
        bot.edit_message_text("✅ Обновлено! Используй /list", message.chat.id, msg.message_id)
    else:
        bot.edit_message_text("❌ Ошибка обновления", message.chat.id, msg.message_id)

if __name__ == "__main__":
    print("Бот запущен!")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(5)
