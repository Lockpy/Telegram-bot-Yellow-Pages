# -*- coding: utf-8 -*-
import telebot
import config
import tgbotlib
import sqlite3
import time
import os.path
from datetime import datetime
from enum import Enum
import cherrypy
from array import array

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR,"bcbot.db")
ADMIN_PATH = os.path.join(BASE_DIR,"bcadmin.db")
#Настройки сервера!!!
WEBHOOK_HOST = '80.211.14.184'
WEBHOOK_PORT = 80  # 443, 80, 88 или 8443 (порт должен быть открыт!)
WEBHOOK_LISTEN = '80.211.14.184'  # На некоторых серверах придется указывать такой же IP, что и выше
WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Путь к сертификату
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Путь к приватному ключу
WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (config.token)

class WebhookServer(object):
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
    home = 0
    region=1
    city=2
    section=3
    head =4
    menu=5
    add =6
    desc = 7
    contacts = 8
    telegram=9
    site=10
    phone =11
    emoReg=12
    emoCity=13
    emoSc = 14
    emoHed = 15

bot = telebot.TeleBot(config.token)
bot.delete_webhook()
now = datetime.now()
print("[{}:{}:{}]Start for {}".format(now.hour,now.minute,now.second,bot.get_me().username))
interface=telebot.types.InlineKeyboardMarkup()
interface.row(telebot.types.InlineKeyboardButton("Кнопки телеграм",callback_data="mark=tg"))
interface.row(telebot.types.InlineKeyboardButton("Гипперссылки",callback_data="mark=txt"))
markTG = telebot.types.InlineKeyboardMarkup()
#markTG.row(telebot.types.InlineKeyboardButton("Изменить набор Emoji:",callback_data = "emo_change"))
markTG.row(telebot.types.InlineKeyboardButton("Меню текстом", callback_data="mark=txt"))
markTXT = telebot.types.InlineKeyboardMarkup()
markTXT.row(telebot.types.InlineKeyboardButton("Кнопочное меню", callback_data="mark=tg"))
homeKB = telebot.types.ReplyKeyboardMarkup()
homeKB.row(telebot.types.KeyboardButton("Интерефейс"))
def heads(section_id):
    print(section_id)
    connect = sqlite3.connect(DB_PATH)
    c = connect.cursor()
    c.execute("SELECT head_id,head_name FROM head WHERE section_id = {}".format(section_id))
    connect.commit()
    head_list = c.fetchall()
    result = "Введите код рубрики раздела:\n\n"
    for item in head_list:
        result += "{}.{}".format(item[0],item[1]) + "\n"
    return result
def showPr(reg_id,user_id):
    try:
        connect = sqlite3.connect(ADMIN_PATH)
        c = connect.cursor()
        c.execute("SELECT text,views FROM pr WHERE reg_id = {}".format(reg_id))
        pr = c.fetchone()
        bot.send_message(user_id, pr[0])
        c.execute("UPDATE pr SET views = {}".format(int(pr[1]) + 1))
        connect.commit()
    except:
        pass
