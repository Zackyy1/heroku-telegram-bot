# -*- coding: utf-8 -*-

print("Version 0.5")

import redis
import os
import telebot
from telebot import types
import parnu
import languages
import inlineQuery
import tallinn
from firebase import firebase
import requests
import re
from flask import request
import localDB
import json
from flask import jsonify
from flask import Flask

token = os.environ['TELEGRAM_TOKEN']
url = os.environ['FIREBASE_URL']
server = Flask(__name__)


global stage
stage = 0
pack = 0

toprestaurants = {}
restaurants = {}
wine= {}
pizza = {}
euro = {}
local = {}
asian = {}

firebase = firebase.FirebaseApplication(url, None)
bot = telebot.TeleBot(token)




restaurantStageButtons = [""]


knownUsers = []  # todo: save these in a file,
userStep = {}  # so they won't reset every time the bot restarts
commands = {  # command description used in the "help" command
    'start': 'Start / reset bot',
    'help': 'Shows this help text',
    'settings': "Shows settings",
    'home': "Main menu / return Home"
}

########################################################################################################################################

hide = types.ReplyKeyboardRemove()
langStage = types.ReplyKeyboardMarkup(row_width=0.5, one_time_keyboard=True)
english = types.KeyboardButton("English")
estonian = types.KeyboardButton("Eesti")
russian = types.KeyboardButton("Русский")
langStage.add(english, estonian, russian)


########################################################### FUNCTIONS ####################################################################################################

def sortRestByType(type, mes):

    tab = getCity(mes).restaurants
    return tab

def getCity(message):
    usr = localDB.database[str(message.from_user.id)]['city']
    chosen = parnu
    if usr == 'parnu':
        chosen = parnu
    elif usr == 'tallinn':
        chosen = tallinn
    else:
        print("There was a mistake, choosing parnu by default")
    return chosen

def sortTopRests(city):
    restaurantsDict = city.restaurants
    for i in range(0, len(restaurantsDict)):
        keys = sorted(restaurantsDict.keys(), key=lambda x: (restaurantsDict[x]["priority"]))[i]
        toprestaurants[keys] = restaurantsDict[keys] ###

def sortRests(m):
    #global wine
    #global pizza
    #global asian
    #global euro
    #global local
    #global restaurants
    db = getCity(m).restaurants
    dbkeys = list(db.keys())
    dbvalues = list(db.values())
    for i in range(0, len(db)):
        if '/restaurant' in dbvalues[i]["type"]:
            print(str(dbkeys[i]))
            restaurants[str(dbkeys[i])] = dbvalues[i]
            print("added "+str(dbkeys[i])+" to /restaurant")
    for i in range(0, len(db)):
        if '/pizza' in dbvalues[i]["type"]:
            print(str(dbkeys[i]))
            pizza[str(dbkeys[i])] = dbvalues[i]
            print("added "+str(dbkeys[i])+" to /pizza")
    for i in range(0, len(db)):
        if '/wine' in dbvalues[i]["type"]:
            print(str(dbkeys[i]))
            wine[str(dbkeys[i])] = dbvalues[i]
            print("added "+str(dbkeys[i])+" to /wine")

def getLang(message):
    usr = localDB.database[str(message.from_user.id)]['language']
    return languages.languages[usr]

def listener(messages):
    for m in messages:
        if m.content_type == 'text':
            # print the sent message to the console
            print(str(m.chat.first_name) + " [" + str(m.chat.id) + "]: " + m.text)

def newButton(*args):
    mrkup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=1)
    for arg in args:
        mrkbut = types.KeyboardButton(arg)
        mrkup.add(mrkbut)
    return mrkup

def upddb():
    attempt = firebase.get('/db', None)
    print("Should localDB.database look like this:? "+str(attempt))
    return attempt

def newInline(*args):
    imrkup = types.InlineKeyboardMarkup(row_width=2)
    for arg1, arg2 in args:
        nbut = types.InlineKeyboardButton(text=arg1, url=arg2)
        imrkup.add(nbut)
    return imrkup

