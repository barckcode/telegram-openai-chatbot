import os
import telebot
import requests
import tempfile
from openai import OpenAI

telegram_token = os.getenv("TELEGRAM_API_KEY")
bot = telebot.TeleBot(telegram_token, parse_mode=None)

openai_token = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_token)

conversations = {}
behavior = "I would like you to be an assistant that can, based on a name, accurately find and explain the meaning of this name across different cultures, religions, and historical periods. You should be able to provide insightful details about the origin, cultural significance, and any variations of the name. This includes how the meaning or perception of the name might have evolved over time and any notable figures who have borne the name. Your responses should be informative, providing a comprehensive understanding of the name’s background and its relevance in various contexts."

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	print(message.chat.id)
	bot.reply_to(message, "¡Hola! dime cuál es tu nombre y buscaré cuál es su origen y significado a lo largo de las diferentes culturas, religiones y épocas del mundo")
	conversations[message.chat.id] = [
		{"role": "system", "content": f"{behavior}"}
	]


@bot.message_handler(func=lambda message: True)
def handle_message(message):
	chat_id = message.chat.id
	if chat_id not in conversations:
		conversations[chat_id] = [
		{"role": "system", "content": f"{behavior}"}
		]
	conversations[chat_id].append({"role": "user", "content": message.text})
	response = client.chat.completions.create(
		model="gpt-3.5-turbo-0125",
		messages=conversations[chat_id]
	)
	ai_response = response.choices[0].message.content
	conversations[chat_id].append({"role": "assistant", "content": ai_response})
	bot.reply_to(message, ai_response)


@bot.message_handler(content_types=['voice'])
def handle_audio(message):
	# Descargar el archivo de audio
	file_info = bot.get_file(message.voice.file_id)
	file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(telegram_token, file_info.file_path))

	# Guardar el archivo de audio en un archivo temporal
	with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp:
		temp.write(file.content)
		temp_file_name = temp.name

	# Transcribir el audio a texto
	with open(temp_file_name, "rb") as audio_file:
		transcription = client.audio.transcriptions.create(
		model="whisper-1",
		file=audio_file,
		response_format="text"
		)

	# Añadir la transcripción a la conversación
	if message.chat.id not in conversations:
		conversations[message.chat.id] = [
		{"role": "system", "content": f"{behavior}"}
		]
	conversations[message.chat.id].append({"role": "user", "content": transcription})

	# Generar una respuesta
	response = client.chat.completions.create(
		model="gpt-3.5-turbo-0125",
		messages=conversations[message.chat.id]
	)
	ai_response = response.choices[0].message.content
	conversations[message.chat.id].append({"role": "assistant", "content": ai_response})

	# Enviar la respuesta al usuario
	bot.reply_to(message, ai_response)


bot.infinity_polling()