@bot.message_handler(content_types='[text,photo]')
def handl_msg(message):                                                                #Обработка сообщений
    try:
        if not tgbotlib.in_table("bcbot.db","users","user_id",message.from_user.id):   #Проверка на нового юзера
            connect = sqlite3.connect(DB_PATH)
            c = connect.cursor()
            if 'None' in str(message.from_user.username):                              #Запись юзера без ника в БД
                c.execute("INSERT INTO users(user_id,username,state,region_id,city_id)"
                          "VALUES ('" + str(message.from_user.id) + "','None',0,0,0)")
            else:                                                                      #Запись юзера в БД
                c.execute("INSERT INTO users(user_id,username,state,region_id,city_id)"
                      "VALUES ('" + str(message.from_user.id) + "','" + message.chat.username + "',0,0,0)")
            connect.commit()                                                           #Запись изменений
            bot.send_message(message.from_user.id,"Добро пожаловать, друг!\n\nДля начала давай определимся со стилем меню для твоего размера экрана:",
                             reply_markup=interface)                                   #Приветствие
            return
        if '/start' in message.text:
            if "reg" in message.text:
                region_id = message.text[11:]
                connect = sqlite3.connect(DB_PATH)
                c = connect.cursor()
                c.execute("UPDATE users SET region_id={} WHERE user_id = {}".format(region_id, message.from_user.id))
                connect.commit()
                c.execute("SELECT region_name FROM region WHERE region_id = {}".format(region_id))
                region_name = c.fetchone()[0]
                bot.send_message(message.from_user.id, "Вы выбрали *{}*".format(region_name),
                                 parse_mode="Markdown")
                if get_cm(message.from_user.id) == 0:
                    bot.send_message(message.from_user.id, "Города", reply_markup=city_markup(message.from_user.id))
                else:
                    if isinstance(city_markup(message.from_user.id), list):
                        bot.send_message(message.from_user.id, "Города\n{}".format(city_markup(message.from_user.id)[0]),parse_mode="Markdown")
                        bot.send_message(message.from_user.id, city_markup(region_id, message.from_user.id)[1],parse_mode="Markdown")
                    else:
                        bot.send_message(message.from_user.id, "Города\n{}".format(city_markup(message.from_user.id)),parse_mode="Markdown")
                return
            if "city" in message.text:
                city_id = message.text[12:]
                print(city_id)
                connect = sqlite3.connect(DB_PATH)
                c = connect.cursor()
                c.execute("UPDATE users SET city_id={} WHERE user_id = {}".format(city_id, message.from_user.id))
                connect.commit()
                c.execute("SELECT city_name FROM city WHERE city_id = {} AND region_id = {}".format(city_id, c.execute(
                    "SELECT region_id FROM users WHERE user_id = " + str(message.from_user.id)).fetchone()[0]))
                city_name = c.fetchone()[0]
                bot.send_message(message.from_user.id, "Вы выбрали *{}*".format(city_name),
                                 parse_mode="Markdown")
                if get_cm(message.from_user.id) == 0:
                    bot.send_message(message.from_user.id, "Разделы", reply_markup=section_markup(message.from_user.id))
                else:
                    if isinstance(section_markup(message.from_user.id), list):
                        bot.send_message(message.from_user.id, "Разделы", reply_markup=section_markup(message.from_user.id))
                        bot.send_message(message.from_user.id, "Разделы\n{}".format(section_markup(message.from_user.id)[0]) ,parse_mode="Markdown")
                        bot.send_message(message.from_user.id, section_markup(city_id, message.from_user.id)[1], parse_mode="Markdown")
                    else:
                        bot.send_message(message.from_user.id, "Разделы\n{}".format(section_markup(message.from_user.id)),parse_mode="Markdown")
                return
            if "hed" in message.text:
                head_id = message.text[11:message.text.find('sec')]        #Выбор нужных ID из сообщения
                section_id = message.text[message.text.find('sec=')+4:]
                #print("hedID: {}\nsecID: {}".format(head_id,section_id))
                connect = sqlite3.connect(DB_PATH)
                c = connect.cursor()
                reg_id = c.execute("SELECT region_id FROM users WHERE user_id = {}".format(                                        #Парсим ID региона и города из БД
                    message.from_user.id)).fetchone()[0]
                city_id = c.execute("SELECT city_id FROM users WHERE user_id = {}".format(
                    message.from_user.id)).fetchone()[0]
                c.execute("UPDATE users SET head_id={} WHERE user_id = {}".format(head_id, message.from_user.id))
                connect.commit()
                head_name = c.execute("SELECT head_name FROM head WHERE head_id = {} AND section_id = {}".format(head_id,          #Парсим название рубрики из БД
                                                                                                                 section_id)).fetchone()[0]
                changes = telebot.types.InlineKeyboardMarkup()
                changes.row(telebot.types.InlineKeyboardButton("Разместить свои данные", callback_data="add"))
                bot.send_message(message.from_user.id, 'Рубрика:"*{}*"'.format(head_name), reply_markup=changes,                   #Отправляем сообщение с выбранной рубрикой,
                                 parse_mode='Markdown')                                                                            #И предлагаем разместить свои данные
                contacts = c.execute(
                    "SELECT * FROM contacts WHERE section_id = {} AND head_id = {} AND region_id = {} AND city_id = {} AND mod = 1".format(
                        section_id, head_id,reg_id, city_id)).fetchall()                                                           #Парсим записи по выбранному пути
                print("contacts: " + str(len(contacts)))
                if len(contacts)<1:                                                                                                #Проверка на наличие записей
                    bot.send_message(message.from_user.id,"Здесь ещё нет контактов!")
                showPr(reg_id,message.from_user.id)                                                                                #Отображение рекламы
                get_contacts(message.from_user.id, contacts)                                                                       #Отображение контактов
                return
            if "sc" in message.text:
                section_id = message.text[10:]
                connect = sqlite3.connect(DB_PATH)
                c = connect.cursor()
                c.execute("UPDATE users SET section_id={} WHERE user_id = {}".format(section_id, message.from_user.id))
                connect.commit()
                c.execute("SELECT section_name FROM section WHERE section_id = {}".format(section_id))
                section_name = c.fetchone()[0]
                bot.send_message(message.from_user.id, "Вы выбрали *{}*".format(section_name), parse_mode='Markdown')
                if get_cm(message.from_user.id) == 0:
                    bot.send_message(message.from_user.id, "Рубрики",
                                     reply_markup=head_markup(section_id, message.from_user.id))
                else:
                    hedKB = head_markup(section_id,message.from_user.id)
                    if isinstance( hedKB, list):
                        bot.send_message(message.from_user.id,
                                         "Рубрики\n{}".format( hedKB[0]),parse_mode="Markdown")
                        bot.send_message(message.from_user.id,  hedKB[1], parse_mode="Markdown")
                    else:
                        bot.send_message(message.from_user.id,
                                         "Рубрики\n{}".format( hedKB),
                                         parse_mode="Markdown")
                return
        state = tgbotlib.get_state('bcbot.db',message.from_user.id);
        if state == State.emoReg.value:
            if len(message.text) == 1:
                emoDef = telebot.types.InlineKeyboardMarkup()
                emoDef.row(telebot.types.InlineKeyboardButton("Стандартный",callback_data="regDef"))
                bot.send_message(message.from_user.id,"{} - установлен как иконка регионов!".format(message.text),reply_markup=emoDef)
                connect = sqlite3.connect(DB_PATH)
                c = connect.cursor()
                c.execute("UPDATE users SET emoReg = '{}' WHERE user_id = {}".format(message.text,message.from_user.id))
                connect.commit()
                bot.send_message(message.from_user.id,"Регионы:",reply_markup=region_markup(message.from_user.id))
            else:
                bot.send_message(message.from_user.id,"Это не смайлик,пробуй ещё")
            tgbotlib.set_state('bcbot.db',State.home,message.from_user.id)
            return
        if state == State.emoCity.value:
            if len(message.text) == 1:
                emoDef = telebot.types.InlineKeyboardMarkup()
                emoDef.row(telebot.types.InlineKeyboardButton("Стандартный",callback_data="cityDef"))
                bot.send_message(message.from_user.id,"{} - установлен как иконка городов!".format(message.text),reply_markup=emoDef)
                connect = sqlite3.connect(DB_PATH)
                c = connect.cursor()
                c.execute("UPDATE users SET emoCity = '{}' WHERE user_id = {}".format(message.text,message.from_user.id))
                connect.commit()
                bot.send_message(message.from_user.id,"Города:",reply_markup=city_markup(message.from_user.id))
            else:
                bot.send_message(message.from_user.id,"Это не смайлик,пробуй ещё")
            tgbotlib.set_state('bcbot.db',State.home,message.from_user.id)
            return
        if "Интерфейс" in message.text:
            bot.send_message(message.from_user.id,"Выбери стиль меню для твоего размера экрана:",reply_markup=interface)
            return
        if '/start' in message.text:
            bot.send_message(message.from_user.id,"Начать новый поиск?",reply_markup=interface)
            return
        if state == State.add.value:
            connect = sqlite3.connect(DB_PATH)
            c = connect.cursor()
            c.execute(
                "SELECT region_id,city_id,section_id,head_id FROM users WHERE user_id = {}".format(message.from_user.id))
            ids = c.fetchone()
            yesorno = telebot.types.InlineKeyboardMarkup()
            yesorno.row(telebot.types.InlineKeyboardButton("Да",callback_data="yesName"),
                        telebot.types.InlineKeyboardButton("Нет",callback_data="noName"))
            c.execute("INSERT INTO contacts(name,region_id,city_id,section_id,head_id) VALUES('{}',{},{},{},{})".format(message.text,ids[0],ids[1],ids[2],ids[3]))
            connect.commit()
            bot.send_message(message.from_user.id,"Имя: {}\nПодтвердить?".format(message.text),reply_markup=yesorno)
            tgbotlib.set_state("bcbot.db",State.desc,message.from_user.id)
            return
        if state == State.desc.value:
            if len(message.text)>100:
                bot.send_message(message.from_user.id,"Описание должно быть короче 100 символов.Попробуйте ещёраз:")
                return
            connect = sqlite3.connect(DB_PATH)
            c = connect.cursor()
            cid = c.execute("SELECT contact_id FROM contacts ORDER BY contact_id DESC LIMIT 1").fetchone()[0]
            c.execute("UPDATE contacts SET desc = '{}' WHERE contact_id = {}".format(message.text,cid))
            yesorno = telebot.types.InlineKeyboardMarkup()
            yesorno.row(telebot.types.InlineKeyboardButton("Да", callback_data="yesDesc"),
                        telebot.types.InlineKeyboardButton("Нет", callback_data="noDesc"))
            bot.send_message(message.from_user.id, "Описание: {}\nПодтвердить?".format(message.text), reply_markup=yesorno)
            connect.commit()
            tgbotlib.set_state("bcbot.db", State.telegram, message.from_user.id)
            return
        if state == State.telegram.value:
            connect = sqlite3.connect(DB_PATH)
            c = connect.cursor()
            cid = c.execute("SELECT contact_id FROM contacts ORDER BY contact_id DESC LIMIT 1").fetchone()[0]
            c.execute("UPDATE contacts SET telegram_id = '{}' WHERE contact_id = {}".format("t.me/"+message.text[1:], cid))
            yesorno = telebot.types.InlineKeyboardMarkup()
            yesorno.row(telebot.types.InlineKeyboardButton("Да", callback_data="yesTg"),
                        telebot.types.InlineKeyboardButton("Нет", callback_data="noTg"))
            bot.send_message(message.from_user.id, "Телеграм: {}\nПодтвердить?".format(message.text), reply_markup=yesorno)
            connect.commit()
            tgbotlib.set_state("bcbot.db", State.phone, message.from_user.id)
            return
        if state == State.phone.value:
            connect = sqlite3.connect(DB_PATH)
            c = connect.cursor()
            cid = c.execute("SELECT contact_id FROM contacts ORDER BY contact_id DESC LIMIT 1").fetchone()[0]
            c.execute("UPDATE contacts SET phone = '{}' WHERE contact_id = {}".format(message.text, cid))
            yesorno = telebot.types.InlineKeyboardMarkup()
            yesorno.row(telebot.types.InlineKeyboardButton("Да", callback_data="yesPh"),
                        telebot.types.InlineKeyboardButton("Нет", callback_data="noPh"))
            bot.send_message(message.from_user.id, "Телефон: {}\nПодтвердить?".format(message.text), reply_markup=yesorno)
            connect.commit()
            tgbotlib.set_state("bcbot.db", State.site, message.from_user.id)
            return
        if state == State.site.value:
            connect = sqlite3.connect(DB_PATH)
            c = connect.cursor()
            cid = c.execute("SELECT contact_id FROM contacts ORDER BY contact_id DESC LIMIT 1").fetchone()[0]
            ids = c.execute("SELECT region_id,city_id,head_id,section_id FROM contacts  WHERE contact_id = {}".format(cid)).fetchone()
            c.execute("UPDATE contacts SET site = '{}' WHERE contact_id = {}".format(message.text, cid))
            yesorno = telebot.types.InlineKeyboardMarkup()
            yesorno.row(telebot.types.InlineKeyboardButton("Да", callback_data="yesSt"),
                        telebot.types.InlineKeyboardButton("Нет", callback_data="noSt"))
            bot.send_message(message.from_user.id, "Сайт: {}\nПодтвердить?".format(message.text), reply_markup=yesorno)
            connect.commit()
            return
        if state == State.contacts.value:
            try:
                contacts = message.text.split(";")
                print(message.text)
                print(contacts[0],contacts[1],contacts[2])
                telegram = "t.me/"+contacts[0][1:]
                print(telegram)
                connect = sqlite3.connect(DB_PATH)
                print("connect")
                c = connect.cursor()
                cid = c.execute("SELECT contact_id FROM contacts ORDER BY contact_id DESC LIMIT 1").fetchone()[0]
                print(cid)
                c.execute("UPDATE contacts SET telegram_id = '{}',phone = '{}',site = '{}' WHERE contact_id = {}".format(telegram,contacts[1],contacts[2],cid))
                connect.commit()
                yesorno = telebot.types.InlineKeyboardMarkup()
                yesorno.row(telebot.types.InlineKeyboardButton("Да", callback_data="yesCont"),
                            telebot.types.InlineKeyboardButton("Нет", callback_data="noCont"))
                bot.send_message(message.from_user.id, "Телеграм: {}\nТелефон: {}\nСайт: {}\nПодтвердить?".format(telegram,contacts[1],contacts[2]), reply_markup=yesorno)
            except Exception as e:
                bot.send_message(message.from_user.id,"Вы ввели данные не в правильном формате!",reply_markup=interface)
            return
                # if message.from_user.id == 36148543 or message.from_user.id == 60569417:
                #     c.execute("INSERT INTO contacts(name,desc,telegram_id,phone,site,section_id,head_id, region_id,city_id,mod)"
                #               "VALUES ('" + contact[0] + "','" + contact[1] + "','" + contact[2] + "','" + contact[
                #                   3] + "','" + contact[4] + "'," + str(ids[2]) + "," + str(ids[3]) + "," + str(
                #         ids[0]) + "," + str(ids[1]) + ",1)")
                #     bot.send_message(message.from_user.id, "Запись добавлена!")
                # else:
                #     c.execute("INSERT INTO contacts(name,desc,telegram_id,phone,site,section_id,head_id, region_id,city_id)"
                #           "VALUES ('" + contact[0] + "','" + contact[1] + "','" + contact[2] + "','" + contact[3] + "','" + contact[4] + "'," + str(ids[2]) + "," + str(ids[3]) + "," + str(ids[0]) + "," + str(ids[1]) + ")")
                #     bot.send_message("@bcalert", ids[0])
                #     bot.send_message(message.from_user.id, "Ваш запрос принят!")
                # connect.commit()
                # connect = sqlite3.connect(DB_PATH)
                # c = connect.cursor()
                # c.execute("UPDATE admins SET state=0 WHERE user_id = {}".format(message.from_user.id))
                # connect.commit()
        if state == State.city.value:
            connect = sqlite3.connect(DB_PATH)
            c = connect.cursor()
            c.execute("SELECT region_id FROM users WHERE user_id = {}".format(message.from_user.id))
            region_id = c.fetchone()[0]
            c.execute("SELECT * FROM city WHERE city_id = {} AND region_id = {}".format(message.text,region_id))
            city = c.fetchone()
            if city is None:
                bot.send_message(message.from_user.id,"Вы ввели неверное значение",reply_markup=interface)
                return
            c.execute("UPDATE users SET city_id = {} WHERE user_id = {}".format(city[0], message.from_user.id))
            connect.commit()
            bot.send_message(message.from_user.id,"Вы выбрали *{}*".format(city[2]),parse_mode='Markdown')
            tgbotlib.set_state("bcbot.db", State.section, message.from_user.id)
            return
        if state==State.section.value:
            try:
                if message.text.isdigit():

                    connect = sqlite3.connect(DB_PATH)
                    c = connect.cursor()
                    c.execute("UPDATE users SET section_id={} WHERE user_id = {}".format(message.text,message.from_user.id))
                    connect.commit()
                    c.execute("SELECT section_name FROM section WHERE section_id = {}".format(message.text))
                    section_name = c.fetchone()[0]
                    c.execute("SELECT city_id FROM users WHERE user_id = {}".format(message.from_user.id))
                    city_id = c.fetchone()[0]

            except Exception as e:
                bot.send_message(message.from_user.id, "Попробуй ещё раз.\nErrorMSG: " + str(e))
                return
            bot.send_message(message.from_user.id,"Вы выбрали *{}*".format(section_name),parse_mode='Markdown')
            bot.send_message(message.from_user.id,heads(message.text))
            tgbotlib.set_state("bcbot.db", State.head, message.from_user.id)
            return
        if state == State.head.value:
            connect = sqlite3.connect(DB_PATH)
            c = connect.cursor()
            change = c.execute("SELECT city_id,section_id,region_id FROM users WHERE user_id = {}".format(message.from_user.id)).fetchone()
            head_name = c.execute("SELECT head_name FROM head WHERE head_id = {}".format(message.text)).fetchone()[0]
            changes = telebot.types.InlineKeyboardMarkup()
            changes.row(telebot.types.InlineKeyboardButton("Разместить свои данные", callback_data="add"))
            bot.send_message(message.from_user.id,'Рубрика:"*{}*"'.format(head_name),reply_markup=changes,parse_mode='Markdown')
            c.execute("SELECT * FROM contacts WHERE section_id = {} AND head_id = {} AND city_id = {} AND region_id = {}".format(change[1],message.text,change[0],change[2]))
            contacts = c.fetchall()
            if len(contacts) == 0:
                bot.send_message(message.from_user.id,"Тут ещё нет контактов.",reply_markup=interface)
            showPr(change[2],message.from_user.id)
            get_contacts(message.from_user.id,contacts)
            return
    except Exception as e:
        print("Message error: {}".format(e))

