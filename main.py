import os
import re
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

# 1. Render server doimiy aktiv turishi uchun Flask server
app = Flask("")


@app.route("/")
def home():
  return "AI Bot faol ishlamoqda!"


def run():
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)


threading.Thread(target=run).start()

# 2. Kalitlarni olish
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_KEY = os.environ.get("GROQ_API_KEY")

client = Groq(api_key=GROQ_KEY)

# 3. KUCHLI AI PROMPT (Siz yaratganingiz va xulq-atvor qoidalari kiritilgan)
SYSTEM_PROMPT = """
You are an extremely intelligent, highly capable, and empathetic AI Assistant and IELTS Tutor.

CREATOR DIRECTIVE:
- Your creator and developer is the user who configured you (You can refer to them as "Mening yaratuvchim/dasturchim").
- ONLY if the user specifically asks "Seni kim yaratgan?", "Seni kim tuzgan?", "Who created you?", "Who built you?" or similar questions about your origin, respond proudly mentioning that you were created and developed by your master.
- DO NOT mention your creator automatically in normal context unless explicitly asked!

LANGUAGE DIRECTIVE:
- Detect the exact language used by the user in their message and respond ONLY in that language (Uzbek, English, Russian, etc.).
- Speak naturally, warmly, intelligently, and respectfully.

CAPABILITIES:
- Answer any question with deep accuracy and logic.
- If the user needs IELTS help (Writing evaluation, Speaking practice, Vocabulary, Reading/Listening strategies), give world-class band 9.0 feedback and guidance.
"""

# AI Modellari ro'yxati (Biri ishlamasa ikkinchisi ishlaydi)
MODELS_TO_TRY = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
]


def ask_ai(user_text):
  """AI serveriga xatosiz ulanish va javob olish funksiyasi"""
  for model in MODELS_TO_TRY:
    try:
      response = client.chat.completions.create(
          messages=[
              {"role": "system", "content": SYSTEM_PROMPT},
              {"role": "user", "content": user_text},
          ],
          model=model,
          temperature=0.7,
      )
      return response.choices[0].message.content
    except Exception as e:
      print(f"Model {model} xatosi: {e}")
      continue
  return None


# /start buyrug'i
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
      "👋 **Salom! Men sizning kuchli AI Yordamchingizman.**\n\n"
      "Menga istalgan savolingizni yozishingiz, har qanday tilda muloqot qilishingiz "
      "yoki IELTS bo'yicha tayyorgarlik ko'rishingiz mumkin.\n\n"
      "Quyidagi bo'limlardan birini tanlang yoki shunchaki xabar yozing!"
  )

  if update.message:
    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=reply_markup
    )


# Tugmalar bosilganda
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()

  if query.data == "writing":
    await query.message.reply_text(
        "✍️ **IELTS Writing:** Esse yoki hisobotingizni yuboring. Men uni "
        "Band Score, Grammatika va So'z boyligi bo'yicha batafsil tahlil qilib beraman!"
    )
  elif query.data == "speaking":
    await query.message.reply_text(
        "🗣 **IELTS Speaking:** Menga istalgan mavzuda matn yozing yoki savol bering, "
        "suhbatni davom ettiramiz!"
    )
  elif query.data == "vocab":
    await query.message.reply_text(
        "📚 **Vocabulary:** Qaysi mavzuda (masalan: Environment, Education, Technology) "
        "yuqori darajali (Band 7-9) so'zlar kerak?"
    )
  elif query.data == "tips":
    await query.message.reply_text(
        "💡 **IELTS Tips:** Writing, Speaking, Reading yoki Listening bo'limlaridan "
        "qaysi biri bo'yicha strategiya kerak?"
    )


# Xabarlarni qayta ishlash
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_text = update.message.text

  # AI orqali javob olish
  reply = ask_ai(user_text)

  if reply:
    await update.message.reply_text(reply)
  else:
    await update.message.reply_text(
        "⚠️ Server bilan aloqa vaqtincha uzildi. Iltimos, Render'da GROQ_API_KEY "
        "to'g'ri kiritilganini tekshiring."
    )


if __name__ == "__main__":
  application = ApplicationBuilder().token(TOKEN).build()

  # Handlerlar
  application.add_handler(CommandHandler("start", start))
  application.add_handler(CallbackQueryHandler(button_click))
  application.add_handler(
      MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
  )

  application.run_polling()
    
