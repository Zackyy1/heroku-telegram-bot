# -*- coding: utf-8 -*-

print("Version 0.2")

import redis
import os
import telebot
from telebot import types
import parnu
import languages
import inlineQuery
from firebase import firebase
import requests
import re
from flask import request
import localDB
import json
from flask import jsonify
from flask import Flask

token = os.environ['TELEGRAM_TOKEN']

firebase = firebase.FirebaseApplication('https://databaserests.firebaseio.com', None)

my_url = 'https://databaserests.firebaseio.com'

######################################## VARIABLES ################################################################################################
global stage
stage = 0
global language
chatid = "404202426"
pack = 0
prevstage = 0
global restaurantDesired
restaurantDesired = 2
global restaurantCurrent
restaurantCurrent = 0
global step
step = 0


def getLang(chat_id):
    usr = localDB.database[str(chat_id.chat.id)]
    print('got ' + str(usr))
    return languages.languages[usr]


restaurantStageButtons = [""]

city = parnu

restaurantsDict = city.restaurants
restaurants = {}
for i in range(0, len(restaurantsDict)):
    keys = sorted(restaurantsDict.keys(), key=lambda x: (restaurantsDict[x]["priority"]))[i]
    restaurants[keys] = restaurantsDict[keys]

knownUsers = []  # todo: save these in a file,
userStep = {}  # so they won't reset every time the bot restarts
commands = {  # command description used in the "help" command
    'start': 'Start / reset bot',
    'help': 'Shows this help text',
    'settings': "Shows settings",
    'home': "Main menu / return Home"
}


########################################################################################################################################


#################################   UTIL    #######################################################################################################

def listener(messages):
    """
    When new messages arrive TeleBot will call this function.
    """
    for m in messages:
        if m.content_type == 'text':
            # print the sent message to the console
            print(str(m.chat.first_name) + " [" + str(m.chat.id) + "]: " + m.text)


bot = telebot.TeleBot(token)
bot.set_update_listener(listener)
start_message_1 = "I'm your Seljanka bot. And I'll help you with anything, bruh!"
start_message_2 = "What would you like to do today?"
help_message = """
This is a help page. We don't need any help, thank you.
Go back to your soup."""

########################################################################################################################################


hide = types.ReplyKeyboardRemove()


def newButton(*args):
    mrkup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for arg in args:
        mrkbut = types.KeyboardButton(arg)
        mrkup.add(mrkbut)
    return mrkup


langStage = types.ReplyKeyboardMarkup(row_width=0.5, one_time_keyboard=True)
english = types.KeyboardButton("English")
estonian = types.KeyboardButton("Eesti")
russian = types.KeyboardButton("Русский")
langStage.add(english, estonian, russian)


########################################################### FUNCTIONS ####################################################################################################


def sort(tab1, mes):
    global step
    kl = tab1
    chid = mes.chat.id
    shouldShowMore = True
    mess = chid
    rests = list(kl.values())
    global language
    for x in range(1, 3):
        if step < len(rests):
            pack = rests[step]
            openedLang = pack[getLang(mes)["openedLocal"]]
            addressLang = getLang(mes)["address"]
            inlineLink = types.InlineKeyboardMarkup()
            inlbut = types.InlineKeyboardButton(text=pack["name"], url=pack["link"])
            inlbut2 = types.InlineKeyboardButton(text=getLang(mes)["showmap"],
                                                 url="https://www.google.ee/maps/place/" + pack["latitude"] + "," +
                                                     pack["longitude"])
            inlineLink.add(inlbut)
            inlineLink.add(inlbut2)
            bot.send_photo(mess, pack["image"])
            # bot.send_message(mes, "+37253088726")
            # f bot.send_contact(mes, phone_number='+37253088726', first_name=pack['name'])
            bot.send_message(mess, pack["name"] + ", " + openedLang + addressLang + pack["address"] + ". Tel: " + pack[
                'phone'], reply_markup=inlineLink)

            step += 1
            print(str(step) + "/" + str(len(rests)))
            if len(rests) == step:
                shouldShowMore = False
                print("rests == step")
                bot.send_message(mess, text=getLang(mes)["endoflist"])
                setStage(0, mes)

        elif step >= len(rests) or step == len(rests):
            shouldShowMore = False
            print("we got into elif tho")
            bot.send_message(mess, text=getLang(mes)["endoflist"])
            setStage(0, mes)

    if shouldShowMore == True:
        bot.send_message(mess, text="Show 2 more?", reply_markup=newButton(getLang(mes)["showmore"],
                                                                          getLang(mes)["home"]))
    else:
        return False


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
        bot.send_message(chid, text=getLang(ch)["initstage0"],
                         reply_markup=newButton(getLang(ch)['restaurants']))
        step = 0

    elif stageNum == 4:
        bot.send_message(chid, text="FOOD!!!!", reply_markup=newButton(getLang(ch)["toprestsaround"],
                                                                       getLang(ch)['offers'],
                                                                       getLang(ch)['home']))

    elif stageNum == 33:
        sort(restaurants, ch)

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
        # setStage(0, chatid)
        # bot.send_message(chid, text="Something wrong happened... Returning to Menu!", reply_markup=markup0)