def get_contacts(user_id,contacts):
    result = ""
    result2 = ""
    i=1
    print("Count: {}".format(len(contacts)))
    for contact in contacts:
        result+="{}.*{}*\n_{}_\n\nТелефон: {}\nTelegram: {}\nСайт: {}\n\n".format(i,contact[2], contact[5], contact[7],
                                                                          contact[6],contact[1],contact[7])
        i+=1
    if len(result)<4096:
         bot.send_message(user_id,result,parse_mode='Markdown',disable_web_page_preview=True)
         return
    result=""
    for contact in contacts:
        if len(result)<4000:
            result+="*{}*\n_{}_\n\nТелефон: +{}\nTelegram: {}\nСайт: {}\n\n".format(contact[2], contact[5], contact[7],
                                                                          contact[6],contact[1],contact[7])
        else:
            result2+="*{}*\n_{}_\n\nТелефон: +{}\nTelegram: {}\nСайт: {}\n\n".format(contact[2], contact[5], contact[7],
                                                                          contact[6],contact[1],contact[7])
    if len(result2)>1:
        bot.send_message(user_id,result,parse_mode='Markdown',disable_web_page_preview=True)
        bot.send_message(user_id,result2,parse_mode='Markdown',disable_web_page_preview=True)

    bot.send_message(user_id,
                     "Рады были помочь Вам!\nПо поводу размещения рекламы на @{}\nНачать новый поиск /start".format(
                         config.adminUsername),reply_markup=interface)
    return
