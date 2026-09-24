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

# 1. Render server o'chmasligi uchun Flask veb-serveri
app = Flask("")


@app.route("/")
def home():
  return "Bot faol va ishlamoqda!"


def run():
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)


threading.Thread(target=run).start()

# 2. Telegram va Groq API kalitlari
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_KEY = os.environ.get("GROQ_API_KEY")

client = Groq(api_key=GROQ_KEY)

# Bot uchun tizim yo'riqnomasi (System Prompt)
SYSTEM_PROMPT = """
You are a helpful, smart AI assistant and IELTS Tutor.
RULES:
1. ALWAYS reply in the exact same language the user uses. If they speak Uzbek, respond in natural Uzbek.
2. Be friendly and conversational.
3. If they ask for IELTS help (Writing, Speaking, Vocab, Tips), provide expert guidance.
"""

# Groq platformasida ishlaydigan aniq va bepul modellar ro'yxati
AVAILABLE_MODELS = [
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]


def ask_groq(user_text):
  """Groq API orqali modellarni ketma-ket sinab ko'rib javob oladi."""
  for model_name in AVAILABLE_MODELS:
    try:
      response = client.chat.completions.create(
          messages=[
              {"role": "system", "content": SYSTEM_PROMPT},
              {"role": "user", "content": user_text},
          ],
          model=model_name,
      )
      return response.choices[0].message.content
    except Exception:
      continue
  return None


# /start komutu bosilganda ishlaydigan funksiya
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
      "👋 **Salom! Men sizning shaxsiy AI Yordamchingizman.**\n\n"
      "Istalgan savolingizni yozing yoki quyidagi bo'limlardan birini tanlang:"
  )

  if update.message:
    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=reply_markup
    )


# Tugmalar bosilganda ishlaydigan funksiya
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()

  if query.data == "writing":
    await query.message.reply_text(
        "✍️ **IELTS Writing:** Esseingizni yuboring, uni tekshirib Band Score"
        " beraman va xatolarni to'g'rilayman!"
    )
  elif query.data == "speaking":
    await query.message.reply_text(
        "🗣 **IELTS Speaking:** Menga matn yozing yoki savol bering, birgalikda"
        " mashq qilamiz!"
    )
  elif query.data == "vocab":
    await query.message.reply_text(
        "📚 **Vocabulary:** Qaysi mavzuda (Education, Technology va h.k.) Band"
        " 7-9 so'zlar kerak?"
    )
  elif query.data == "tips":
    await query.message.reply_text(
        "💡 **IELTS Tips:** Qaysi bo'lim bo'yicha maslahat kerak? (Writing,"
        " Speaking, Reading, Listening)"
    )


# Foydalanuvchi xabar yozganda ishlaydigan funksiya
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_text = update.message.text

  # Süniy intelektga so'rov yuborish
  bot_reply = ask_groq(user_text)

  if bot_reply:
    await update.message.reply_text(bot_reply)
  else:
    await update.message.reply_text(
        "⚠️ Hozircha AI serveriga ulanishda texnik muammo bo'ldi. Iltimos,"
        " Render'dagi GROQ_API_KEY kalitingiz to'g'riligini tekshiring."
    )


if __name__ == "__main__":
  application = ApplicationBuilder().token(TOKEN).build()

  # Handlerlarni qo'shish
  application.add_handler(CommandHandler("start", start))
  application.add_handler(CallbackQueryHandler(button_click))
  application.add_handler(
      MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
  )

  application.run_polling()
    
