
import telebot
import config
import tgbotlib
import sqlite3
import time
import os.path
from datetime import datetime
from enum import Enum
import traceback
import cherrypy
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR,"bcbot.db")
ADMIN_PATH = os.path.join(BASE_DIR,"bcadmin.db")

WEBHOOK_HOST = '80.211.14.184'              #IP сервера на котором расположен бот
WEBHOOK_PORT = 88                           # 443, 80, 88 или 8443 (порт должен быть открыт!)
WEBHOOK_LISTEN = '80.211.14.184'            #IP сервера на котором расположен бот
WEBHOOK_SSL_CERT = './webhook_cert.pem'     # Путь к сертификату
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'     # Путь к приватному ключу
WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (config.token_admin)

bot = telebot.TeleBot(config.token_admin)
bot.delete_webhook()
now = datetime.now()

class WebhookServer(object):                           #Класс реализующий экземпляр веб-сервера
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                        'content-type' in cherrypy.request.headers and \
                        cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            # Эта функция обеспечивает проверку входящего сообщения
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)

class State(Enum):
    home=0
    admin = 1
    admin_name = 2
    edit = 3
    PR=4
    text = 5

print("[{}:{}:{}]Start for {}".format(now.hour,now.minute,now.second,bot.get_me().username))
def new_rec(user):
    connect = sqlite3.connect(DB_PATH)
    c = connect.cursor()
    if get_status(user) == 1:
        c.execute("SELECT * FROM contacts WHERE mod = 0")
    else:
        connectAdm = sqlite3.connect(ADMIN_PATH)
        cADm = connectAdm.cursor()
        c.execute("SELECT * FROM contacts WHERE mod = 0 AND region_id = {}".format(cADm.execute("SELECT region FROM users WHERE user_id = {}".format(user.id)).fetchone()[0]))
    return len(c.fetchall())
back = telebot.types.ReplyKeyboardMarkup()
back.row(telebot.types.KeyboardButton("Назад"))
back.resize_keyboard = True
@bot.channel_post_handler(func=lambda message: check(message.chat.username))
def comment_alert(message):
    try:
        reg_id = int(message.text)
        connect = sqlite3.connect(ADMIN_PATH)
        c = connect.cursor()
        c.execute("SELECT * FROM users WHERE status = 1 OR region = {}".format(reg_id))
        for admin in c.fetchall():
            try:
                bot.send_message(admin[0],"Появился новый запрос!")
            except Exception as e:
                print(e)
    except Exception as e:
        print("Post handler: {}".format(e))
def check(name):
    if "bcalert" in name:
            return True
    return False
class user:
    id = 0
    username = ""
    def __init__(self, id, name):
        self.id = id
        self.username = name
    def getId(self):
        return user.id
    def getName(self):
        return user.username
def getEdit(user):
    return