@bot.callback_query_handler(func =lambda call:True)
def callback_handler(call):                                                         #Обработка нажатий Callback клавиатуры
    now = datetime.now()
    print("Get callback: {}\nUID: {}\nTime: {}\nState: {}"
          .format(call.data,call.from_user.id,str(now),tgbotlib.get_state('bcbot.db',call.from_user.id)))
    try:
        if "emo_change" in call.data:
            emoKB = telebot.types.InlineKeyboardMarkup()
            emoKB.row(telebot.types.InlineKeyboardButton("Регионы",callback_data="emo_reg"))
            emoKB.row(telebot.types.InlineKeyboardButton("Города",callback_data="emo_city"))
            bot.send_message(call.from_user.id,"Выбери где ты хочешь поменять emoji:",reply_markup=emoKB)
            bot.answer_callback_query(call.id,"Customize!")
        if "regDef" in call.data:
            connect =sqlite3.connect(DB_PATH)
            c = connect.cursor()
            c.execute("UPDATE users SET emoReg = '🏘' WHERE user_id = {}".format(call.from_user.id))
            connect.commit()
            bot.answer_callback_query(call.id,"Иконка регионов в классическом виде")
            return
        if "cityDef" in call.data:
            connect = sqlite3.connect(DB_PATH)
            c = connect.cursor()
            c.execute("UPDATE users SET emoCity = '🏠' WHERE user_id = {}".format(call.from_user.id))
            connect.commit()
            bot.answer_callback_query(call.id, "Иконка городов в классическом виде")
            return
        if "emo_reg" in call.data:
            tgbotlib.set_state('bcbot.db',State.emoReg,call.from_user.id)
            bot.send_message(call.from_user.id,"Отправь мне смайлик на регионы:")
            return
        if "emo_city" in call.data:
            tgbotlib.set_state('bcbot.db',State.emoCity,call.from_user.id)
            bot.send_message(call.from_user.id,"Отправь мне смайлик на города:")
            return
        if "mark=tg" in call.data:                                                                             #Выбор кнопочного меню
            bot.answer_callback_query(call.id,"Вы выбрали кнопочное меню!")
            connect = sqlite3.connect(DB_PATH)
            c = connect.cursor()
            c.execute("UPDATE users SET cm=0 WHERE user_id='{}'".format(call.from_user.id))                    #Запись выбранного стиля в БД
            connect.commit()
            bot.send_message(call.from_user.id,"Вы выбрали кнопочное меню:",reply_markup=markTG)
            bot.send_message(call.from_user.id,"Регионы:",reply_markup=region_markup(call.from_user.id))       #Отображение регионов кнопками
            return
        if "mark=txt" in call.data:                 #Выбор текстового меню
            bot.answer_callback_query(call.id, "Вы выбрали текстовое меню!")
            connect = sqlite3.connect(DB_PATH)
            c = connect.cursor()
            c.execute("UPDATE users SET cm=1 WHERE user_id='{}'".format(call.from_user.id))                     #Запись выбранного стиля в БД
            connect.commit()
            bot.send_message(call.from_user.id, "Вы выбрали текстовое меню", reply_markup=markTXT)              #Отображение регионов текстом
            if  isinstance(region_markup(call.from_user.id),list):                                              #Случай когда список не помещаеться в 1 сообщение
                bot.send_message(call.from_user.id,"Регионы:\n" + region_markup(call.from_user.id)[0],parse_mode="Markdown")
                bot.send_message(call.from_user.id,region_markup(call.from_user.id)[1],parse_mode="Markdown")   #Разбиваем на 2 отдельных
            else:
                bot.send_message(call.from_user.id,"Регионы:\n{}"
                                 .format(region_markup(call.from_user.id)),parse_mode="Markdown")               #Или не разбиваем если помещаеться :)
            return
        if "sc=" in call.data and "hed" not in call.data:
            secId = call.data[3]
            print("secID: {}".format(secId))
            connect = sqlite3.connect(DB_PATH)
            c = connect.cursor()
            c.execute("UPDATE users SET section_id={} WHERE user_id = {}".format(secId, call.from_user.id))
            connect.commit()
            c.execute("SELECT section_name FROM section WHERE section_id = {}".format(secId))
            section_name = c.fetchone()[0]
            bot.send_message(call.from_user.id,"Вы выбрали *{}*".format(section_name),parse_mode='Markdown')
            if get_cm(call.from_user.id) ==0:
                bot.send_message(call.from_user.id,"Рубрики",reply_markup=head_markup(secId,call.from_user.id))
            else:
                hedKb = head_markup(secId, call.from_user.id)
                if isinstance(hedKb, list):
                    bot.send_message(call.from_user.id, "Рубрики\n{}".format(hedKb[0]),parse_mode="Markdown")
                    bot.send_message(call.from_user.id, hedKb[1],parse_mode="Markdown")
                else:
                    bot.send_message(call.from_user.id,"Рубрики\n{}".format(hedKb),parse_mode="Markdown")
            return
        if "reg=" in call.data:
            region_id = call.data[4:]
            connect = sqlite3.connect(DB_PATH)
            c = connect.cursor()
            c.execute("UPDATE users SET region_id={} WHERE user_id = {}".format(region_id, call.from_user.id))
            connect.commit()
            c.execute("SELECT region_name FROM region WHERE region_id = {}".format(region_id))
            region_name = c.fetchone()[0]
            bot.send_message(call.from_user.id, "Вы выбрали *{}*".format(region_name),
                             parse_mode="Markdown")
            if get_cm(call.from_user.id) == 0:
                bot.send_message(call.from_user.id, "Города",reply_markup=city_markup(call.from_user.id))
            else:
                if isinstance(city_markup(call.from_user.id), list):
                    bot.send_message(call.from_user.id, "Города\n{}".format(city_markup(call.from_user.id)[0]))
                    bot.send_message(call.from_user.id, city_markup(call.data[3:][1], call.from_user.id))
                else:
                    bot.send_message(call.from_user.id, "Города\n{}".format(city_markup(call.from_user.id)))
        if "city=" in call.data:
            city_id = call.data[5:]
            print(city_id)
            connect = sqlite3.connect(DB_PATH)
            c = connect.cursor()
            c.execute("UPDATE users SET city_id={} WHERE user_id = {}".format(city_id, call.from_user.id))
            connect.commit()
            c.execute("SELECT city_name FROM city WHERE city_id = {} AND region_id = {}".format(city_id,c.execute("SELECT region_id FROM users WHERE user_id = "+str(call.from_user.id)).fetchone()[0]))
            city_name = c.fetchone()[0]
            bot.send_message(call.from_user.id, "Вы выбрали *{}*".format(city_name),
                             parse_mode="Markdown")
            if get_cm(call.from_user.id) == 0:
                bot.send_message(call.from_user.id, "Разделы", reply_markup=section_markup(call.from_user.id))
            else:
                if isinstance(section_markup(call.from_user.id), list):
                    bot.send_message(call.from_user.id, "Разделы", reply_markup=section_markup(call.from_user.id))
                    bot.send_message(call.from_user.id, "Разделы\n{}".format(section_markup(call.from_user.id)[0]),parse_mode="Markdown")
                    bot.send_message(call.from_user.id, section_markup(call.data[3:][1], call.from_user.id),parse_mode="Markdown")
                else:
                    bot.send_message(call.from_user.id, "Разделы\n{}".format(section_markup(call.from_user.id)),parse_mode="Markdown")
        if "hed=" in call.data:
            try:
                head_id = call.data[4:call.data.find('sec')]
                secId = call.data[call.data.find('sec')+4:]
                print("hID: {}\nsID: {}".format(head_id,secId))
                connect = sqlite3.connect(DB_PATH)
                c = connect.cursor()
                c.execute("UPDATE users SET head_id={},section_id={} WHERE user_id = {}".format(head_id,secId, call.from_user.id))
                connect.commit()
                change = c.execute(
                    "SELECT city_id,section_id,region_id FROM users WHERE user_id = {}".format(call.from_user.id)).fetchone()
                head_name = c.execute("SELECT head_name FROM head WHERE head_id = {} AND section_id = {}".format(head_id,secId)).fetchone()[0]
                changes = telebot.types.InlineKeyboardMarkup()
                changes.row(telebot.types.InlineKeyboardButton("Разместить свои данные", callback_data="add"))
                bot.send_message(call.from_user.id, 'Рубрика:"*{}*"'.format(head_name),reply_markup=changes, parse_mode='Markdown')
                c.execute("SELECT * FROM contacts WHERE section_id = {} AND head_id = {} AND region_id = {} AND city_id = {} AND mod = 1".format(secId, head_id,change[2],change[0]))
                contacts = c.fetchall()
                print("contacts: " + str(len(contacts)))
                if len(contacts)<1:
                    bot.send_message(call.from_user.id,"Здесь ёще нет записей.")
                showPr(change[2], call.from_user.id)
                get_contacts(call.from_user.id,contacts)
            except Exception as e:
                print(e)
        if "yesName" in call.data:
            bot.answer_callback_query(call.id,"Верно")
            bot.send_message(call.from_user.id,"Введите описание: ")
            return
        if "yesDesc" in call.data:
            bot.answer_callback_query(call.id,"Верно")
            bot.send_message(call.from_user.id, "Введите контакты @телеграм: ")
            return
        if "yesTg" in call.data:
            bot.answer_callback_query(call.id,"Верно")
            bot.send_message(call.from_user.id,"Введите номер телефона:")
            return
        if "yesPh" in call.data:
            bot.answer_callback_query(call.id,"Верно")
            bot.send_message(call.from_user.id,"Введите ссылку на сайт:")
            return
        if "yesSt" in call.data:
            bot.answer_callback_query(call.id,"Верно")
            bot.send_message(call.from_user.id,"Ваша заявка принята и будет добавлена после модерации!",reply_markup=interface)
            return
        if "noName" in call.data or "noDesc" in call.data or "noCont" in call.data or "noSt" in call.data or "noPh" in call.data:
            bot.answer_callback_query(call.id,"Отмена")
            tgbotlib.set_state('bcbot.db',State.home,call.from_user.id)
            connect = sqlite3.connect(DB_PATH)
            c = connect.cursor()
            c.execute("DELETE FROM contacts WHERE contact_id = {}".format(c.execute("SELECT contact_id FROM contacts ORDER BY contact_id DESC LIMIT 1").fetchone()[0]))
            connect.commit()
            return
        if "yes" in call.data:
            bot.answer_callback_query(call.id, "Новый поиск!")
            if get_cm(call.from_user.id) == 0:
                bot.send_message(call.from_user.id,"Регионы:",reply_markup=region_markup(call.from_user.id))
            else:
                if isinstance(region_markup(call.from_user.id), list):
                    bot.send_message(call.from_user.id, "Регионы:\n" + region_markup(call.from_user.id)[0],parse_mode="Markdown")
                    bot.send_message(call.from_user.id, region_markup(call.from_user.id)[1],parse_mode="Markdown")
                else:
                    bot.send_message(call.from_user.id, "Регионы:\n" + region_markup(call.from_user.id),parse_mode="Markdown")
            return
        if "no" in call.data:
            bot.answer_callback_query(call.id, "Нет")
            return
        if "add" in call.data:
            bot.send_message(call.from_user.id,"Введите информацию о себе по очереди(Имя,Описание,Контакты):\n")
            tgbotlib.set_state("bcbot.db", State.add, call.from_user.id)
    except Exception as e:
        print("Callback error: {}".format(e))
