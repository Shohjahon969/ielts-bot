import os
import threading
from flask import Flask
from groq import Groq
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# 1. Render o'chib qolmasligi uchun Flask veb-serveri
app = Flask("")


@app.route("/")
def home():
  return "Bot ishlamoqda!"


def run():
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)


threading.Thread(target=run).start()

# 2. Telegram Bot va Groq AI qismi
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_KEY = os.environ.get("GROQ_API_KEY")

client = Groq(api_key=GROQ_KEY)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text(
      "Salom! Men sizning IELTS AI turingizaman. Savolingizni yuboring!"
  )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_text = update.message.text
  response = client.chat.completions.create(
      messages=[{"role": "user", "content": user_text}],
      model="llama3-8b-8192",
  )
  bot_reply = response.choices[0].message.content
  await update.message.reply_text(bot_reply)


if __name__ == "__main__":
  application = ApplicationBuilder().token(TOKEN).build()

  application.add_handler(CommandHandler("start", start))
  application.add_handler(
      MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
  )

  application.run_polling()
  
