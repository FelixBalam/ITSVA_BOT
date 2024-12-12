import telebot  # Librería para la interacción con el bot de Telegram
from telebot import types  # Manejo de botones y tipos de mensajes
from dotenv import load_dotenv  # Para cargar variables de entorno
import os  # Manejo de variables del sistema
import sqlite3  # Base de datos SQLite

# Cargar las variables de entorno del archivo .env
load_dotenv()

# Inicializar el bot con el token
TOKEN = os.getenv("MYTOKEN")
bot = telebot.TeleBot("7229947344:AAHrFsa1aAjDbKlCgtIxS5AH7FRN7xiHswI")

# Variables globales para rastrear datos de usuario y estados
user_data = {}

# Función para obtener conexión a la base de datos
def get_db_connection():
    return sqlite3.connect("gaviBOT.db")

# ---------------
# MENÚ PRINCIPAL
# ---------------
@bot.message_handler(commands=['start'])
def main_menu(message):
    """
    Función que muestra el menú principal al iniciar la interacción.
    """
    user_data[message.chat.id] = {'State': 'MAIN_MENU'}
    
    # Crear botones principales
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("Reportar objetos perdidos y encontrados", callback_data='LOST_FOUND')
    button2 = types.InlineKeyboardButton("Solicitar información", callback_data='INFO')
    button3 = types.InlineKeyboardButton("Buscar objeto por ID", callback_data='SEARCH_OBJECT')
    markup.add(button1, button2, button3)
    
    # Enviar mensaje con los botones
    bot.send_message(message.chat.id, "¡Bienvenido! ¿Cómo puedo ayudarte hoy?", reply_markup=markup)

# --------------------
# REPORTES DE OBJETOS
# --------------------
@bot.callback_query_handler(func=lambda call: call.data == 'LOST_FOUND')
def lost_found_menu(call):
    """
    Muestra opciones específicas para objetos perdidos/encontrados.
    """
    update_state(call.message.chat.id, call.data)
    
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("Perdí algo", callback_data='LOST')
    button2 = types.InlineKeyboardButton("Encontré algo", callback_data='FOUND')
    button3 = types.InlineKeyboardButton("Regresar al menú principal", callback_data='BACK_TO_MAIN')
    markup.add(button1, button2, button3)
    
    bot.send_message(call.message.chat.id, "¿Perdiste o encontraste un objeto?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['LOST', 'FOUND'])
def lf_object_status(call):
    """
    Maneja la entrada del usuario indicando si perdió o encontró un objeto.
    """
    update_state(call.message.chat.id, call.data)
    
    if call.data == 'LOST':
        # Caso de objeto perdido
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton("Tengo una foto", callback_data='PICTURE')
        button2 = types.InlineKeyboardButton("Solo dar una descripción", callback_data='LF_DESCRIPTION')
        button3 = types.InlineKeyboardButton("Regresar al menú principal", callback_data='BACK_TO_MAIN')
        markup.add(button1, button2, button3)

        user_data[call.message.chat.id]['found'] = 'false'
        bot.send_message(call.message.chat.id, "Lamento escuchar eso. ¿Tienes una foto del objeto perdido?", reply_markup=markup)
        
    elif call.data == 'FOUND':
        # Caso de objeto encontrado
        update_state(call.message.chat.id, 'LF_DESCRIPTION')
        user_data[call.message.chat.id]['found'] = 'true'
        bot.send_message(call.message.chat.id, "Por favor, dame una descripción detallada del objeto.")

@bot.callback_query_handler(func=lambda call: call.data == 'BACK_TO_MAIN')
def back_to_main_menu(call):
    """
    Regresa al menú principal.
    """
    main_menu(call.message)

@bot.callback_query_handler(func=lambda call: call.data in ['PICTURE', 'LF_DESCRIPTION'])
def lf_object_description(call):
    """
    Maneja la selección de descripción o imagen.
    """
    update_state(call.message.chat.id, call.data)
    
    if call.data == 'PICTURE':
        bot.send_message(call.message.chat.id, "Genial, envíala cuando puedas.")
        
    if call.data == 'LF_DESCRIPTION':
        user_data[call.message.chat.id]['image_url'] = 'null'
        bot.send_message(call.message.chat.id, "Por favor, da una descripción detallada del objeto.")

# --------------------
# ENTRADA DE IMAGEN
# --------------------
@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('State') == 'PICTURE')
def handle_image_input(message):
    """
    Captura y guarda la imagen proporcionada, verificando si es un archivo PNG o JPG.
    """
    if message.photo:
        # Extraer la última foto de mayor calidad
        file_id = message.photo[-1].file_id
        
        try:
            # Obtener el archivo de la foto usando el file_id
            file_info = bot.get_file(file_id)
            file_path = file_info.file_path
            file_url = f'https://api.telegram.org/file/bot{TOKEN}/{file_path}'

            # Verificar que la imagen es en formato PNG o JPG
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                # Guardar la URL de la imagen en el estado del usuario
                user_data[message.chat.id]['image_url'] = file_url
                update_state(message.chat.id, 'LF_DESCRIPTION')

                # Confirmar al usuario que la foto fue recibida
                bot.reply_to(message, "¡Imagen recibida! Ahora por favor da una descripción detallada del objeto.")
            else:
                bot.reply_to(message, "Por favor, asegúrate de enviar una imagen en formato PNG o JPG.")
        
        except Exception as e:
            bot.reply_to(message, f"Ocurrió un error al procesar la foto. Error: {e}")
    else:
        bot.reply_to(message, "No se detectó una foto en tu mensaje. Por favor, intenta enviar una imagen.")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('State') == 'LF_DESCRIPTION')