def section_list():
    connect = sqlite3.connect(DB_PATH)
    c = connect.cursor()
    c.execute("SELECT * FROM section")
    sections = c.fetchall()
    result = ""
    for section in sections:
        result += str(section[0]) + "." + section[1] + "\n"
    return result
def city_list(region_id):
    connect = sqlite3.connect(DB_PATH)
    c = connect.cursor()
    c.execute("SELECT * FROM city WHERE region_id = {}".format(region_id))
    cityes = c.fetchall()
    result = ""
    for city in cityes:
        result += str(city[0]) + "." + city[2] + "\n"
    return result
def region_list():
    connect = sqlite3.connect(DB_PATH)
    c = connect.cursor()
    c.execute("SELECT * FROM region")
    regions = c.fetchall()
    result = ""
    for region in regions:
        result+=str(region[0])+"."+region[1]+"\n"
    return result
def get_cm(user_id):
    connect =sqlite3.connect(DB_PATH)
    c = connect.cursor()
    c.execute("SELECT cm FROM users WHERE user_id = {}".format(user_id))
    return  int(c.fetchone()[0])

def section_markup(user_id):
    connect = sqlite3.connect(DB_PATH)
    c = connect.cursor()
    c.execute("SELECT * FROM section")
    sections = c.fetchall()
    if get_cm(user_id) == 0:
        result = telebot.types.InlineKeyboardMarkup()
        i = 0
        for section in sections:
            result.row(telebot.types.InlineKeyboardButton("{}{}".format(section[2],section[1]),callback_data="sc={}".format(section[0])))
            i+=1
        return result
    else:
        result = ""
        result2 = ""
        for section in sections:
            result += "[{}.{}](t.me/{}?start=sc={})\n".format(section[0], section[1],config.Username, section[0])
    if len(result) < 4096:
        return result
    result = ""
    for section in sections:
        if len(result) > 4000:
            result2 += "[{}.{}](t.me/{}?start=sc={})\n".format(section[0], section[1],config.Username, section[0])
        else:
            result += "[{}.{}](t.me/{}?start=sc={})\n".format(section[0], section[1],config.Username, section[0])
    return [result, result2]