def sendPhoto(name):
    pack = city.restaurants[name]
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


###########################################################################################################################################################################################


#########################################   HANDLERS   ####################################################################################################################################
@bot.message_handler(commands=['start'])
def command_start(message):
    cid = message.chat.id
    result = firebase.get('/users/' + str(message.from_user.id), None)

    if result == None:
        print("New user, adding to the database")
        result = firebase.patch('/users/' + str(message.from_user.id) + "/",  {"name": message.from_user.first_name})
        bot.send_message(message.chat.id, text="Hello, dear friend! It's the first time you are using me, so let me help you.")
        bot.send_message(message.chat.id, text="I will show you where you can have fun and get your pizza dosage back to normal!")
        bot.send_message(message.chat.id, text="Type \'/help\' for additional commands & info!")
        setStage(13, message)
        chosenlang = "english"
        localDB.database[str(message.from_user.id)] = chosenlang
    else:
        chosenlang = "english"
        localDB.database[str(message.from_user.id)] = chosenlang
        bot.send_message(cid, getLang(message)["welcome1"])
        bot.send_message(cid, getLang(message)["welcome2"], reply_markup=hide)
        setStage(0, message)

@bot.message_handler(commands=['home'])
def command_home(m):
    print("Going home from /home command")
    setStage(0, m)


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
    global language
    bot.send_message(m.chat.id, getLang(m)['settingsMsg'],
                     reply_markup=newButton(getLang(m)["language"],
                                            getLang(m)['city']))


print(list(parnu.inline.values()))
arr = list(parnu.inline.values())
print(arr, list(parnu.inline.keys()))


@bot.inline_handler(func=lambda query: len(query.query) > 0)
def smth(inline_query):
    qid = inline_query.id
    query = inline_query.query
    key = types.InlineKeyboardMarkup()

    list1 = list(inlineQuery.all.keys())
    list2 = list(inlineQuery.all.values())
    print(len(inlineQuery.all), list1[0])
    # try:
    for i in range(0, len(inlineQuery.all)):
        if query[0:len(query)].lower() == str(list1[i])[0:len(query)].lower():
            print((query[0:len(query)].lower(), str(list1[i])[0:len(query)].lower()))

            key.add(types.InlineKeyboardButton(text=list2[i]['name'], url=list2[i]['link']))
            key.add(types.InlineKeyboardButton(text="Show on map",
                                               url="https://www.google.ee/maps/place/" + list2[i]["latitude"] + "," +
                                                   list2[i]["longitude"]))
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
        print("Sorting 3 more, starting at " + str(step))
        setStage(33, mes)

    elif message.text == "English" and stage == 13:
        print("Changed language to English")
        chosenlang = "english"
        localDB.database[str(message.from_user.id)] = chosenlang
        setStage(14, mes)

    elif message.text == "Eesti" and stage == 13:
        print("Changed language to Eesti")
        chosenlang = "estonian"
        localDB.database[str(message.from_user.id)] = chosenlang
        setStage(14, mes)

    elif message.text == "English" and stage != 13:
        print("Changed language to English")
        chosenlang = "english"
        localDB.database[str(message.from_user.id)] = chosenlang
        setStage(0, mes)

    elif message.text == "Eesti" and stage != 13:
        print("Changed language to Eesti")
        chosenlang = "estonian"
        localDB.database[str(message.from_user.id)] = chosenlang
        setStage(0, mes)

    elif message.text == getLang(cidi)['language'] and stage != 13:

        setStage(15, mes)

    elif message.text == getLang(cidi)['city'] and stage != 13:
        setStage(14, mes)

    elif stage == 14:
        if message.text == getLang(cidi)['parnu']:
            city = parnu
            print("Set city to parnu")
        elif message.text == getLang(cidi)['tallinn']:
            city = parnu
            print("set city to Tallinn (parnu)")
        setStage(0, mes)
    else:
        bot.send_message(message.chat.id, text=getLang(cidi)["unknown"])


########################################################################################################################


@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://seljankatest.herokuapp.com/' + TOKEN)
    return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
