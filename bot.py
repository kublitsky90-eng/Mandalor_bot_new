import telebot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional

# Токен бота
TOKEN = "8295503667:AAEHfdeLyL158BE1qcRTLCpp0ya5BbzSFe4"
bot = telebot.TeleBot(TOKEN)

# Конфигурация
ADMIN_USERNAME = "@KuBiK90"  # Администратор бота
GUILD_URL = "https://swgoh.gg/g/j16DZ27ZQWe7UqWJP90zjg/"
DATA_FILE = "guild_data.json"
MESSAGE_ID_FILE = "message_id.txt"
CHAT_ID_FILE = "chat_id.txt"

# Роли
ROLES = ["Лидер", "Офицер", "Воин", "Неизвестный воин"]

# Мандалорские фразы
MANDALORIAN_PHRASES = [
    "Таков путь.",
    "Я мандалорец, оружие — часть моей религии.",
    "Я всё сказал.",
    "Я купил свою свободу мастерством своих рук и трудом трёх ваших человеческих жизней."
]

class GuildBot:
    def __init__(self):
        self.players = {}  # {player_name: {"tg_nick": str, "role": str}}
        self.list_message_id = None
        self.chat_id = None
        self.load_data()
        self.load_message_info()
        
    def get_mandalorian_phrase(self) -> str:
        """Возвращает случайную мандалорскую фразу"""
        import random
        return random.choice(MANDALORIAN_PHRASES)
    
    def parse_swgoh_gg(self) -> List[str]:
        """Парсит список участников с swgoh.gg"""
        try:
            response = requests.get(GUILD_URL)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем таблицу с участниками
            players = []
            # Адаптируйте селектор под структуру сайта
            name_elements = soup.select('.player-name a')
            
            for element in name_elements:
                name = element.text.strip()
                if name:
                    players.append(name)
            
            return players
        except Exception as e:
            print(f"Ошибка при парсинге: {e}")
            return []
    
    def initialize_from_website(self):
        """Инициализирует список игроков с сайта"""
        website_players = self.parse_swgoh_gg()
        for player in website_players:
            if player not in self.players:
                self.players[player] = {
                    "tg_nick": None,
                    "role": "Неизвестный воин"
                }
        self.save_data()
    
    def format_player_list(self) -> str:
        """Форматирует список игроков для вывода"""
        if not self.players:
            return "Список воинов пуст. Таков путь."
        
        # Сортируем по ролям и имени
        sorted_players = sorted(
            self.players.items(),
            key=lambda x: (ROLES.index(x[1]["role"]), x[0])
        )
        
        message = "🛡 **СПИСОК ВОИНОВ ГИЛЬДИИ MANDALORIANS KRYZE** 🛡\n\n"
        
        current_role = None
        for i, (player_name, player_info) in enumerate(sorted_players, 1):
            # Добавляем заголовок роли если сменилась
            if player_info["role"] != current_role:
                current_role = player_info["role"]
                message += f"\n**{current_role.upper()}:**\n"
            
            tg_nick = player_info["tg_nick"] if player_info["tg_nick"] else "❌ не указан"
            message += f"{i}. {player_name} - {tg_nick}\n"
        
        message += f"\n*{self.get_mandalorian_phrase()}*"
        return message
    
    def add_player(self, game_nick: str, tg_nick: str) -> bool:
        """Добавляет или обновляет игрока"""
        # Очищаем никнеймы
        game_nick = game_nick.strip()
        tg_nick = tg_nick.strip()
        
        # Проверяем существует ли игрок
        if game_nick in self.players:
            # Обновляем существующего
            self.players[game_nick]["tg_nick"] = tg_nick
            # Если был неизвестным воином, меняем роль на Воин
            if self.players[game_nick]["role"] == "Неизвестный воин":
                self.players[game_nick]["role"] = "Воин"
        else:
            # Добавляем нового
            self.players[game_nick] = {
                "tg_nick": tg_nick,
                "role": "Воин"
            }
        
        self.save_data()
        return True
    
    def remove_player(self, game_nick: str) -> bool:
        """Удаляет игрока"""
        if game_nick in self.players:
            del self.players[game_nick]
            self.save_data()
            return True
        return False
    
    def change_role(self, game_nick: str, new_role: str, user: str) -> bool:
        """Изменяет роль игрока (только для админов)"""
        if not self.is_admin(user):
            return False
        
        if game_nick in self.players and new_role in ROLES:
            self.players[game_nick]["role"] = new_role
            self.save_data()
            return True
        return False
    
    def is_admin(self, user: str) -> bool:
        """Проверяет является ли пользователь администратором"""
        return user == ADMIN_USERNAME
    
    def save_data(self):
        """Сохраняет данные в файл"""
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.players, f, ensure_ascii=False, indent=2)
    
    def load_data(self):
        """Загружает данные из файла"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    self.players = json.load(f)
            except:
                self.players = {}
        else:
            self.players = {}
            self.initialize_from_website()
    
    def save_message_info(self, chat_id: int, message_id: int):
        """Сохраняет ID сообщения и чата"""
        self.chat_id = chat_id
        self.list_message_id = message_id
        with open(MESSAGE_ID_FILE, 'w') as f:
            f.write(str(message_id))
        with open(CHAT_ID_FILE, 'w') as f:
            f.write(str(chat_id))
    
    def load_message_info(self):
        """Загружает ID сообщения и чата"""
        if os.path.exists(MESSAGE_ID_FILE) and os.path.exists(CHAT_ID_FILE):
            try:
                with open(MESSAGE_ID_FILE, 'r') as f:
                    self.list_message_id = int(f.read())
                with open(CHAT_ID_FILE, 'r') as f:
                    self.chat_id = int(f.read())
            except:
                self.list_message_id = None
                self.chat_id = None

# Инициализация бота
guild_bot = GuildBot()

def is_admin_or_officer(message: Message) -> bool:
    """Проверяет является ли пользователь администратором чата или бота"""
    if message.from_user.username and f"@{message.from_user.username}" == ADMIN_USERNAME:
        return True
    
    if message.chat.type == "private":
        return False
    
    try:
        member = bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in ['administrator', 'creator']
    except:
        return False

@bot.message_handler(commands=['start'])
def start(message: Message):
    """Обработчик команды /start"""
    welcome_text = (
        "🛡 **Приветствую, воин!** 🛡\n\n"
        "Я бот гильдии Mandalorians Kryze. Таков путь.\n\n"
        "**Доступные команды:**\n"
        "/list - Показать список воинов\n"
        "/update - Обновить список с сайта\n"
        "/help - Показать это сообщение\n\n"
        "**Как добавить себя в список:**\n"
        "Отправь сообщение в формате:\n"
        "`Ник в игре - @твой_ник_в_телеграм`\n\n"
        "Для администраторов:\n"
        "/role [ник в игре] [роль] - Изменить роль\n"
        "/remove [ник в игре] - Удалить воина"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def help_command(message: Message):
    start(message)

@bot.message_handler(commands=['list'])
def show_list(message: Message):
    """Показывает список игроков"""
    list_text = guild_bot.format_player_list()
    
    # Создаем клавиатуру для админов
    markup = None
    if is_admin_or_officer(message):
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("🔄 Обновить с сайта", callback_data="update_from_site"),
            InlineKeyboardButton("📝 Сохранить этот список", callback_data="save_list")
        )
    
    sent_message = bot.send_message(
        message.chat.id, 
        list_text, 
        parse_mode="Markdown",
        reply_markup=markup
    )
    
    # Сохраняем ID сообщения для последующего обновления
    guild_bot.save_message_info(message.chat.id, sent_message.message_id)

@bot.message_handler(commands=['update'])
def update_from_site(message: Message):
    """Обновляет список с сайта"""
    if not is_admin_or_officer(message):
        bot.reply_to(message, f"Ты не достоин этой команды, воин. {guild_bot.get_mandalorian_phrase()}")
        return
    
    bot.reply_to(message, "Обновляю список с сайта swgoh.gg. Это займет некоторое время...")
    guild_bot.initialize_from_website()
    
    # Обновляем сообщение со списком если оно есть
    if guild_bot.list_message_id and guild_bot.chat_id:
        try:
            bot.edit_message_text(
                guild_bot.format_player_list(),
                guild_bot.chat_id,
                guild_bot.list_message_id,
                parse_mode="Markdown"
            )
            bot.send_message(message.chat.id, "Список обновлен. Таков путь.")
        except:
            bot.send_message(message.chat.id, "Список обновлен, но не удалось обновить сообщение. Используй /list")

@bot.message_handler(commands=['role'])
def change_role(message: Message):
    """Изменяет роль игрока (только для админов)"""
    if not is_admin_or_officer(message):
        bot.reply_to(message, f"Ты не достоин этой команды, воин. {guild_bot.get_mandalorian_phrase()}")
        return
    
    try:
        command_parts = message.text.split(maxsplit=2)
        if len(command_parts) < 3:
            bot.reply_to(message, f"Использование: /role [ник в игре] [роль]\nДоступные роли: {', '.join(ROLES)}")
            return
        
        game_nick = command_parts[1]
        new_role = command_parts[2]
        
        if new_role not in ROLES:
            bot.reply_to(message, f"Неверная роль. Доступные роли: {', '.join(ROLES)}")
            return
        
        if guild_bot.change_role(game_nick, new_role, f"@{message.from_user.username}"):
            # Обновляем список
            if guild_bot.list_message_id and guild_bot.chat_id:
                try:
                    bot.edit_message_text(
                        guild_bot.format_player_list(),
                        guild_bot.chat_id,
                        guild_bot.list_message_id,
                        parse_mode="Markdown"
                    )
                except:
                    pass
            bot.reply_to(message, f"Роль воина {game_nick} изменена на {new_role}. {guild_bot.get_mandalorian_phrase()}")
        else:
            bot.reply_to(message, f"Воин {game_nick} не найден в списке.")
            
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

@bot.message_handler(commands=['remove'])
def remove_player(message: Message):
    """Удаляет игрока (только для админов)"""
    if not is_admin_or_officer(message):
        bot.reply_to(message, f"Ты не достоин этой команды, воин. {guild_bot.get_mandalorian_phrase()}")
        return
    
    try:
        game_nick = message.text.split(maxsplit=1)[1]
        
        if guild_bot.remove_player(game_nick):
            # Обновляем список
            if guild_bot.list_message_id and guild_bot.chat_id:
                try:
                    bot.edit_message_text(
                        guild_bot.format_player_list(),
                        guild_bot.chat_id,
                        guild_bot.list_message_id,
                        parse_mode="Markdown"
                    )
                except:
                    pass
            bot.reply_to(message, f"Воин {game_nick} удален из списка. {guild_bot.get_mandalorian_phrase()}")
        else:
            bot.reply_to(message, f"Воин {game_nick} не найден в списке.")
            
    except IndexError:
        bot.reply_to(message, "Использование: /remove [ник в игре]")

@bot.message_handler(func=lambda message: True)
def handle_player_add(message: Message):
    """Обрабатывает добавление игрока"""
    # Проверяем формат сообщения: "ник в игре - @ник в телеграм"
    text = message.text.strip()
    
    # Ищем паттерн с дефисом и @
    pattern = r'^(.+?)\s*-\s*(@.+)$'
    match = re.match(pattern, text)
    
    if match:
        game_nick = match.group(1).strip()
        tg_nick = match.group(2).strip()
        
        # Добавляем игрока
        guild_bot.add_player(game_nick, tg_nick)
        
        # Обновляем сообщение со списком
        if guild_bot.list_message_id and guild_bot.chat_id:
            try:
                bot.edit_message_text(
                    guild_bot.format_player_list(),
                    guild_bot.chat_id,
                    guild_bot.list_message_id,
                    parse_mode="Markdown"
                )
                bot.reply_to(message, f"Воин {game_nick} добавлен в список. {guild_bot.get_mandalorian_phrase()}")
            except Exception as e:
                bot.reply_to(message, f"Воин добавлен, но не удалось обновить список. Используй /list")
        else:
            bot.reply_to(message, f"Воин добавлен. Используй /list чтобы увидеть список.")
    else:
        # Если сообщение не соответствует формату, просто игнорируем или отвечаем стандартной фразой
        if text.lower() not in ['/start', '/help', '/list', '/update']:
            bot.reply_to(message, f"Я мандалорец, и я не понимаю твоих слов. Используй формат: Ник в игре - @ник в телеграмме")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    """Обработчик callback запросов от инлайн кнопок"""
    if call.data == "update_from_site":
        if is_admin_or_officer(call.message):
            bot.answer_callback_query(call.id, "Обновляю список с сайта...")
            guild_bot.initialize_from_website()
            bot.edit_message_text(
                guild_bot.format_player_list(),
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown"
            )
            bot.send_message(call.message.chat.id, "Список обновлен с сайта. Таков путь.")
        else:
            bot.answer_callback_query(call.id, "Ты не достоин этой команды!", show_alert=True)
    
    elif call.data == "save_list":
        guild_bot.save_message_info(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "Этот список теперь будет автоматически обновляться!")

if __name__ == "__main__":
    print("Бот Mandalorians Kryze запущен. Таков путь.")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Ошибка: {e}")