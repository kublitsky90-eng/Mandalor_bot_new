import telebot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import json
import os
import requests
from bs4 import BeautifulSoup
import re
import random
import time
from typing import Dict, List, Optional, Tuple

# Токен бота
TOKEN = "8295503667:AAEHfdeLyL158BE1qcRTLCpp0ya5BbzSFe4"
bot = telebot.TeleBot(TOKEN)

# Конфигурация
ADMIN_USERNAME = "KuBiK90"  # БЕЗ @ в начале
ADMIN_USERNAME_WITH_AT = "@KuBiK90"
GUILD_URL = "https://swgoh.gg/g/j16DZ27ZQWe7UqWJP90zjg/"
DATA_FILE = "guild_data.json"
MESSAGE_ID_FILE = "message_id.txt"
CHAT_ID_FILE = "chat_id.txt"

# 👇 ID вашего канала
CHANNEL_CHAT_ID = -1002068153965

# Роли (Манд'алор теперь первый в списке)
ROLES = ["Манд'алор", "Офицер", "Воин", "Неизвестный воин"]
ROLE_EMOJI = {
    "Манд'алор": "👑",
    "Офицер": "⚔️",
    "Воин": "🛡️",
    "Неизвестный воин": "❓"
}

# Мандалорские фразы
MANDALORIAN_PHRASES = [
    "Таков путь.",
    "Я мандалорец, оружие — часть моей религии.",
    "Я всё сказал.",
    "Я купил свою свободу мастерством своих рук и трудом трёх ваших человеческих жизней.",
    "Это — путь мандалорца.",
    "Наше дело правое, Таков путь."
]