reg_id_pr = 77
@bot.message_handler(content_types='[text]')
def handl_msg(message):
    try:
        if not tgbotlib.in_table("bcadmin.db","users","user_id",message.from_user.id):
            if tgbotlib.in_table("bcadmin.db","users","username",message.from_user.username):
                connect = sqlite3.connect(ADMIN_PATH)
                c = connect.cursor()
                c.execute("UPDATE users SET user_id = {} WHERE username = '{}'".format(message.from_user.id,message.from_user.username))
                connect.commit()
                return
            else:
                connect = sqlite3.connect(ADMIN_PATH)
                c = connect.cursor()
                c.execute("INSERT INTO users(user_id,username,state,status,region) VALUES({},'{}',0,0,0)".format(message.from_user.id,message.from_user.username))
                connect.commit()
                ad = telebot.types.ReplyKeyboardMarkup()
                ad.row(telebot.types.KeyboardButton("Реклама"))
                ad.resize_keyboard=True
                bot.send_message(message.from_user.id,"Приветствую в админ панели бизнес контактов!Тебе доступен только раздел рекламы!",reply_markup=ad)
                return
        if "/start" in message.text or "Назад" in message.text:
            print("username: {}\nstatus: {}".format(message.from_user.username,get_status(message.from_user)))
            if get_status(message.from_user) != 0:
                home = telebot.types.ReplyKeyboardMarkup()
                home.row(telebot.types.KeyboardButton("Назначить модератора"), telebot.types.KeyboardButton("Редактировать БД"))
                home.row(telebot.types.KeyboardButton("Новые записи {}".format(new_rec(message.from_user))),
                         telebot.types.KeyboardButton("Админы"))
                home.row(telebot.types.KeyboardButton("Реклама"))
                home.resize_keyboard = True
                bot.send_message(message.from_user.id,"Приветсвую в админ-панели Бизнесс Контактов!",reply_markup=home)
                tgbotlib.set_state("bcadmin.db",State.home,message.from_user.id)
            else:
                ad = telebot.types.ReplyKeyboardMarkup()
                ad.row(telebot.types.KeyboardButton("Реклама"))
                ad.resize_keyboard = True
                bot.send_message(message.from_user.id,"Приветствую в админ панели бизнес контактов!Тебе доступен только раздел рекаламы!",reply_markup=ad)
        if message.text == "Реклама":
            if get_status(message.from_user) != 1:
                bot.send_message(message.from_user.id,"Посмотреть рекламу в регионе:",reply_markup=region_markup(message.from_user))
                tgbotlib.set_state('bcadmin.db',State.PR,message.from_user.id)
                return
            connect = sqlite3.connect(DB_PATH)
            c = connect.cursor()
            c.execute("SELECT * FROM region")
            regions = c.fetchall()
            PRkb= telebot.types.InlineKeyboardMarkup()
            for region in regions:
                PRkb.row(telebot.types.InlineKeyboardButton(region[1],callback_data="setPr={}".format(region[0])))
            bot.send_message(message.from_user.id,"Установить рекламный текст в регионе:",reply_markup=PRkb)
            return
            PRkb= telebot.types.InlineKeyboardMarkup()
            PRkb.row(telebot.types.InlineKeyboardButton("Моя реклама",callback_data="prlist={}".format(message.from_user.id)))
            PRkb.row(telebot.types.InlineKeyboardButton("Купить рекламу",callback_data="prbuy={}".format(message.from_user.id)))
            bot.send_message(message.from_user.id,"Реклама",reply_markup=PRkb)
        if tgbotlib.get_state('bcadmin.db',message.from_user.id) == State.text.value:
            connect = sqlite3.connect(ADMIN_PATH)
            c = connect.cursor()
            c.execute("INSERT INTO pr(reg_id,text,views) VALUES({},'{}',0)".format(reg_id_pr,message.text))
            connect.commit()
            tgbotlib.set_state('bcadmin.db',State.home,message.from_user.id)
            home = telebot.types.ReplyKeyboardMarkup()
            home.row(telebot.types.KeyboardButton("Назначить модератора"), telebot.types.KeyboardButton("Редактировать БД"))
            home.row(telebot.types.KeyboardButton("Новые записи {}".format(new_rec(message.from_user))),
                     telebot.types.KeyboardButton("Админы"))
            home.row(telebot.types.KeyboardButton("Реклама"))
            home.resize_keyboard = True
            bot.send_message(message.from_user.id,"Рекламный текст установлен!",reply_markup=home)
            return
        if message.text == 'Админы':
            connect = sqlite3.connect(ADMIN_PATH)
            c = connect.cursor()
            c.execute("SELECT * FROM users")
            admins = c.fetchall()
            for admin in admins:
                if admin[2] == 0:
                    continue
                if 'None' in str(admin[0]):
                    delBut = telebot.types.InlineKeyboardMarkup()
                    delBut.row(telebot.types.InlineKeyboardButton("Удалить из админов",
                                                                  callback_data="ban={}".format(admin[1])))
                    bot.send_message(message.from_user.id,
                                     "Username: @{}\nРегион: *{}*\nСтатус: *{}*".format(admin[1],admin[4],admin[2]),
                                     reply_markup=delBut, parse_mode='Markdown')
                    continue
                delBut = telebot.types.InlineKeyboardMarkup()
                delBut.row(telebot.types.InlineKeyboardButton("Удалить из админов",callback_data="ban={}".format(admin[0])))
                if admin[2] == 1:
                    bot.send_message(message.from_user.id,"Username: [{}](tg://user?id={})\nСтатус: *{}*\n".format(admin[1],admin[0],admin[2]),parse_mode='Markdown')
                else:
                    if admin[4] == 777:
                        bot.send_message(message.from_user.id,
                                         "Username: [{}](tg://user?id={})\nСтатус: *{}*\n".format(admin[1], admin[0],
                                                                                                  admin[2]),
                                         parse_mode='Markdown',reply_markup=delBut)
                    else:
                        bot.send_message(message.from_user.id, "Username: [{}](tg://user?id={})\nРегион: *{}*\nСтатус: *{}*".format(admin[1],admin[0],admin[4],admin[2]),reply_markup=delBut,parse_mode='Markdown')
            home = telebot.types.ReplyKeyboardMarkup()
            home.row(telebot.types.KeyboardButton("Назначить модератора"), telebot.types.KeyboardButton("Редактировать БД"))
            home.row(telebot.types.KeyboardButton("Новые записи {}".format(new_rec(message.from_user))),
                     telebot.types.KeyboardButton("Админы"))
            home.row(telebot.types.KeyboardButton("Реклама"))
            home.resize_keyboard = True
            bot.send_message(message.from_user.id,"Статусы\n1 - Главный Админ\n2 - Локальный Админ\n3 - Рекламодатель",reply_markup=home)
        if message.text == 'Назначить модератора':
            bot.send_message(message.chat.id,"Выберите регион администратора:",reply_markup=region_markup(message.from_user))
            tgbotlib.set_state("bcadmin.db",State.admin,message.from_user.id)
            return
        if message.text == 'Редактировать БД':
            if get_status(message.from_user) == 1:
                bot.send_message(message.chat.id, "Выбирите регион", reply_markup=region_edit_markup(message.from_user))
                tgbotlib.set_state("bcadmin.db", State.edit, message.from_user.id)
                return
            connect = sqlite3.connect(ADMIN_PATH)
            c = connect.cursor()
            c.execute("SELECT region FROM users WHERE user_id = {}".format(message.from_user.id))
            reg_id = c.fetchone()[0]
            print("reg_id = {}".format(reg_id))
            connect = sqlite3.connect(DB_PATH)
            c = connect.cursor()
            c.execute("SELECT * FROM contacts WHERE region_id = {}".format(reg_id))
            contacts = c.fetchall()
            if len(contacts)<1:
                bot.send_message(message.from_user.id,"В вашем регионе нет контактов!")
                return
            getContacts(contacts,message.from_user.id)
            return
        if "Новые записи" in message.text:
            try:
                if get_status(message.from_user) == 1 or get_status(message.from_user) == 2:
                    connect = sqlite3.connect(DB_PATH)
                    c = connect.cursor()
                    if get_status(message.from_user) == 1:
                        c.execute("SELECT * FROM contacts WHERE mod = 0")
                        contacts = c.fetchall()
                    else:
                        print("{} ne admin".format(message.from_user.username))
                        connectADM = sqlite3.connect(ADMIN_PATH)
                        cADM = connectADM.cursor()
                        cADM.execute("SELECT region FROM users WHERE user_id = {}".format(message.from_user.id))
                        region_id = int(cADM.fetchone()[0])
                        c.execute("SELECT * FROM contacts WHERE mod = 0 AND region_id = {}".format(region_id))
                        contacts = c.fetchall()
                    if len(contacts) == 0:
                        home = telebot.types.ReplyKeyboardMarkup()
                        home.row(telebot.types.KeyboardButton("Назначить модератора"), telebot.types.KeyboardButton("Редактировать БД"))
                        home.row(telebot.types.KeyboardButton("Новые записи {}".format(new_rec(message.from_user))),
                                 telebot.types.KeyboardButton("Админы"))
                        home.row(telebot.types.KeyboardButton("Реклама"))
                        home.resize_keyboard = True
                        bot.send_message(message.from_user.id,"В вашем регионе нет контактов не прошедших модерацию!",reply_markup=home)
                else:
                    bot.send_message(message.from_user.id,"У вас нет доступа к модерации данных!")
            except Exception as e:
                print("first part: " + str(e))
            try:
                for contact in contacts:
                    c.execute("SELECT section_name FROM section WHERE section_id = {}".format(contact[3]))
                    section_name = c.fetchone()[0]
                    c.execute("SELECT head_name FROM head WHERE head_id = {} AND section_id = {}".format(contact[4],contact[3]))
                    head_name = c.fetchone()[0]
                    mod_mark = telebot.types.InlineKeyboardMarkup()
                    mod_mark.row(telebot.types.InlineKeyboardButton("Принять", callback_data="mod={}".format(contact[0]))
                    ,telebot.types.InlineKeyboardButton("Отклонить", callback_data="del={}".format(contact[0])))
                    bot.send_message(message.from_user.id,
                                     "Имя: {}\nТелеграм: {}\nРубрика: {}\nРаздел: {}\nОписание: {}\nТелефон: {}\nСайт: {}".format(
                                         contact[2], contact[1], section_name, head_name, contact[5], contact[6], contact[7]),
                                     reply_markup=mod_mark)
            except Exception as e:
                print("second part: " + str(e))
            if get_status(message.from_user) == 1:
                c.execute("SELECT region_id FROM contacts WHERE mod = 0 ")
                regions = c.fetchall()
                fools = []
                region_name = []
                for region in regions:
                    i = 0;
                    equal = False
                    for fool in fools:
                        if len(fools) == 0:
                            equal = True
                            fool = region[0]
                            region_name[i] = c.execute(
                                "SELECT region_name FROM region WHERE region_id = {}".format(region[0])).fetchone()[0]
                        if fool == region:
                            equal = True
                        i += 1
                    if not equal:
                        fools.append(region[0])
                        region_name.append(c.execute(
                            "SELECT region_name FROM region WHERE region_id = {}".format(region[0])).fetchone()[0])
                result = "Статистика модераторов по регионам(кол-во непроверенных записей):\n"
                for key, val in Counter(region_name).items():
                    result += "_{}_ - *{}*\n".format(key, val)
                bot.send_message(message.from_user.id, result, parse_mode='Markdown')
            return
        if tgbotlib.get_state("bcadmin.db", message.from_user.id) == State.admin_name.value:
            try:
                if get_status(message.from_user)==1:
                    connect = sqlite3.connect(ADMIN_PATH)
                    c = connect.cursor()
                    c.execute("SELECT region FROM users WHERE user_id = {}".format(message.from_user.id))
                    reg_id = int(c.fetchone()[0])
                    print("REGION {}".format(reg_id))
                    username = message.text[1:]
                    if 'None' in str(username):
                        if reg_id == 777:
                            c.execute("INSERT INTO users(username,status,state,region)"
                                      "VALUES ('{}',3,0,{})".format(message.text[1:], reg_id))
                        else:
                            c.execute("INSERT INTO users(username,status,state,region)"
                                      "VALUES ('{}',2,0,{})".format(message.text[1:], reg_id))
                    else:
                        if reg_id == 777:
                            c.execute("UPDATE users SET status = 3 , region = {} WHERE username = '{}'".format(reg_id,username))
                        else:
                            c.execute("UPDATE users SET status = 2 , region = {} WHERE username = '{}'".format(reg_id,username))

                    connect.commit()
                    home = telebot.types.ReplyKeyboardMarkup()
                    home.row(telebot.types.KeyboardButton("Назначить модератора"), telebot.types.KeyboardButton("Редактировать БД"))
                    home.row(telebot.types.KeyboardButton("Новые записи {}".format(new_rec(message.from_user))),
                             telebot.types.KeyboardButton("Админы"))
                    home.row(telebot.types.KeyboardButton("Реклама"))
                    home.resize_keyboard = True
                    bot.send_message(message.from_user.id,"Вы успешно добавили {} в админы".format(message.text),reply_markup=home)
                    tgbotlib.set_state("bcadmin.db", State.home, message.from_user.id)
            except Exception as e:
                print(traceback.format_exc())
                print(str(e))
                bot.send_message(message.from_user.id,"Ошибка ввода(ник админа вводить с '@')")
            return
    except Exception as e:
        print("Message handler exception: {}".format(e))
