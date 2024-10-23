import telebot
from telebot import types
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("MYTOKEN")
bot = telebot.TeleBot(TOKEN)

user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Crear los primeros dos botones para que el usuario elija si encontró o perdió un objeto
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("Encontré un Objeto Extraviado", callback_data='encontre_objeto')
    button2 = types.InlineKeyboardButton("Perdí un Objeto", callback_data='perdi_objeto')
    markup.add(button1, button2)
    
    bot.send_message(message.chat.id, "¿Qué deseas hacer?", reply_markup=markup)
    user_data[message.from_user.id] = {'State': 'SELECTING'}

@bot.callback_query_handler(func=lambda call: call.data in ['encontre_objeto', 'perdi_objeto', 'regresar'])
def handle_selection(call):
    if call.data == 'encontre_objeto':
        # Crear los botones para "Encontré un Objeto Extraviado"
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton("Aula o Lugar", callback_data='aula_lugar')
        button2 = types.InlineKeyboardButton("Hora", callback_data='hora')
        button3 = types.InlineKeyboardButton("Descripción", callback_data='descripcion')
        button_back = types.InlineKeyboardButton("Regresar", callback_data='regresar')
        markup.add(button1, button2, button3)
        markup.add(button_back)  # Añadir botón de regresar
        
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                              text="Selecciona una opción para describir el objeto que encontraste:", reply_markup=markup)
    
    elif call.data == 'perdi_objeto':
        # Botón para ingresar contacto al perder un objeto
        user_data[call.from_user.id]['State'] = 'AWAITING_CONTACT'
        bot.send_message(call.message.chat.id, "Por favor, proporciona tu contacto para que se comuniquen contigo.")
    
    elif call.data == 'regresar':
        # Regresar al menú principal
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton("Encontré un Objeto Extraviado", callback_data='encontre_objeto')
        button2 = types.InlineKeyboardButton("Perdí un Objeto", callback_data='perdi_objeto')
        markup.add(button1, button2)
        
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                              text="¿Qué deseas hacer?", reply_markup=markup)

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
        user_data[call.from_user.id]['State'] = 'AWAITING_DESCRIPTION'
        bot.send_message(call.message.chat.id, "Por favor, describe el objeto encontrado.")

@bot.message_handler(func=lambda message: user_data.get(message.from_user.id, {}).get('State') in ['AWAITING_LOCATION', 'AWAITING_TIME', 'AWAITING_DESCRIPTION', 'AWAITING_CONTACT'])
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
    
    elif state == 'AWAITING_DESCRIPTION':
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
