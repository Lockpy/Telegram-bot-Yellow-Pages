import sqlite3
import telebot
import os.path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
stock_path = os.path.join(BASE_DIR, "bcbot.db")
au_path = os.path.join(BASE_DIR, "bcadmin.db")

def get_state(database_name,user_id):
    if database_name == 'bcbot.db':
        connect = sqlite3.connect(database_name)
    if database_name == 'bcadmin.db':
        connect = sqlite3.connect(au_path)
    connect.row_factory = lambda cursor, row: row[0]
    c = connect.cursor()
    c.execute('SELECT user_id FROM users')
    users = c.fetchall()
    for user in users:
        if (str(user) == str(user_id)):
            c.execute("SELECT state FROM users WHERE user_id = '"+str(user)+"'")
            return c.fetchone()
def in_table(database_name,table_name,field,obj):
    if database_name == 'bcbot.db':
        connect = sqlite3.connect(database_name)
    if database_name == 'bcadmin.db':
        connect = sqlite3.connect(au_path)
    connect.row_factory = lambda cursor, row: row[0]
    c = connect.cursor()
    c.execute('SELECT '+field+' FROM '+table_name)
    objs = c.fetchall()
    for item in objs:
        if(str(item) == str(obj)):
            return True
    return False

def get_channel_list(user_id):
        connect = sqlite3.connect(au_path)
        connect.row_factory = lambda cursor, row: row[0]
        c = connect.cursor()
        c.execute("SELECT channel_name FROM channels where user_id = '" + str(user_id) + "'")
        result = []
        for item in c.fetchall():
            result.append(str(item))
        return result
def get_channel_list_string(user_id):
    list = get_channel_list(user_id)
    text = "Ваш список каналов:\n"
    i = 1
    for item in list:
        text += str(i) + "." + item + "\n"
        i += 1
    if len(list) == 0:
        text = "Ваш список каналов пуст."
    return  text
def get_list_keybard(user_id):
    reply_keyboard_del = telebot.types.ReplyKeyboardMarkup()
    list = get_channel_list(user_id)
    for item in list:
        reply_keyboard_del.row(telebot.types.KeyboardButton(item))
    reply_keyboard_del.row(telebot.types.KeyboardButton("❌ Отмена"))
    reply_keyboard_del.resize_keyboard = True
    return reply_keyboard_del
def set_state(database_name,state,user_id):
    if database_name == 'bcbot.db':
        connect = sqlite3.connect(database_name)
    if database_name == 'bcadmin.db':
        connect = sqlite3.connect(au_path)
    connect.row_factory = lambda cursor, row: row[0]
    c = connect.cursor()
    c.execute('SELECT user_id FROM users')
    users = c.fetchall()
    for user in users:
        if (str(user) == str(user_id)):
            c.execute("UPDATE users SET state = "+str(state.value)+" WHERE user_id = '" +str(user_id)+"'")
            connect.commit()
def set_state_admin(database_name,state,user_id):
    if database_name == 'bcbot.db':
        connect = sqlite3.connect(database_name)
    if database_name == 'bcadmin.db':
        connect = sqlite3.connect(au_path)
    connect.row_factory = lambda cursor, row: row[0]
    c = connect.cursor()
    c.execute('SELECT user_id FROM users')
    users = c.fetchall()
    for user in users:
        if (str(user) == str(user_id)):
            c.execute("UPDATE users SET state = "+str(state.value)+" WHERE user_id = '" +str(user_id)+"'")
            connect.commit()