def sort(tab1, mes):
    kl = tab1

    chid = mes.chat.id
    shouldShowMore = True
    mess = chid
    rests = list(kl.values())
    restskey = list(kl.keys())

    db = localDB.database[str(mes.from_user.id)]
    step = db['step']
    print("Users:"+str(mes.from_user.id)+". Step for sort: "+str(step))

    for x in range(1, 3):
        if step < len(rests):
            pack = rests[step]
            inlineLink = types.InlineKeyboardMarkup()

            menubut = types.InlineKeyboardButton(text=getLang(mes)['menu'], callback_data=str(restskey[step]))
            inlineLink.add(menubut)
            if pack['image'] is not "":
                bot.send_photo(mess, pack["image"])

            bot.send_message(mess, pack["name"] + ", " + pack["address"] + ". " + pack['phone'], reply_markup=inlineLink)

            step += 1
            print(str(db['step']) + "/" + str(len(rests)))

        elif step >= len(rests) or step == len(rests):
            shouldShowMore = False
            bot.send_message(mess, text=getLang(mes)["endoflist"])
            setStage(0, mes)
            db['step'] = step
    if shouldShowMore == True:
        bot.send_message(mess, text="Show 2 more?", reply_markup=newButton(getLang(mes)["showmore"],
                                                                          getLang(mes)["home"]))
        db['step'] = step
    else:
        return False

def save(message):
    res = firebase.patch("/db/"+str(message.from_user.id), localDB.database[str(message.from_user.id)])

def get_user_step(uid):
    if uid in userStep:
        return userStep[uid]
    else:
        knownUsers.append(uid)
        userStep[uid] = 0
        return 0

def setPrevStage(st):
    prevstage = st
    return prevstage

def applyStage(stageNum, ch):
    global step
    global language
    global stage
    chid = ch.chat.id
    if stageNum == 0:
        bot.send_message(chid, text=getLang(ch)["initstage0"], reply_markup=newButton(getLang(ch)['restaurants']))
        save(ch)
        localDB.database[str(ch.from_user.id)]['step'] = 0

    elif stageNum == 4:
        bot.send_message(chid, text="FOOD!!!!", reply_markup=newButton(getLang(ch)["toprestsaround"],
                                                                       getLang(ch)['offers'],
                                                                       getLang(ch)['home']))

    elif stageNum == 33:
        sort(toprestaurants, ch)

        ######################################      command sorting ######## todo: add more sorting options ############
    elif stageNum == 34:
        sort(toprestaurants, ch)
    elif stageNum == 35:
        sort(wine, ch)
    elif stageNum == 36:
        sort(pizza, ch)
    elif stageNum == 37:
        sort(local, ch)
    elif stageNum == 38:
        sort(asian, ch)
    elif stageNum == 39:
        sort(euro, ch)
        ################################################################################################################
    elif stageNum == 13:
        bot.send_message(chid, text="Let's choose your preferred language", reply_markup=langStage)

    elif stageNum == 15:
        bot.send_message(chid, text="Let's choose your preferred language", reply_markup=langStage)

    elif stageNum == 14:
        bot.send_message(chid, text=getLang(ch)["citychoice"],
                         reply_markup=newButton(  ####### CITIES TO SHOW todo: make more cities :)
                             getLang(ch)['tallinn'],
                             getLang(ch)['parnu']))


    else:
        return

def sendPhoto(name):
    pack = inlineQuery.all[name]
    print(pack)
    ans1 = types.InlineQueryResultPhoto('1', pack["image"], pack["image"],
                                        input_message_content=types.InputTextMessageContent(
                                            pack["name"] + ", Opened: " + pack['openedEn'] + ". " + pack[
                                                'address'] + ". Tel: " + pack['phone']))
    return ans1

def sendText(text):
    klw = types.InputTextMessageContent(text)
    return klw

def setStage(num, chatid1):
    global stage
    stage = num
    chatid = chatid1
    applyStage(stage, chatid1)


######################################################    SETUP    #################################################

localDB.database = upddb()
print("Updated database.")
bot.set_update_listener(listener)
sortTopRests(parnu)
sortTopRests(tallinn)

