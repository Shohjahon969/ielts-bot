import os
import threading
from flask import Flask
from groq import Groq
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# 1. Render serverini uxlab qolmasligi uchun Flask
app = Flask("")


@app.route("/")
def home():
  return "Bot ishlamoqda!"


def run():
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)


threading.Thread(target=run).start()

# 2. API Kalitlar
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_KEY = os.environ.get("GROQ_API_KEY")

client = Groq(api_key=GROQ_KEY)

SYSTEM_PROMPT = (
    "You are an expert IELTS Tutor AI. Help users with IELTS Speaking, Writing,"
    " Reading, and Listening. Evaluate their text, give Band Scores, correct"
    " grammar, and suggest better vocabulary. Be polite and encouraging."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  keyboard = [
      [
          InlineKeyboardButton("📝 Writing Check", callback_data="writing"),
          InlineKeyboardButton("🗣 Speaking Practice", callback_data="speaking"),
      ],
      [
          InlineKeyboardButton("📚 Vocabulary Helper", callback_data="vocab"),
          InlineKeyboardButton("💡 IELTS Tips", callback_data="tips"),
      ],
  ]
  reply_markup = InlineKeyboardMarkup(keyboard)

  text = (
      "👋 **Salom! Men sizning shaxsiy IELTS AI Yordamchingizman.**\n\n"
      "Quyidagi bo'limlardan birini tanlang yoki istalgan IELTS'ga oid"
      " savolingizni/esseingizni to'g'ridan-to'g'ri yuboring!"
  )

  if update.message:
    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=reply_markup
    )


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()

  if query.data == "writing":
    await query.message.reply_text(
        "✍️ **IELTS Writing:** Esseingizni yoki xatingizni shu yerga yuboring."
        " Men uni tekshirib, Band Score beraman va xatolaringizni to'g'rilayman!"
    )
  elif query.data == "speaking":
    await query.message.reply_text(
        "🗣 **IELTS Speaking:** Menga istalgan mavzuda matn yuboring yoki savol"
        " so'rang, birga muloqot qilamiz va nutqingizni yaxshilaymiz!"
    )
  elif query.data == "vocab":
    await query.message.reply_text(
        "📚 **Vocabulary:** Qaysi mavzuda (masalan: Environment, Education,"
        " Technology) Band 7-9 so'zlar kerak? Mavzuni yozing!"
    )
  elif query.data == "tips":
    await query.message.reply_text(
        "💡 **IELTS Tips:** Qaysi bo'lim bo'yicha maslahat kerak? (Writing,"
        " Speaking, Reading, Listening) Yozib qoldiring!"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_text = update.message.text

  try:
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        model="llama-3.3-70b-versatile",  # Hozirda Groq'dagi yagona va asosiy faol model
    )
    bot_reply = response.choices[0].message.content
    await update.message.reply_text(bot_reply)
  except Exception as e:
    await update.message.reply_text(
        f"⚠️ Xatolik yuz berdi:\n\n{e}\n\nIltimos, Render'dagi GROQ_API_KEY to'g'riligini tekshiring."
    )


if __name__ == "__main__":
  application = ApplicationBuilder().token(TOKEN).build()

  application.add_handler(CommandHandler("start", start))
  application.add_handler(CallbackQueryHandler(button_click))
  application.add_handler(
      MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
  )

  application.run_polling()
    