def region_edit_markup(user):
    connect = sqlite3.connect(DB_PATH)
    c = connect.cursor()
    connectAdm = sqlite3.connect(ADMIN_PATH)
    cAdm = connectAdm.cursor()
    if get_status(user) == 1:
        c.execute("SELECT * FROM region")
    else:
        try:
            c.execute("SELECT * FROM region WHERE region_id = {}".format(
                cAdm.execute("SELECT region FROM users WHERE user_id = {}".format(user.id)).fetchone()[0]))
        except Exception as e:
            print(e)
    result = telebot.types.InlineKeyboardMarkup()
    regions = c.fetchall()
    for region in regions:
        result.row(telebot.types.InlineKeyboardButton(region[1], callback_data="edit={}".format(region[0])))
    return result
def region_markup(user):
    connect = sqlite3.connect(DB_PATH)
    c = connect.cursor()
    connectAdm = sqlite3.connect(ADMIN_PATH)
    cAdm = connectAdm.cursor()
    if tgbotlib.get_state('bcadmin.db',user.id) == State.PR.value:
        print("PR state")
        c.execute("SELECT * FROM region")
        result = telebot.types.InlineKeyboardMarkup()
        regions = c.fetchall()
        for region in regions:
            result.row(telebot.types.InlineKeyboardButton(region[1], callback_data="pReg={}".format(region[0])))
        tgbotlib.set_state('bcadmin.db',State.home,user.id)
        return result
    if get_status(user) == 1:
        c.execute("SELECT * FROM region")
    else:
        try:
            c.execute("SELECT * FROM region WHERE region_id = {}".format(cAdm.execute("SELECT region FROM users WHERE user_id = {}".format(user.id)).fetchone()[0]))
        except Exception as e:
            print(e)
    result = telebot.types.InlineKeyboardMarkup()
    regions = c.fetchall()
    for region in regions:
        result.row(telebot.types.InlineKeyboardButton(region[1],callback_data="reg={}".format(region[0])))
    result.row(telebot.types.InlineKeyboardButton("Рекламодатель",callback_data="reg=777"))
    return result