def region_markup(user_id):
    connect = sqlite3.connect(DB_PATH)
    c = connect.cursor()
    c.execute("SELECT emoReg FROM users WHERE user_id = {}".format(user_id))
    emoji = c.fetchone()[0]
    if 'None' in str(emoji):
        emoji = "🏘"
    c.execute("SELECT * FROM region")
    regions = c.fetchall()
    if get_cm(user_id) == 0:
        result = telebot.types.InlineKeyboardMarkup()
        for region in regions:
            result.row(telebot.types.InlineKeyboardButton("{}{}".format(emoji,region[1]),callback_data="reg={}".format(region[0])))
        return result
    else:
        result = ""
        result2=""
        for region in regions:
            result+="[{}.{}](t.me/{}?start=reg={})\n".format(region[0],region[1],config.Username,region[0])
    if len(result)<4096:
        return result
    result=""
    for region in regions:
        if len(result)>4000:
            result2+="[{}.{}](t.me/{}?start=reg={})\n".format(region[0],region[1],config.Username,region[0])
        else:
            result+="[{}.{}](t.me/{}?start=reg={})\n".format(region[0],region[1],config.Username,region[0])
    return [result,result2]
def city_markup(user_id):
    print("city")
    connect = sqlite3.connect(DB_PATH)
    c = connect.cursor()
    c.execute("SELECT emoCity FROM users WHERE user_id = {}".format(user_id))
    emoji = c.fetchone()[0]
    if 'None' in str(emoji):
        emoji = "🏠"
    c.execute("SELECT city_id,city_name FROM city WHERE region_id={}".format(c.execute("SELECT region_id FROM users WHERE user_id = {}".format(user_id)).fetchone()[0]))
    cityes = c.fetchall()
    if get_cm(user_id)==0:
        result = telebot.types.InlineKeyboardMarkup()
        for city in cityes:
            result.row(telebot.types.InlineKeyboardButton("{}{}".format(emoji,city[1]),callback_data="city={}".format(city[0])))
        return result
    else:
        result = ""
        result2=""
        for city in cityes:
            result+="[{}.{}](t.me/{}?start=city={})\n".format(city[0],city[1],config.Username,city[0])
        if len(result) < 4096:
            return result
        result = ""
        for city in cityes:
            if len(result) > 4000:
                result2 += "[{}.{}](t.me/{}?start={city={})\n".format(city[0], city[1],config.Username, city[0])
            else:
                result += "[{}.{}](t.me/{}?start={city={})\n".format(city[0], city[1],config.Username, city[0])
        return [result, result2]
    return result