#########################################   HANDLERS   ####################################################################################################################################
@bot.message_handler(commands=['start'])
def command_start(message):
    cid = message.chat.id
    localDB.database = upddb()
    result = firebase.get('/users/' + str(message.from_user.id), None)


    if result is None:
        result = firebase.patch('/users/' + str(message.from_user.id) + "/",  {"name": message.from_user.first_name})
        bot.send_message(message.chat.id, text="Hello, dear friend! It's the first time you are using me, so let me help you.")
        bot.send_message(message.chat.id, text="I will show you where you can have fun and get your pizza dosage back to normal!")
        bot.send_message(message.chat.id, text="Type \'/help\' for additional commands & info!")
        setStage(13, message)
        chosenlang = "english"

        localDB.database[str(message.from_user.id)] = {'language': chosenlang, 'step': 0, 'city':'Tallinn'}
        firebase.patch('/db', localDB.database)
        print("New user, adding to the database. User's DB: "+ str(localDB.database[str(message.from_user.id)]))
    else:
        #chosenlang = localDB.database[str(message.from_user.id)]['language'] # Getting language from Local DB
        chosenlang = localDB.database[str(message.from_user.id)]['language']
        getCity = firebase.get("/db/"+str(message.from_user.id)+"/city", None)
        localDB.database[str(message.from_user.id)] = {'language' : chosenlang, 'step':0, 'city':getCity }
        print(localDB.database[str(message.from_user.id)]['step'])
        print(localDB.database[str(message.from_user.id)])
        localDB.database[str(message.from_user.id)] = firebase.get('/db/'+str(message.from_user.id), None)
        bot.send_message(cid, getLang(message)["welcome1"])
        bot.send_message(cid, getLang(message)["welcome2"], reply_markup=hide)
        print("Existing user. User's DB: " + str(localDB.database[str(message.from_user.id)]))
        setStage(0, message)

@bot.message_handler(commands=['home'])
def command_home(m):
    print("Going home from /home command")
    setStage(0, m)

@bot.message_handler(commands=['restaurant', 'restaurants'])
def list_restaurants(m):
    sortRests(m)
    localDB.database[str(m.from_user.id)]['step'] = 0
    setStage(34, m)
@bot.message_handler(commands=['wine'])
def list_restaurants(m):
    sortRests(m)
    localDB.database[str(m.from_user.id)]['step'] = 0
    setStage(35, m)
@bot.message_handler(commands=['pizza'])
def list_restaurants(m):
    sortRests(m)
    localDB.database[str(m.from_user.id)]['step'] = 0
    setStage(36, m)

@bot.message_handler(commands=['help'])
def command_help(m):
    cid = m.chat.id
    help_text = "The following commands are available: \n"
    for key in commands:  # generate help text out of the commands dictionary defined at the top
        help_text += "/" + key + ": "
        help_text += commands[key] + "\n"
    bot.send_message(cid, help_text)  # send the generated help page


@bot.message_handler(commands=['settings'])
def command_settings(m):
    bot.send_message(m.chat.id, getLang(m)['settingsMsg'], reply_markup=newButton(getLang(m)["language"], getLang(m)['city']))

@bot.callback_query_handler(func=lambda call: True)
def doit(m):
    print(m)
    findinTable = getCity(m).restaurants[m.data]
    if m.inline_message_id is None:
        bot.edit_message_reply_markup(chat_id=m.message.chat.id, message_id=m.message.message_id, reply_markup=newInline(
                                        ("Website", findinTable['link']),
                                        (getLang(m)['showmenu'], "test2.com"),
                                        (getLang(m)['showmap'],
                                         "https://www.google.ee/maps/place/" + findinTable["latitude"] + "," + findinTable["longitude"])))
    else:
        bot.edit_message_reply_markup(inline_message_id=m.inline_message_id,
                                      reply_markup=newInline(
                                          ("Website", findinTable['link']),
                                          ("Show menu", "test2.com"),
                                          ("Show on map",
                                           "https://www.google.ee/maps/place/" + findinTable["latitude"] + "," +
                                           findinTable["longitude"])))