class GuildBot:
    def __init__(self):
        self.players = {}  # {player_name: {"tg_nick": str, "role": str}}
        self.list_message_id = None
        self.chat_id = None
        self.last_update = None
        self.load_data()
        self.load_message_info()
        
    def get_mandalorian_phrase(self) -> str:
        """Возвращает случайную мандалорскую фразу"""
        return random.choice(MANDALORIAN_PHRASES)
    
    def parse_swgoh_gg_direct(self) -> List[str]:
        """Прямой парсинг таблицы гильдии с сайта swgoh.gg"""
        try:
            print(f"Парсинг сайта: {GUILD_URL}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(GUILD_URL, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            players = []
            
            # Ищем таблицу гильдии
            guild_table = soup.find('table', {'class': re.compile(r'guild-members-table|table')})
            
            if guild_table:
                rows = guild_table.find_all('tr')
                print(f"Найдено строк в таблице: {len(rows)}")
                
                for row in rows:
                    if row.find('th'):
                        continue
                    cols = row.find_all('td')
                    if cols and len(cols) >= 1:
                        name_cell = cols[0]
                        name_link = name_cell.find('a')
                        if name_link:
                            name = name_link.text.strip()
                            if name and len(name) > 1 and name not in players:
                                players.append(name)
                                print(f"Найден игрок: {name}")
            
            print(f"Всего найдено игроков: {len(players)}")
            return players
            
        except Exception as e:
            print(f"Ошибка при прямом парсинге: {e}")
            return []
    
    def initialize_from_website(self):
        """Инициализирует список игроков с сайта"""
        print("Начинаем инициализацию списка с сайта...")
        
        website_players = self.parse_swgoh_gg_direct()
        
        if not website_players:
            print("Не удалось загрузить с сайта, используем тестовый список")
            website_players = [
                "Just Alex", "Leon", "MarkArt", "Qbik", "Kero Kurn", "Zephyr", "pyzer",
                "Джонни", "Viking", "MrCucumber", "Phasma47", "iSlon", "Рейнджер",
                "Frostman", "Anaken", "Frost43", "Snape T1one", "першак", "Nogitsune",
                "Тигра", "TantenPisyun", "Frederic Nedjam", "Veskasa Stargazer",
                "alpha seed", "Maxim Nikolaev", "HEKPACUBO", "screammer24", "Gazoniy",
                "Stolz", "Jeffcheasey", "Sibirisch", "Merioon Valhoun", "Koyo",
                "Mymtimin", "DevotedEvil", "Ultmaru", "SËMA26", "M21", "WITCHER",
                "SKolyveN", "TenhuZ", "магистор рогнар", "KALAHAN", "Anasteisha",
                "DambldorSuka", "Rakot", "Vvdxz", "Usbik", "BarsD3", "Boogeyman"
            ]
        
        # Обновляем список игроков
        new_players_count = 0
        for player in website_players:
            if player not in self.players:
                self.players[player] = {
                    "tg_nick": None,
                    "role": "Неизвестный воин"
                }
                new_players_count += 1
        
        print(f"Загружено {len(website_players)} игроков с сайта")
        print(f"Добавлено новых: {new_players_count}")
        
        self.save_data()
        self.last_update = time.time()
    
    def fix_roles(self) -> int:
        """Заменяет 'Лидер' на 'Манд'алор' во всех данных"""
        count = 0
        for player_info in self.players.values():
            if player_info["role"] == "Лидер":
                player_info["role"] = "Манд'алор"
                count += 1
        if count > 0:
            self.save_data()
        return count
    
    def format_player_list(self) -> str:
        """Форматирует список игроков для вывода (без Markdown)"""
        try:
            if not self.players:
                return "🛡 Список воинов пуст. Таков путь."
            
            # Принудительно преобразуем все роли "Лидер" в "Манд'алор" при выводе
            for player_info in self.players.values():
                if player_info["role"] == "Лидер":
                    player_info["role"] = "Манд'алор"
            
            # Сортируем по ролям (Манд'алор первый) и имени
            sorted_players = sorted(
                self.players.items(),
                key=lambda x: (ROLES.index(x[1]["role"]) if x[1]["role"] in ROLES else 999, x[0].lower())
            )
            
            message_lines = []
            message_lines.append("🛡 СПИСОК ВОИНОВ ГИЛЬДИИ MANDALORIANS KRYZE 🛡")
            message_lines.append("")
            
            current_role = None
            role_counts = {role: 0 for role in ROLES}
            counter = 1
            
            for player_name, player_info in sorted_players:
                role_counts[player_info["role"]] = role_counts.get(player_info["role"], 0) + 1
                
                if player_info["role"] != current_role:
                    current_role = player_info["role"]
                    emoji = ROLE_EMOJI.get(current_role, "•")
                    message_lines.append("")
                    message_lines.append(f"{emoji} {current_role.upper()}:")
                
                tg_nick = player_info["tg_nick"] if player_info["tg_nick"] else "❌ не указан"
                message_lines.append(f"{counter}. {player_name} - {tg_nick}")
                counter += 1
            
            message_lines.append("")
            message_lines.append("Статистика:")
            for role, count in role_counts.items():
                if count > 0:
                    emoji = ROLE_EMOJI.get(role, "•")
                    message_lines.append(f"{emoji} {role}: {count}")
            
            message_lines.append("")
            message_lines.append(f"Всего воинов: {len(self.players)}")
            if self.last_update:
                message_lines.append(f"Последнее обновление: {time.strftime('%d.%m.%Y %H:%M', time.localtime(self.last_update))}")
            message_lines.append("")
            message_lines.append(self.get_mandalorian_phrase())
            
            return "\n".join(message_lines)
            
        except Exception as e:
            print(f"Ошибка форматирования списка: {e}")
            return "🛡 Ошибка при формировании списка. Таков путь."
    
    def add_player(self, game_nick: str, tg_nick: str = None) -> bool:
        """Добавляет или обновляет игрока"""
        try:
            game_nick = game_nick.strip()
            if tg_nick:
                tg_nick = tg_nick.strip()
            
            found = False
            for existing_nick in list(self.players.keys()):
                if existing_nick.lower() == game_nick.lower():
                    if tg_nick:
                        self.players[existing_nick]["tg_nick"] = tg_nick
                    if self.players[existing_nick]["role"] == "Неизвестный воин":
                        self.players[existing_nick]["role"] = "Воин"
                    found = True
                    print(f"Игрок {existing_nick} обновлен с tg ником {tg_nick}")
                    break
            
            if not found:
                self.players[game_nick] = {
                    "tg_nick": tg_nick,
                    "role": "Воин"
                }
                print(f"Добавлен новый игрок {game_nick} с tg ником {tg_nick}")
            
            self.save_data()
            self.last_update = time.time()
            return True
        except Exception as e:
            print(f"Ошибка добавления игрока: {e}")
            return False
    
    def remove_player(self, game_nick: str) -> bool:
        """Удаляет игрока"""
        try:
            for existing_nick in list(self.players.keys()):
                if existing_nick.lower() == game_nick.lower():
                    del self.players[existing_nick]
                    self.save_data()
                    self.last_update = time.time()
                    print(f"Игрок {existing_nick} удален")
                    return True
            return False
        except Exception as e:
            print(f"Ошибка удаления игрока: {e}")
            return False
    
    def change_role(self, game_nick: str, new_role: str, user: str) -> Tuple[bool, str]:
        """Изменяет роль игрока"""
        try:
            if not self.can_change_roles(user):
                return False, "У тебя нет права изменять роли, воин."
            
            # Нормализуем роль (должна быть из списка ROLES)
            if new_role not in ROLES:
                return False, f"Неверная роль. Доступные роли: {', '.join(ROLES)}"
            
            # Поиск игрока без учета регистра
            for existing_nick in self.players.keys():
                if existing_nick.lower() == game_nick.lower():
                    old_role = self.players[existing_nick]["role"]
                    self.players[existing_nick]["role"] = new_role
                    self.save_data()
                    self.last_update = time.time()
                    print(f"Роль {existing_nick} изменена с {old_role} на {new_role}")
                    return True, f"Роль воина {existing_nick} изменена с '{old_role}' на '{new_role}'. {self.get_mandalorian_phrase()}"
            
            return False, f"Воин {game_nick} не найден в списке."
        except Exception as e:
            print(f"Ошибка изменения роли: {e}")
            return False, f"Ошибка: {e}"
    
    def can_change_roles(self, user: str) -> bool:
        """Проверяет может ли пользователь менять роли"""
        try:
            clean_user = user.replace('@', '').lower().strip()
            clean_admin = ADMIN_USERNAME.lower().replace('@', '').strip()
            
            if clean_user == clean_admin:
                print(f"✅ Админ бота {user} имеет право менять роли")
                return True
            
            user_tg_nick = f"@{clean_user}" if not clean_user.startswith('@') else clean_user
            
            for player_info in self.players.values():
                if player_info.get("tg_nick"):
                    player_tg = player_info["tg_nick"].lower().strip()
                    if player_tg == user_tg_nick.lower():
                        if player_info["role"] in ["Манд'алор", "Офицер"]:
                            print(f"✅ {player_info['role']} имеет право менять роли")
                            return True
            
            return False
        except Exception as e:
            print(f"Ошибка проверки прав: {e}")
            return False
    
    def is_admin(self, user: str) -> bool:
        """Проверяет является ли пользователь администратором бота"""
        clean_user = user.replace('@', '').lower().strip()
        clean_admin = ADMIN_USERNAME.lower().replace('@', '').strip()
        return clean_user == clean_admin
    
    def save_data(self):
        """Сохраняет данные в файл"""
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'players': self.players,
                    'last_update': self.last_update
                }, f, ensure_ascii=False, indent=2)
            print(f"Данные сохранены в {DATA_FILE}")
        except Exception as e:
            print(f"Ошибка сохранения данных: {e}")
    
    def load_data(self):
        """Загружает данные из файла"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.players = data.get('players', {})
                    self.last_update = data.get('last_update')
                print(f"Данные загружены из {DATA_FILE}, игроков: {len(self.players)}")
            except Exception as e:
                print(f"Ошибка загрузки данных: {e}")
                self.players = {}
                self.initialize_from_website()
        else:
            print(f"Файл {DATA_FILE} не найден, инициализация с сайта")
            self.players = {}
            self.initialize_from_website()
    
    def save_message_info(self, chat_id: int, message_id: int):
        """Сохраняет ID сообщения и чата"""
        self.chat_id = chat_id
        self.list_message_id = message_id
        try:
            with open(MESSAGE_ID_FILE, 'w') as f:
                f.write(str(message_id))
            with open(CHAT_ID_FILE, 'w') as f:
                f.write(str(chat_id))
        except Exception as e:
            print(f"Ошибка сохранения информации о сообщении: {e}")
    
    def load_message_info(self):
        """Загружает ID сообщения и чата"""
        if os.path.exists(MESSAGE_ID_FILE) and os.path.exists(CHAT_ID_FILE):
            try:
                with open(MESSAGE_ID_FILE, 'r') as f:
                    self.list_message_id = int(f.read())
                with open(CHAT_ID_FILE, 'r') as f:
                    self.chat_id = int(f.read())
            except Exception as e:
                print(f"Ошибка загрузки информации о сообщении: {e}")
                self.list_message_id = None
                self.chat_id = None

# Инициализация бота
guild_bot = GuildBot()

# Функция для отправки в канал (только если сообщение пришло из канала и это не команда)
def send_to_channel_if_needed(message: Message, text: str, reply_markup=None):
    """Отправляет сообщение в канал только если оно пришло из канала"""
    try:
        # Проверяем, пришло ли сообщение из канала
        if message.chat.id == CHANNEL_CHAT_ID:
            # Проверяем, не является ли это ответом на команду (чтобы избежать дублирования)
            if not message.text.startswith('/'):
                # Отправляем в ту же тему (если есть)
                bot.send_message(
                    chat_id=CHANNEL_CHAT_ID,
                    text=text,
                    message_thread_id=message.message_thread_id,
                    reply_markup=reply_markup
                )
                print(f"✅ Сообщение отправлено в канал (тема: {message.message_thread_id})")
    except Exception as e:
        print(f"❌ Ошибка отправки в канал: {e}")

def can_change_roles(message: Message) -> bool:
    """Проверяет может ли пользователь менять роли"""
    if not message.from_user or not message.from_user.username:
        return False
    
    username = message.from_user.username
    
    # Админ бота всегда может
    if username.lower() == ADMIN_USERNAME.lower().replace('@', ''):
        return True
    
    # Проверяем роль в списке
    user_tg_nick = f"@{username}"
    for player_info in guild_bot.players.values():
        if player_info.get("tg_nick") and player_info["tg_nick"].lower() == user_tg_nick.lower():
            if player_info["role"] in ["Манд'алор", "Офицер"]:
                return True
    
    return False

@bot.message_handler(commands=['start'])
def start(message: Message):
    """Обработчик команды /start"""
    try:
        username = message.from_user.username if message.from_user.username else "без ника"
        can_change = can_change_roles(message)
        
        user_status = "АДМИН БОТА" if guild_bot.is_admin(f"@{username}") else \
                      "МАНД'АЛОР/ОФИЦЕР" if can_change else \
                      "воин"
        
        welcome_text = (
            f"🛡 Приветствую, воин! 🛡\n\n"
            f"Я бот гильдии Mandalorians Kryze. Таков путь.\n"
            f"Твой ник: @{username}\n"
            f"Твой статус: {user_status}\n"
            f"Права на роли: {'✅' if can_change else '❌'}\n\n"
            f"Доступные команды:\n"
            f"/list - Показать список воинов\n"
            f"/update - Обновить список с сайта\n"
            f"/help - Показать это сообщение\n\n"
            f"Добавление в список:\n"
            f"• /add Qbik - @KuBiK90 - добавить игрока\n"
            f"• Или просто отправь: Qbik - @KuBiK90\n\n"
            f"Управление (только Манд'алор/Офицер):\n"
            f"• /remove Qbik - удалить игрока\n"
            f"• /role Qbik Манд'алор - изменить роль\n"
            f"Доступные роли: {', '.join(ROLES)}"
        )
        bot.reply_to(message, welcome_text)
        
    except Exception as e:
        print(f"Ошибка в /start: {e}")
        bot.reply_to(message, "Ошибка при запуске. Таков путь.")

@bot.message_handler(commands=['help'])
def help_command(message: Message):
    start(message)

@bot.message_handler(commands=['list'])
def show_list(message: Message):
    """Показывает список игроков"""
    try:
        list_text = guild_bot.format_player_list()
        print(f"Отправка списка, длина: {len(list_text)} символов")
        
        # Создаем клавиатуру для тех, у кого есть права
        markup = None
        if can_change_roles(message):
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("🔄 Обновить с сайта", callback_data="update_from_site"),
                InlineKeyboardButton("📝 Сохранить этот список", callback_data="save_list")
            )
        
        # Отправляем пользователю
        sent_message = bot.send_message(
            message.chat.id, 
            list_text,
            message_thread_id=message.message_thread_id,
            reply_markup=markup
        )
        
        guild_bot.save_message_info(message.chat.id, sent_message.message_id)
        print(f"Список отправлен, message_id: {sent_message.message_id}")
        
    except Exception as e:
        print(f"Ошибка в /list: {e}")
        error_msg = f"❌ Ошибка при формировании списка: {str(e)[:100]}"
        bot.reply_to(message, error_msg)

@bot.message_handler(commands=['update'])
def update_from_site(message: Message):
    """Обновляет список с сайта"""
    if not can_change_roles(message):
        reply = f"Ты не достоин этой команды, воин. {guild_bot.get_mandalorian_phrase()}"
        bot.reply_to(message, reply)
        return
    
    try:
        msg = bot.reply_to(message, "🔄 Обновляю список с сайта swgoh.gg. Это займет некоторое время...")
        guild_bot.initialize_from_website()
        
        if guild_bot.list_message_id and guild_bot.chat_id:
            try:
                new_list_text = guild_bot.format_player_list()
                bot.edit_message_text(new_list_text, guild_bot.chat_id, guild_bot.list_message_id)
                success_msg = "✅ Список обновлен. Таков путь."
                bot.edit_message_text(success_msg, message.chat.id, msg.message_id)
            except Exception as e:
                print(f"Ошибка обновления списка: {e}")
                success_msg = "✅ Список обновлен. Используй /list чтобы увидеть."
                bot.edit_message_text(success_msg, message.chat.id, msg.message_id)
        else:
            success_msg = "✅ Список обновлен. Используй /list чтобы увидеть."
            bot.edit_message_text(success_msg, message.chat.id, msg.message_id)
    except Exception as e:
        print(f"Ошибка в /update: {e}")
        error_msg = f"❌ Ошибка при обновлении: {str(e)[:100]}"
        bot.reply_to(message, error_msg)

@bot.message_handler(commands=['add'])
def add_player_command(message: Message):
    """Добавляет игрока через команду /add"""
    try:
        text = message.text[4:].strip()
        pattern = r'^(.+?)\s*[-–—]\s*(@.+)$'
        match = re.match(pattern, text)
        
        if match:
            game_nick = match.group(1).strip()
            tg_nick = match.group(2).strip()
            
            if guild_bot.add_player(game_nick, tg_nick):
                if guild_bot.list_message_id and guild_bot.chat_id:
                    try:
                        new_list_text = guild_bot.format_player_list()
                        bot.edit_message_text(
                            new_list_text,
                            guild_bot.chat_id,
                            guild_bot.list_message_id
                        )
                    except Exception as e:
                        print(f"Ошибка обновления списка после add: {e}")
                
                success_msg = f"✅ Воин {game_nick} добавлен в список. {guild_bot.get_mandalorian_phrase()}"
                bot.reply_to(message, success_msg)
                
                # Отправляем уведомление в канал только если сообщение пришло из канала
                if message.chat.id == CHANNEL_CHAT_ID:
                    bot.send_message(
                        chat_id=CHANNEL_CHAT_ID,
                        text=f"➕ {game_nick} присоединился к гильдии! {guild_bot.get_mandalorian_phrase()}",
                        message_thread_id=message.message_thread_id
                    )
            else:
                bot.reply_to(message, "❌ Ошибка при добавлении воина.")
        else:
            bot.reply_to(message, "❌ Неверный формат. Используй: /add Ник в игре - @ник_в_телеграм")
    except Exception as e:
        print(f"Ошибка в /add: {e}")
        bot.reply_to(message, f"❌ Ошибка: {str(e)[:100]}")

@bot.message_handler(commands=['remove'])
def remove_player_command(message: Message):
    """Удаляет игрока через команду /remove"""
    if not can_change_roles(message):
        reply = f"Ты не достоин этой команды, воин. {guild_bot.get_mandalorian_phrase()}"
        bot.reply_to(message, reply)
        return
    
    try:
        game_nick = message.text[7:].strip()
        
        if not game_nick:
            bot.reply_to(message, "❌ Использование: /remove Ник в игре")
            return
        
        if guild_bot.remove_player(game_nick):
            if guild_bot.list_message_id and guild_bot.chat_id:
                try:
                    new_list_text = guild_bot.format_player_list()
                    bot.edit_message_text(
                        new_list_text,
                        guild_bot.chat_id,
                        guild_bot.list_message_id
                    )
                except Exception as e:
                    print(f"Ошибка обновления списка после remove: {e}")
            
            success_msg = f"✅ Воин {game_nick} удален из списка. {guild_bot.get_mandalorian_phrase()}"
            bot.reply_to(message, success_msg)
            
            # Отправляем уведомление в канал только если сообщение пришло из канала
            if message.chat.id == CHANNEL_CHAT_ID:
                bot.send_message(
                    chat_id=CHANNEL_CHAT_ID,
                    text=f"➖ {game_nick} покинул гильдию. {guild_bot.get_mandalorian_phrase()}",
                    message_thread_id=message.message_thread_id
                )
        else:
            bot.reply_to(message, f"❌ Воин {game_nick} не найден в списке.")
            
    except Exception as e:
        print(f"Ошибка в /remove: {e}")
        bot.reply_to(message, f"❌ Ошибка: {str(e)[:100]}")

@bot.message_handler(commands=['role'])
def change_role_command(message: Message):
    """Изменяет роль игрока - исправленная версия для имен с пробелами"""
    if not can_change_roles(message):
        reply = f"Ты не достоин этой команды, воин. {guild_bot.get_mandalorian_phrase()}"
        bot.reply_to(message, reply)
        return
    
    try:
        # Получаем текст после команды /role
        text = message.text[5:].strip()
        
        # Ищем последнее слово в сообщении - это будет роль
        words = text.split()
        if len(words) < 2:
            bot.reply_to(message, f"❌ Использование: /role Ник в игре Роль\nДоступные роли: {', '.join(ROLES)}")
            return
        
        # Последнее слово - это роль
        possible_role = words[-1]
        # Все что до последнего слова - это имя игрока (может содержать пробелы)
        game_nick = ' '.join(words[:-1])
        
        print(f"Распознано: game_nick='{game_nick}', possible_role='{possible_role}'")
        
        # Нормализуем роль - ищем совпадение без учета регистра
        normalized_role = None
        for role in ROLES:
            if role.lower() == possible_role.lower():
                normalized_role = role
                break
        
        if not normalized_role:
            bot.reply_to(message, f"❌ Неверная роль. Доступные роли: {', '.join(ROLES)}")
            return
        
        user_identifier = f"@{message.from_user.username}" if message.from_user.username else "unknown"
        success, result_message = guild_bot.change_role(game_nick, normalized_role, user_identifier)
        
        if success and guild_bot.list_message_id and guild_bot.chat_id:
            try:
                new_list_text = guild_bot.format_player_list()
                bot.edit_message_text(
                    new_list_text,
                    guild_bot.chat_id,
                    guild_bot.list_message_id
                )
            except Exception as e:
                print(f"Ошибка обновления списка после role: {e}")
        
        bot.reply_to(message, result_message)
        
        # Отправляем уведомление в канал только если сообщение пришло из канала
        if message.chat.id == CHANNEL_CHAT_ID:
            bot.send_message(
                chat_id=CHANNEL_CHAT_ID,
                text=f"🔄 {game_nick} теперь {normalized_role}! {guild_bot.get_mandalorian_phrase()}",
                message_thread_id=message.message_thread_id
            )
            
    except Exception as e:
        print(f"Ошибка в /role: {e}")
        bot.reply_to(message, f"❌ Ошибка: {str(e)[:100]}")

@bot.message_handler(commands=['fixroles'])
def fix_roles_command(message: Message):
    """Исправляет роли - заменяет 'Лидер' на 'Манд'алор' (только для админа)"""
    if not can_change_roles(message):
        bot.reply_to(message, f"Ты не достоин этой команды, воин. {guild_bot.get_mandalorian_phrase()}")
        return
    
    try:
        count = guild_bot.fix_roles()
        
        if count > 0:
            # Обновляем список
            if guild_bot.list_message_id and guild_bot.chat_id:
                try:
                    bot.edit_message_text(
                        guild_bot.format_player_list(),
                        guild_bot.chat_id,
                        guild_bot.list_message_id
                    )
                except Exception as e:
                    print(f"Ошибка обновления списка: {e}")
            
            bot.reply_to(message, f"✅ Исправлено {count} ролей. Теперь Манд'алор будет первым! {guild_bot.get_mandalorian_phrase()}")
            
            # Отправляем уведомление в канал только если сообщение пришло из канала
            if message.chat.id == CHANNEL_CHAT_ID:
                bot.send_message(
                    chat_id=CHANNEL_CHAT_ID,
                    text=f"🛠 Манд'алор исправил роли гильдии. {guild_bot.get_mandalorian_phrase()}",
                    message_thread_id=message.message_thread_id
                )
        else:
            bot.reply_to(message, "❌ Роль 'Лидер' не найдена.")
            
    except Exception as e:
        print(f"Ошибка в /fixroles: {e}")
        bot.reply_to(message, f"❌ Ошибка: {str(e)[:100]}")

