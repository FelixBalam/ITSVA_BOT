import telebot
from telebot import types
from dotenv import load_dotenv
import os
import sqlite3

load_dotenv()

TOKEN = os.getenv("MYTOKEN")
bot = telebot.TeleBot(TOKEN)

user_data = {}
current_state = ''

db_connection = sqlite3.connect("gaviBOT.db")
db_cursor = db_connection.cursor()
db_cursor.execute("INSERT INTO misc_report('user_id', 'description') VALUES ('user_a', 'sample report')")
db_connection.commit()

@bot.message_handler(commands=['start'])
def main_menu(message):
    user_data[message.chat.id] = {'State':'MAIN_MENU'}
    
    # Crear los primeros dos botones para que el usuario elija si encontró o perdió un objeto
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("Report lost and found objects", callback_data='LOST_FOUND')
    button2 = types.InlineKeyboardButton("Report damaged furniture or equipment", callback_data='DAMAGES')
    button3 = types.InlineKeyboardButton("Report something else", callback_data='MISC')
    button4 = types.InlineKeyboardButton("Request information", callback_data='INFO')
    markup.add(button1, button2, button3, button4)
    
    bot.send_message(message.chat.id, "Welcome! \nHow can I help you today?", reply_markup=markup)

# --------------
# LOST AND FOUND
# --------------
# Report Type
@bot.callback_query_handler(func=lambda call: call.data == 'LOST_FOUND')
def lost_found_menu(call):
    update_state(call.message.chat.id, call.data)
    
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("I lost something", callback_data='LOST')
    button2 = types.InlineKeyboardButton("I found something", callback_data='FOUND')
    markup.add(button1, button2)
    
    bot.send_message(call.message.chat.id, "Did you find or lose an object?", reply_markup=markup)

# Object Information
@bot.callback_query_handler(func=lambda call: call.data in ['LOST', 'FOUND'])
def lf_object_status(call):
    update_state(call.message.chat.id, call.data)
    
    if call.data == 'LOST':
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton("I have a picture", callback_data='PICTURE')
        button2 = types.InlineKeyboardButton("Just give a description", callback_data='LF_DESCRIPTION')
        markup.add(button1, button2)

        user_data[call.message.chat.id]['found'] = 'false'
        bot.send_message(call.message.chat.id, "I'm so sorry to hear that \nDo you have a picture of the missing object?", reply_markup=markup)
        
    if call.data == 'FOUND':
        update_state(call.message.chat.id, 'LF_DESCRIPTION')
        user_data[call.message.chat.id]['found'] = 'true'
        bot.send_message(call.message.chat.id, "Please give me a detailed description of the object")
    
@bot.callback_query_handler(func=lambda call: call.data in ['PICTURE', 'LF_DESCRIPTION'])
def lf_object_status(call):
    update_state(call.message.chat.id, call.data)
    
    if call.data == 'PICTURE':
        bot.send_message(call.message.chat.id, "Awesome, feel free to send it")
        
    if call.data == 'LF_DESCRIPTION':
        user_data[call.message.chat.id]['image_url'] = 'null'
        bot.send_message(call.message.chat.id, "Please give me a detailed description of the object")

# Picture Input
@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('State') == 'PICTURE')
def handle_description_input(message):
    #TODO: validate input
    last_picture = bot.get_file(message.photo[-1].file_id)
    path = last_picture.file_path
    url = f'https://api.telegram.org/file/bot/{TOKEN}/{path}'
    
    user_data[message.chat.id]['image_url'] = url
    
    update_state(message.chat.id, 'LF_DESCRIPTION')
    bot.reply_to(message, "Picture recived! \nPlease give me a detailed description of the object as well")
    
# Description Input
@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('State') == 'LF_DESCRIPTION')
def handleLF_description_input(message):
    user_data[message.chat.id]['description'] = message.text
    update_state(message.chat.id, 'LF_LOCATION')
    bot.reply_to(message, f"Description submited! \nWhere was the object lost/found?")
    