@bot.message_handler(commands = ['a'])
def test(mes):
    bot.send_message(mes.chat.id, text="Test", reply_markup=newInline(("Test button 1",
                                                                       'https://www.tutorialspoint.com/python/python_tuples.htm'),
                                                                      ('test button 2',
                                                                      'https://www.tutorialspoint.com/python/python_tuples.htm')))

print(list(parnu.inline.values()))
arr = list(parnu.inline.values())



@bot.inline_handler(func=lambda query: len(query.query) > 0)
def smth(inline_query):
    qid = inline_query.id
    query = inline_query.query
    key = types.InlineKeyboardMarkup()
    list1 = list(inlineQuery.all.keys())
    list2 = list(inlineQuery.all.values())

    # try:
    for i in range(0, len(inlineQuery.all)):
        if query[0:len(query)].lower() == str(list1[i])[0:len(query)].lower():
            print((query[0:len(query)].lower(), str(list1[i])[0:len(query)].lower()))

            key.add(types.InlineKeyboardButton(text="Menu", callback_data=str(list1[i])))

            result1 = types.InlineQueryResultPhoto('0', list2[i]['image'], list2[i]['image'],
                                                   caption=list2[i]["name"] + ", Address: " + list2[i][
                                                       "address"] + ". Tel: " + list2[i]['phone'],
                                                   reply_markup=key)  # input_message_content=types.InputTextMessageContent(list2[i]['name'])
            bot.answer_inline_query(qid, [result1])

    # except Exception as e:
    # print(e)
    # return


@bot.message_handler(content_types=["text"])
def handleSoup(message):
    global step
    global language
    global city
    global stage
    mes = message
    cid = message.chat.id
    cidi = message
    if message.text == getLang(cidi)["restaurants"]:

        setStage(4, mes)
        localDB.database[str(message.from_user.id)]['step'] = 0
        bot.send_message(message.chat.id, text=getLang(cidi)['initstage4'])
    elif message.text == "Home" or message.text == "Tagasi" or message.text == "Назад":
        bot.send_message(message.chat.id, text=getLang(cidi)["returning"])
        setStage(0, mes)

    elif message.text == getLang(cidi)["toprestsaround"]:
        setStage(33, mes)

    elif message.text == getLang(cidi)["offers"]:
        bot.send_message(message.chat.id, text=getLang(cidi)["maintenance"])
        setStage(0, mes)

    elif message.text == getLang(cidi)["showmore"]:
        setStage(stage, mes)

    elif message.text == "English" and stage == 13:
        print("Changed language to English")
        chosenlang = "english"
        localDB.database[str(message.from_user.id)]['language'] = chosenlang
        setStage(14, mes)

    elif message.text == "Eesti" and stage == 13:
        print("Changed language to Eesti")
        chosenlang = "estonian"
        localDB.database[str(message.from_user.id)]['language'] = chosenlang
        setStage(14, mes)

    elif message.text == "English" and stage != 13:
        print("Changed language to English")
        chosenlang = "english"
        localDB.database[str(message.from_user.id)]['language'] = chosenlang
        setStage(0, mes)

    elif message.text == "Eesti" and stage != 13:
        print("Changed language to Eesti")
        chosenlang = "estonian"
        localDB.database[str(message.from_user.id)]['language'] = chosenlang
        setStage(0, mes)

    elif message.text == getLang(cidi)['language'] and stage != 13:

        setStage(15, mes)

    elif message.text == getLang(cidi)['city'] and stage != 13:
        setStage(14, mes)

    elif stage == 14:
        if message.text == getLang(cidi)['parnu']:
            city = 'parnu'
            localDB.database[str(message.from_user.id)]['city'] = city
            print("Set city to parnu")
        elif message.text == getLang(cidi)['tallinn']:
            city = 'tallinn'
            localDB.database[str(message.from_user.id)]['city'] = city
            print("Set city to Tallin () parnu")
        setStage(0, mes)
    else:
        bot.send_message(message.chat.id, text=getLang(cidi)["unknown"])


########################################################################################################################


@server.route('/' + token, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://seljankatest.herokuapp.com/' + token)
    return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