def city_markup(reg_id):
    connect = sqlite3.connect(DB_PATH)
    c = connect.cursor()
    c.execute("SELECT * FROM city WHERE region_id={}".format(reg_id))
    result = telebot.types.InlineKeyboardMarkup()
    cityes = c.fetchall()
    for city in cityes:
        result.row(telebot.types.InlineKeyboardButton(city[2],callback_data="city={};{}".format(city[0],reg_id)))
    return result
def get_status(user):
    try:
        username = user.username[user.username.find("@")+1:]
        user_id = user.id
        connect = sqlite3.connect(ADMIN_PATH)
        c = connect.cursor()
        c.execute("SELECT status FROM users WHERE user_id = {}".format(user_id))
        result = c.fetchone()[0]
        if 'None' in str(result):
            c.execute("SELECT status FROM users WHERE username = {}".format(username))
            usernameResult = c.fetchone()[0]
            if 'None' in str(usernameResult):
                return "None"
            return usernameResult
        return result
    except Exception as e:
        print(e)
@bot.callback_query_handler(func =lambda call:True)
def callback_handler(call):                                                     #Обработка нажатий Callback клавиатуры
    try:
        prbuykb = telebot.types.InlineKeyboardMarkup()
        prbuykb.row(
            telebot.types.InlineKeyboardButton("Купить рекламу", callback_data="prbuy={}".format(call.from_user.id)))
        print(call.data)
        if "setPr" in call.data:                                                #Вызов рекламного интерфейса по региону
            reg_id = call.data[6:]                                              #Парсим ID региона из CallBack
            connect = sqlite3.connect(ADMIN_PATH)
            c = connect.cursor()
            c.execute("SELECT * FROM pr WHERE reg_id = {}".format(reg_id))      #Парсим рекламу по региону
            global reg_id_pr
            reg_id_pr =reg_id
            pr = c.fetchone()
            if 'None' in str(pr):                                               #Рекламное место пустует
                bot.send_message(call.from_user.id,"Введите рекламный текст:")  #Установка рекламы
                tgbotlib.set_state('bcadmin.db',State.text,call.from_user.id)
                return
            else:                                                               #Рекламное место занято
                delPr = telebot.types.InlineKeyboardMarkup()
                delPr.row(telebot.types.InlineKeyboardButton("Удалить текст",callback_data="delPr={}".format(reg_id)))
                bot.send_message(call.from_user.id,"В выбранном регионе уже установлен текст: {}\nПросмотров: {}"
                                 .format(pr[1],pr[2]),reply_markup=delPr)       #Статистика рекламы + кнопка удаления рекламы
                return
        if "delPr" in call.data:
            reg_id = call.data[6:]
            connect = sqlite3.connect(ADMIN_PATH)
            c = connect.cursor()
            c.execute("SELECT * FROM pr WHERE reg_id = {}".format(reg_id))
            pr = c.fetchone()
            if 'None' in str(pr):
                bot.answer_callback_query(call.id,"Запись уже удаленна")
            else:
                c.execute("DELETE FROM pr WHERE reg_id = {}".format(reg_id_pr))
                connect.commit()
                setPr = telebot.types.InlineKeyboardMarkup()
                setPr.row(telebot.types.InlineKeyboardButton("Установить текст",callback_data="setPr={}".format(reg_id)))
                bot.send_message(call.from_user.id, "Текст удален!", reply_markup=setPr)
            return
        if "pReg" in call.data:
            reg_id = call.data[5:]
            connect = sqlite3.connect(ADMIN_PATH)
            c = connect.cursor()
            c.execute("SELECT views,text FROM pr WHERE reg_id = {}".format(reg_id))
            ads = c.fetchall()[0]
            if len(ads) == 0:
                bot.send_message(call.from_user.id,"В выбранном регионе нет рекламы!")
                return
            else:
                bot.send_message(call.from_user.id,"Текст: {}\nПросмотров: {}".format(ads[1],ads[0]))
            return
        if "price_set" in call.data:
            print(call.from_user.username)
            connect = sqlite3.connect(ADMIN_PATH)
            cAd = connect.cursor()
            user_id = call.data[10:]
            connect = sqlite3.connect(DB_PATH)
            c = connect.cursor()
            c.execute("SELECT * FROM region")
            regions = c.fetchall()
            regKB = telebot.types.InlineKeyboardMarkup()
            for region in regions:
                regKB.row(telebot.types.InlineKeyboardButton("Установить цену в {}".format(region[1]),callback_data="reg_price={}".format(region[0])))
                bot.send_message(call.from_user.id, "Установить цену в регионе:", reply_markup=regKB)
                regKB = telebot.types.InlineKeyboardMarkup()

            return
        if "reg_price" in call.data:
            reg_id = call.data[10:]
            connect = sqlite3.connect(DB_PATH)
            c = connect.cursor()
            c.execute("SELECT region_name FROM region WHERE region_id = {}".format(reg_id))
            bot.answer_callback_query(call.id,"Установка прайса в {} сейчас недоступна".format(c.fetchone()))
            return
        if "prbuy" in call.data:
            user_id = call.data[6:]
            connect = sqlite3.connect(ADMIN_PATH)
            c = connect.cursor()
            c.execute("SELECT region FROM users WHERE user_id = {}".format(user_id))
            c.execute("SELECT * FROM price WHERE region_id = {}".format(c.fetchone()[0]))
            pricelist = c.fetchall()
            for price in pricelist:
                reg_name = c.execute("SELECT region_name FROM region WHERE region_id = {}".format(price[0])).fetchone()
                reg_id = price[0]
                prbuykb = telebot.types.InlineKeyboardMarkup()
                prbuykb.row(telebot.types.InlineKeyboardButton("Купить в {} регионе".format(reg_name), callback_data=reg_id))
                bot.send_message(call.from_user.id,"Регион: {}\nЦена: {}\n".format(reg_name,reg_id))
            if len(pricelist)==0:
                bot.answer_callback_query(call.id,"Прайс не установлен!")
                if get_status(call.from_user) == 1:
                    price_set=telebot.types.InlineKeyboardMarkup()
                    price_set.row(telebot.types.InlineKeyboardButton("Установить прайс",callback_data="price_set"))
                    bot.send_message(call.from_user.id,"Редактировать прайс",reply_markup=price_set)
            return
        if "prlist" in call.data:

            home = telebot.types.ReplyKeyboardMarkup()
            home.row(telebot.types.KeyboardButton("Назначить модератора"), telebot.types.KeyboardButton("Редактировать БД"))
            home.row(telebot.types.KeyboardButton("Новые записи {}".format(new_rec(call.from_user))),
                     telebot.types.KeyboardButton("Админы"))
            home.row(telebot.types.KeyboardButton("Реклама"))
            home.resize_keyboard = True
            connect = sqlite3.connect(ADMIN_PATH)
            c = connect.cursor()
            c.execute("SELECT * FROM ad WHERE ad_user = {}".format(call.from_user.id))
            ads = c.fetchall()
            if len(ads)==0:

                bot.send_message(call.from_user.id,"У вас нет активной реакламы.",reply_markup=prbuykb)
            for ad in ads:
                bot.send_message(call.id,"Ид: {}\nКонтент: {}\nРегион: {}\nКоличество показов: {}\nЦена: {}\nДата публикации: {}\nДата удаления: {}".format(ad[0],ad[1]),reply_markup=home)
            return
        if "del" in call.data:
            contact_id = call.data[4:]
            connect = sqlite3.connect(DB_PATH)
            c = connect.cursor()
            c.execute("DELETE FROM contacts WHERE contact_id={}".format(contact_id))
            connect.commit()
            bot.answer_callback_query(call.id, "Контакт удален!")
            return
        if "mod" in call.data:
            contact_id = call.data[4:]
            connect = sqlite3.connect(DB_PATH)
            c = connect.cursor()
            c.execute("UPDATE contacts SET mod = 1 WHERE contact_id = {}".format(contact_id))
            connect.commit()
            bot.answer_callback_query(call.id, "Контакт добавлен в базу!")
            return
        if get_status(call.from_user) == 1:
                if "ban" in call.data:
                    id = call.data[4:]
                    connect = sqlite3.connect(ADMIN_PATH)
                    c = connect.cursor()
                    if id.isdigit():
                        c.execute("DELETE FROM users WHERE user_id={}".format(id))
                    else:
                        c.execute("DELETE FROM users WHERE username = '{}'".format(id))
                    connect.commit()
                    bot.answer_callback_query(call.id,"Админ удален!")
                if "edit" in call.data:
                    reg_id = int(call.data[5:])
                    bot.send_message(call.from_user.id, "Выбирите город:", reply_markup=city_markup(reg_id))
                    return
                if "reg" in call.data:
                        reg_id = int(call.data[4:])

                        if reg_id == 777:
                            mark = telebot.types.InlineKeyboardMarkup()
                            mark.row(telebot.types.InlineKeyboardButton("Назначить рекламодателя",
                                                                        callback_data="admin={}".format(reg_id)))
                            bot.send_message(call.from_user.id, "Вы выбрали рекламодатель", reply_markup=mark)
                            return
                        connect = sqlite3.connect(DB_PATH)
                        c  = connect.cursor()
                        c.execute("SELECT region_name FROM region WHERE region_id = {}".format(reg_id))
                        reg_name = c.fetchone()[0]
                        mark = telebot.types.InlineKeyboardMarkup()
                        mark.row(telebot.types.InlineKeyboardButton("Назначить модератора по {}".format(reg_name),callback_data="admin={}".format(reg_id)))
                        bot.answer_callback_query(call.id,"Pick")
                        bot.send_message(call.from_user.id,"Вы выбрали {}".format(reg_name),reply_markup=mark)
                        return

                if "city" in call.data:
                    city_id = call.data[5:call.data.find(";")]
                    reg_id = call.data[call.data.find(";")+1:]
                    connect = sqlite3.connect(DB_PATH)
                    c = connect.cursor()
                    c.execute("SELECT * FROM contacts WHERE city_id = {} AND region_id = {} AND mod = 1".format(city_id,reg_id))
                    getContacts(c.fetchall(),call.from_user.id)
                if "admin" in call.data:
                    reg_id = int(call.data[6:])
                    connect = sqlite3.connect(ADMIN_PATH)
                    c = connect.cursor()
                    c.execute("UPDATE users SET region = {} WHERE user_id = {}".format(reg_id,call.from_user.id))
                    connect.commit()
                    bot.send_message(call.from_user.id,"Введите @username админа:",reply_markup=back)
                    tgbotlib.set_state("bcadmin.db",State.admin_name,call.from_user.id)
    except Exception as e:
        print(e)