@bot.message_handler(func=lambda message: True)
def handle_player_add(message: Message):
    """Обрабатывает добавление игрока в свободном формате"""
    if message.text.startswith('/'):
        return
    
    try:
        text = message.text.strip()
        pattern = r'^(.+?)\s*[-–—]\s*(@.+)$'
        match = re.match(pattern, text)
        
        if match:
            game_nick = match.group(1).strip()
            tg_nick = match.group(2).strip()
            
            if guild_bot.add_player(game_nick, tg_nick):
                if guild_bot.list_message_id and guild_bot.chat_id:
                    try:
                        new_list_text = guild_bot.format_player_list()
                        bot.edit_message_text(
                            new_list_text,
                            guild_bot.chat_id,
                            guild_bot.list_message_id
                        )
                        reply_msg = f"✅ Воин {game_nick} добавлен в список. {guild_bot.get_mandalorian_phrase()}"
                        bot.reply_to(message, reply_msg)
                        
                        # Отправляем уведомление в канал только если сообщение пришло из канала
                        if message.chat.id == CHANNEL_CHAT_ID:
                            bot.send_message(
                                chat_id=CHANNEL_CHAT_ID,
                                text=f"➕ {game_nick} присоединился к гильдии! {guild_bot.get_mandalorian_phrase()}",
                                message_thread_id=message.message_thread_id
                            )
                    except Exception as e:
                        print(f"Ошибка обновления списка: {e}")
                        bot.reply_to(message, f"✅ Воин добавлен. Используй /list чтобы увидеть список.")
                else:
                    bot.reply_to(message, f"✅ Воин добавлен. Используй /list чтобы увидеть список.")
    except Exception as e:
        print(f"Ошибка в handle_player_add: {e}")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call: CallbackQuery):
    """Обработчик callback запросов от инлайн кнопок"""
    try:
        username = call.from_user.username if call.from_user.username else "unknown"
        
        if call.data == "update_from_site":
            # Проверяем права
            has_rights = False
            
            if username and username.lower() == ADMIN_USERNAME.lower().replace('@', ''):
                has_rights = True
            
            if not has_rights and username:
                user_tg_nick = f"@{username}"
                for player_info in guild_bot.players.values():
                    if player_info.get("tg_nick") and player_info["tg_nick"].lower() == user_tg_nick.lower():
                        if player_info["role"] in ["Манд'алор", "Офицер"]:
                            has_rights = True
                            break
            
            if has_rights:
                bot.answer_callback_query(call.id, "Обновляю список с сайта...")
                guild_bot.initialize_from_website()
                try:
                    new_list_text = guild_bot.format_player_list()
                    bot.edit_message_text(
                        new_list_text,
                        call.message.chat.id,
                        call.message.message_id
                    )
                    bot.send_message(call.message.chat.id, "✅ Список обновлен с сайта. Таков путь.")
                except Exception as e:
                    print(f"Ошибка обновления: {e}")
                    bot.answer_callback_query(call.id, "Ошибка при обновлении", show_alert=True)
            else:
                bot.answer_callback_query(call.id, "Ты не достоин этой команды!", show_alert=True)
        
        elif call.data == "save_list":
            guild_bot.save_message_info(call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id, "✅ Этот список теперь будет автоматически обновляться!")
            
    except Exception as e:
        print(f"Ошибка в callback_handler: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка", show_alert=True)

if __name__ == "__main__":
    print("="*60)
    print("🛡 Бот Mandalorians Kryze запущен. Таков путь.")
    print(f"👑 Манд'алор бота: @{ADMIN_USERNAME}")
    print(f"📊 Текущих игроков в памяти: {len(guild_bot.players)}")
    print(f"📢 Канал для авто-постинга: {CHANNEL_CHAT_ID}")
    if guild_bot.players:
        print("📋 Первые 5 игроков:")
        for i, (name, info) in enumerate(list(guild_bot.players.items())[:5]):
            print(f"   {i+1}. {name} - {info['role']} - {info['tg_nick'] or 'нет TG'}")
    print("="*60)
    
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            time.sleep(5)