def handleLF_description_input(message):
    """
    Captura y guarda la descripción del objeto.
    """
    user_data[message.chat.id]['description'] = message.text
    update_state(message.chat.id, 'LF_LOCATION')
    bot.reply_to(message, "¡Descripción registrada! ¿Dónde se perdió o encontró el objeto?")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('State') == 'LF_LOCATION')
def handleLF_location_input(message):
    """
    Captura y guarda la ubicación del objeto.
    """
    user_data[message.chat.id]['location'] = message.text
    update_state(message.chat.id, 'LF_DATE')
    bot.reply_to(message, "¡Ubicación registrada! ¿Cuándo se perdió o encontró el objeto?")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('State') == 'LF_DATE')
def handleLF_date_input(message):
    """
    Captura y guarda la fecha relacionada con el objeto.
    """
    user_data[message.chat.id]['date'] = message.text
    update_state(message.chat.id, 'LF_END')
    bot.reply_to(message, "¡Fecha registrada! Tu reporte está siendo procesado.")
    submitLF_report(message)

# -------------------
# ENVÍO DEL REPORTE
# -------------------
def submitLF_report(message):
    """
    Envía el reporte a la base de datos SQLite.
    """
    description = user_data[message.chat.id].get('description', '').strip()
    if not description:
        description = 'Descripción no proporcionada'
        
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO object_report('user_id', 'found', 'image_url', 'description', 'location', 'date') VALUES (?, ?, ?, ?, ?, ?)",
        [
            message.from_user.id,
            1 if user_data[message.chat.id]['found'] == 'false' else 0,  # Convertir a entero
            user_data[message.chat.id].get('image_url', 'null'),
            description,
            user_data[message.chat.id]['location'],
            user_data[message.chat.id]['date']
        ]
    )
    connection.commit()
    object_id = cursor.lastrowid
    connection.close()
    update_state(message.chat.id, 'MAIN_MENU')
    bot.send_message(message.chat.id, f"¡Tu reporte ha sido enviado! El ID de tu reporte es {object_id}. Guárdalo para futuras referencias.")

@bot.callback_query_handler(func=lambda call: call.data == 'SEARCH_OBJECT')
def search_object_menu(call):
    """
    Muestra el menú para buscar un objeto por ID.
    """
    update_state(call.message.chat.id, 'SEARCH_OBJECT')
    bot.send_message(call.message.chat.id, "Por favor, envía el ID del objeto que deseas buscar.")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('State') == 'SEARCH_OBJECT')
def handle_search_object(message):
    object_id = message.text
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM object_report WHERE rowid = ?", (object_id,))
        result = cursor.fetchone()
        connection.close()

        if result:
            # Interpretar el valor de 'found'
            status_message = "El objeto está en la caseta." if result[1] == 0 else "El objeto ha sido devuelto al dueño."

            image_url = result[2] if result[2] != 'null' else None

            message_text = f"Estado del objeto:\n" \
                           f"ID: {object_id}\n" \
                           f"Descripción: {result[4]}\n" \
                           f"Ubicación: {result[5]}\n" \
                           f"Fecha: {result[6]}\n" \
                           f"{status_message}"

            markup = types.InlineKeyboardMarkup()
            if result[1] == 0:  # Si el objeto está perdido, podemos cambiar su estado
                button = types.InlineKeyboardButton("Marcar como entregado", callback_data=f'CHANGE_STATUS_{object_id}')
                markup.add(button)

            if image_url and image_url != 'null':
                try:
                    bot.send_photo(message.chat.id, image_url, caption=message_text, reply_markup=markup)
                except Exception as e:
                    bot.send_message(message.chat.id, f"{message_text}\n\nImagen no disponible.", reply_markup=markup)
            else:
                bot.send_message(message.chat.id, f"{message_text}\n\nImagen no disponible.", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "No se encontró ningún objeto con ese ID.")
    
    except Exception as e:
        bot.send_message(message.chat.id, f"Hubo un error al buscar el objeto. Error: {e}")

# --------------------
# FUNCIONES AUXILIARES
# --------------------
def update_state(user_id, new_state):
    """
    Actualiza el estado del usuario.
    """
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['State'] = state

# Arrancar el bot
bot.polling()
