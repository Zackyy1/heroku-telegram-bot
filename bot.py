
# -*- coding: utf-8 -*-

print("Version 0.1")

import redis
import os
import telebot
from telebot import types
import parnu
import languages
from firebase import firebase
import requests
from flask import request
import json
from flask import jsonify
from flask import Flask

token = os.environ['TELEGRAM_TOKEN']
server = Flask(__name__)
firebase = firebase.FirebaseApplication('https://databaserests.firebaseio.com', None)

######################################## VARIABLES ################################################################################################
global stage
stage = 0

chatid = "404202426"
pack = 0
prevstage = 0
global restaurantDesired
restaurantDesired = 2
global restaurantCurrent
restaurantCurrent = 0
global step
step = 0

restaurantStageButtons = [""]

language = languages.languages["english"]

dict = parnu.restaurants
restaurants = {}
for i in range(0, len(dict)):
    keys = sorted(dict.keys(), key=lambda x: (dict[x]["priority"]))[i]
    restaurants[keys] = dict[keys]

knownUsers = []  # todo: save these in a file,
userStep = {}  # so they won't reset every time the bot restarts
commands = {  # command description used in the "help" command
              'start': 'Start / reset bot',
              'help': 'Shows this help text',
              'settings': "Shows settings",
              'home':"Main menu / return Home"
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
            print (str(m.chat.first_name) + " [" + str(m.chat.id) + "]: " + m.text)
bot = telebot.TeleBot(token)
bot.set_update_listener(listener)
start_message_1 = "I'm your Seljanka bot. And I'll help you with anything, bruh!"
start_message_2 = "What would you like to do today?"
help_message= """
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
    shouldShowMore = True
    rests = list(kl.values())

    for x in range(1, 3):
        if step < len(rests):
            pack = rests[step]
            openedLang = pack[language["openedLocal"]]
            addressLang = language["address"]
            inlineLink = types.InlineKeyboardMarkup()
            inlbut = types.InlineKeyboardButton(text = pack["name"], url = pack["link"])
            inlbut2 = types.InlineKeyboardButton(text = language["showmap"], url = "https://www.google.ee/maps/place/"+pack["latitude"]+","+pack["longitude"])
            inlineLink.add(inlbut)
            inlineLink.add(inlbut2)
            bot.send_photo(mes, pack["image"])
            #bot.send_message(mes, "+37253088726")
            #f bot.send_contact(mes, phone_number='+37253088726', first_name=pack['name'])
            bot.send_message(mes, pack["name"] + ", " + openedLang + addressLang + pack["address"]+ ". Tel: "+pack['phone'], reply_markup=inlineLink)


            step += 1
            print(str(step)+"/"+str(len(rests)))
            if len(rests) == step:
                shouldShowMore = False
                print("rests == step")
                bot.send_message(mes, text=language["endoflist"])
                setStage(0, mes)

        elif step >= len(rests) or step == len(rests):
            shouldShowMore = False
            print("we got into elif tho")
            bot.send_message(mes, text=language["endoflist"])
            setStage(0, mes)

    if shouldShowMore == True:
        bot.send_message(mes, text="Show 2 more?", reply_markup= newButton(language["showmore"], language["home"]))
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

def applyStage(stageNum, chid):
    global step
    global stage
    if stageNum == 0:
        bot.send_message(chid, text=language["initstage0"], reply_markup=newButton(language['restaurants']))
        step = 0
    elif stageNum == 4:
        bot.send_message(chid, text="FOOD!!!!", reply_markup=newButton(language["toprestsaround"], language['offers'],language['home']))
    elif stageNum == 33:
        sort(restaurants, chid)
    elif stageNum == 13:
        bot.send_message(chid, text="Let's choose your preferred language", reply_markup=langStage)


    else:
        return
        #setStage(0, chatid)
        #bot.send_message(chid, text="Something wrong happened... Returning to Menu!", reply_markup=markup0)


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
    result = firebase.get('/' + str(message.from_user.id), None)
    if result == None:
        print("New user, adding to the database")
        #result = firebase.post('/'+str(message.from_user.id),message.from_user.first_name)
        bot.send_message(message.chat.id, text=language["firstwelcome1"], reply_markup=hide)
        bot.send_message(message.chat.id, text=language["firstwelcome2"])
        bot.send_message(message.chat.id, text=language["firstwelcome3"])
        setStage(13, cid)
    else:
        print("Existing user")
        user = message.from_user.first_name
        bot.send_message(cid, language["welcome1"])
        bot.send_message(cid, language["welcome2"], reply_markup=hide)
        setStage(0, cid)
        prevstage = stage

@bot.message_handler(commands=['home'])
def command_home(m):
    print("Going home from /home command")
    setStage(0, m.chat.id)

@bot.message_handler(commands=['help'])
def command_help(m):
    cid = m.chat.id
    help_text = "The following commands are available: \n"
    for key in commands:  # generate help text out of the commands dictionary defined at the top
        help_text += "/" + key + ": "
        help_text += commands[key] + "\n"
    bot.send_message(cid, help_text)  # send the generated help page

@bot.message_handler(commands=['settings'])
def command_help(m):
    bot.send_message(m.chat.id, language['settingsMsg'], reply_markup=newButton(language["language"], language['city']))

@bot.message_handler(content_types=["text"])
def handleSoup(message):
    global step
    global language
    global languages
    global stage
    cid = message.chat.id
    if message.text == language["restaurants"]:
        setStage(4, cid)
        bot.send_message(message.chat.id, text=language['initstage4'])
    elif message.text == "Home" or message.text == "Tagasi" or message.text == "Назад":
        bot.send_message(message.chat.id, text=language["returning"])
        setStage(0, message.chat.id)

    elif message.text == language["toprestsaround"]:
        setStage(33, cid)

    elif message.text == language["offers"]:
        bot.send_message(message.chat.id, text=language["maintenance"])
        setStage(0, cid)
    elif message.text == language["showmore"]:
        print("Sorting 3 more, starting at "+str(step))
        setStage(33, cid)

    elif message.text == "English" and stage == 13:
        print("Changed language to English")
        language = languages.languages["english"]
        setStage(0, cid)

    elif message.text == "Eesti" and stage == 13:
        print("Changed language to Eesti")
        language = languages.languages["estonian"]
        setStage(0, cid)
        print("Stage to 0 with language "+message.text)
    elif message.text == language['language']:
        setStage(13, cid)
    elif message.text == language['city']:
        print("soon!")
        bot.send_message(message.chat.id, text=language["maintenance"])
        setStage(0, cid)
        #todo: Make inter-city lists :))))))

    else:
        bot.send_message(message.chat.id, text=language["unknown"])

########################################################################################################################


TOKEN = token
PORT = int(os.environ.get('PORT', '8443'))
updater = Updater(TOKEN)
# add handlers
updater.start_webhook(listen="0.0.0.0",
                      port=PORT,
                      url_path=TOKEN)
updater.bot.set_webhook("https://seljankatest.herokuapp.com/" + TOKEN)
updater.idle()