def head_markup(section_id, user_id):
    connect = sqlite3.connect(DB_PATH)
    c = connect.cursor()
    c.execute("SELECT head_id,head_name FROM head WHERE section_id = {}".format(section_id))
    heads = c.fetchall()
    if get_cm(user_id) == 0:
        result = telebot.types.InlineKeyboardMarkup()
        for head in heads:
            result.row(telebot.types.InlineKeyboardButton("📒{}".format(head[1]),callback_data="hed={}sec={}".format(head[0],section_id)))
    else:
        result = ""
        result2 = ""
        for head in heads:
            result+="[{}.{}](t.me/{}?start=hed={}sec={})\n".format(head[0],head[1],config.Username,head[0],section_id)
        if len(result) < 4096:
            return result
        result = ""
        for head in heads:
            if len(result) > 4000:
                result2 += "[{}.{}](t.me/{}?start={hed={}sec={})\n".format(head[0], head[1],config.Username, head[0],section_id)
            else:
                result += "[{}.{}](t.me/{}?start={hed={}sec={})\n".format(head[0], head[1],config.Username, head[0],section_id)
        return [result, result2]
    return result
# try:
#     bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,certificate=open(WEBHOOK_SSL_CERT, 'r'))
#     cherrypy.config.update({
#         'server.socket_host': WEBHOOK_LISTEN,
#         'server.socket_port': WEBHOOK_PORT,
#         'server.ssl_module': 'builtin',
#         'server.ssl_certificate': WEBHOOK_SSL_CERT,
#         'server.ssl_private_key': WEBHOOK_SSL_PRIV
#     })
#     cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
#     print(bot.get_webhook_info())
# except Exception as e:
#     print("Webhook error: {}".format(e))
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print("Error")
        time.sleep(15)