def getContacts(contacts,user_id):
    connect = sqlite3.connect(DB_PATH)
    c = connect.cursor()
    for contact in contacts:
        c.execute("SELECT section_name FROM section WHERE section_id = {}".format(contact[3]))
        section_name = c.fetchone()[0]
        c.execute("SELECT head_name FROM head WHERE head_id = {}".format(contact[4]))
        head_name = c.fetchone()[0]
        delBut = telebot.types.InlineKeyboardMarkup()
        delBut.row(telebot.types.InlineKeyboardButton("Удалить контакт",callback_data="del={}".format(contact[0])))
        bot.send_message(user_id,"Имя: {}\nТелеграм: {}\nРубрика: {}\nРаздел: {}\nОписание: {}\nТелефон: {}\nСайт: {}".format(contact[2],contact[1],section_name,head_name,contact[5],contact[6],contact[7]),reply_markup=delBut)
    home = telebot.types.ReplyKeyboardMarkup()
    home.row(telebot.types.KeyboardButton("Назначить модератора"), telebot.types.KeyboardButton("Редактировать БД"))
    home.row(telebot.types.KeyboardButton("Новые записи {}".format(new_rec(user(user_id,"noname")))),
             telebot.types.KeyboardButton("Админы"))
    home.row(telebot.types.KeyboardButton("Реклама"))
    home.resize_keyboard = True
    if get_status(user(user_id,"noname")) == 1:
        bot.send_message(user_id,"Добавить контакт можно в основном боте,посты администрации не модерируются!",reply_markup=home)
# try:
#      bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,certificate=open(WEBHOOK_SSL_CERT, 'r'))  #Устанавливаем вебхук
#      cherrypy.config.update({                                                                          # Указываем настройки сервера CherryPy
#          'server.socket_host': WEBHOOK_LISTEN,
#          'server.socket_port': WEBHOOK_PORT,
#          'server.ssl_module': 'builtin',
#          'server.ssl_certificate': WEBHOOK_SSL_CERT,
#          'server.ssl_private_key': WEBHOOK_SSL_PRIV
#      })
#      cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})                                  # Запускаем сервер CherryPy
# except Exception as e:
#      print("Webhook error: {}".format(e))                                                               #Обработка ошибок
bot.polling()