# Location Input
@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('State') == 'LF_LOCATION')
def handleLF_location_input(message):
    user_data[message.chat.id]['location'] = message.text
    update_state(message.chat.id, 'LF_DATE')
    bot.reply_to(message, f"Location submited! \nWhen did you find/lose the object?")
    
# Date Input
@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('State') == 'LF_DATE')
def handleLF_location_input(message):
    user_data[message.chat.id]['date'] = message.text
    update_state(message.chat.id, 'LF_END')
    bot.reply_to(message, f"Date submited! \nYour report is being processed")
    
    submitLF_report(message)

# Submit LF Report
def submitLF_report(message):
    db_connection = sqlite3.connect("gaviBOT.db")
    db_cursor = db_connection.cursor()
    
    db_cursor.execute("INSERT INTO object_report('user_id', 'found', 'image_url', 'description', 'location', 'date') VALUES (?, ?, ?, ?, ?, ?)", 
                      [message.from_user.id,
                      user_data[message.chat.id]['found'],
                      user_data[message.chat.id]['image_url'],
                      user_data[message.chat.id]['description'],
                      user_data[message.chat.id]['location'],
                      user_data[message.chat.id]['date']])
    db_connection.commit()
    update_state(message.chat.id, 'MAIN_MENU')
    bot.send_message(message.chat.id, "Your report has been submited!, we'll reach out with any updates")

# Export Report to DB
@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('State') == 'LF_END')
def handleLF_location_input(message):
    update_state(message.chat.id, 'MAIN_MENU')
    bot.send_message(message.chat.id, "Please wait while your report is being processed")
    
def update_state(chat_id, new_state):
    user_data[chat_id]['State'] = new_state
    current_state = new_state
    
@bot.callback_query_handler(func=lambda call: call.data in ['aula_lugar', 'hora', 'descripcion'])
def handle_found_object(call):
    # Configurar el estado según la opción seleccionada
    if call.data == 'aula_lugar':
        user_data[call.from_user.id]['State'] = 'AWAITING_LOCATION'
        bot.send_message(call.message.chat.id, "Por favor, indica el aula o lugar donde encontraste el objeto.")
    elif call.data == 'hora':
        user_data[call.from_user.id]['State'] = 'AWAITING_TIME'
        bot.send_message(call.message.chat.id, "Por favor, indica la hora aproximada en que encontraste el objeto.")
    elif call.data == 'descripcion':
        user_data[call.from_user.id]['State'] = 'AWAITING_LF_DESCRIPTION'
        bot.send_message(call.message.chat.id, "Por favor, describe el objeto encontrado.")
        
@bot.message_handler(func=lambda message: user_data.get(message.from_user.id, {}).get('State') in ['AWAITING_LOCATION', 'AWAITING_TIME', 'AWAITING_LF_DESCRIPTION', 'AWAITING_CONTACT'])
def handle_user_input(message):
    user_id = message.from_user.id
    state = user_data[user_id]['State']
    
    # Guardar la información del usuario dependiendo del estado
    if state == 'AWAITING_LOCATION':
        user_data[user_id]['Location'] = message.text
        bot.send_message(message.chat.id, f"Ubicación registrada: {message.text}")
    
    elif state == 'AWAITING_TIME':
        user_data[user_id]['Time'] = message.text
        bot.send_message(message.chat.id, f"Hora registrada: {message.text}")
    
    elif state == 'AWAITING_LF_DESCRIPTION':
        user_data[user_id]['Description'] = message.text
        bot.send_message(message.chat.id, f"Descripción registrada: {message.text}")
    
    elif state == 'AWAITING_CONTACT':
        user_data[user_id]['Contact'] = message.text
        bot.send_message(message.chat.id, f"Contacto registrado: {message.text}")
    
    # Restablecer el estado
    user_data[user_id]['State'] = 'SELECTING'
    
    # Mostrar los botones para regresar o continuar
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("Encontré un Objeto Extraviado", callback_data='encontre_objeto')
    button2 = types.InlineKeyboardButton("Perdí un Objeto", callback_data='perdi_objeto')
    markup.add(button1, button2)
    
    bot.send_message(message.chat.id, "¿Qué deseas hacer?", reply_markup=markup)

bot.infinity_polling()
