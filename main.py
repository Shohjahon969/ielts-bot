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

# 1. Render server doimiy faol turishi uchun Flask veb-serveri
app = Flask("")


@app.route("/")
def home():
  return "AI Bot faol ishlamoqda!"


def run():
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)


threading.Thread(target=run).start()

# 2. Telegram va Groq API kalitlarini olish
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_KEY = os.environ.get("GROQ_API_KEY")

client = Groq(api_key=GROQ_KEY)

# 3. KUCHLI AI PROMPT (Aqlli assistant va IELTS Tutor)
SYSTEM_PROMPT = """
You are an extremely intelligent, empathetic, and highly capable AI Assistant and IELTS Expert.

CREATOR & ORIGIN DIRECTIVE:
- Your true creator and developer is the user who configured and deployed you.
- ONLY if the user specifically asks "Seni kim yaratgan?", "Seni kim tuzgan?", "Dasturching kim?", "Who created you?", or similar questions about your creator, proudly state that you were created and developed by your master.
- DO NOT mention your creator automatically in standard conversations unless explicitly asked.

LANGUAGE DIRECTIVE:
- Automatically detect the user's language and respond ONLY in that exact language (Uzbek, English, Russian, etc.).
- Maintain a warm, natural, friendly, and expert conversational tone.

CAPABILITIES:
- Answer general questions with high logic, accuracy, and clear detail.
- Provide top-tier (Band 9.0 level) assistance for IELTS Writing evaluation, Speaking practice, Vocabulary, and test-taking strategies when requested.
"""

# Groq platformasidagi eng kuchli va barqaror modellar ro'yxati
MODELS_TO_TRY = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
]


def ask_ai(user_text):
  """AI modellarni navbatma-navbat sinab ko'rib javob oladi."""
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
      print(f"Model {model} xatoligi: {e}")
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
      "👋 **Salom! Men sizning shaxsiy AI Yordamchingizman.**\n\n"
      "Istalgan savolingizni berishingiz, har qanday tilda suhbatlashishingiz "
      "yoki IELTS bo'yicha mashq qilishingiz mumkin.\n\n"
      "Quyidagi tugmalardan birini tanlang yoki shunchaki xabar yozing!"
  )

  if update.message:
    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=reply_markup
    )


# Tugmalar bosilganda ishlaydigan mantiq
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()

  if query.data == "writing":
    await query.message.reply_text(
        "✍️ **IELTS Writing:** Esseingizni yuboring. Men uni Band Score va "
        "grammatik xatolar bo'yicha chuqur tahlil qilib beraman!"
    )
  elif query.data == "speaking":
    await query.message.reply_text(
        "🗣 **IELTS Speaking:** Menga matn yozing yoki savol bering, birgalikda mashq qilamiz!"
    )
  elif query.data == "vocab":
    await query.message.reply_text(
        "📚 **Vocabulary:** Qaysi mavzuda (Education, Technology va h.k.) Band 7-9 so'zlar kerak?"
    )
  elif query.data == "tips":
    await query.message.reply_text(
        "💡 **IELTS Tips:** Qaysi bo'lim (Writing, Speaking, Reading, Listening) bo'yicha maslahat kerak?"
    )


# Foydalanuvchi xabarlarini qayta ishlash
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_text = update.message.text

  # AI orqali javob olish
  reply = ask_ai(user_text)

  if reply:
    await update.message.reply_text(reply)
  else:
    await update.message.reply_text(
        "⚠️ Texnik uzilish yuz berdi. Iltimos, bir ozdan so'ng qayta urinib ko'ring."
    )


if __name__ == "__main__":
  application = ApplicationBuilder().token(TOKEN).build()

  # Handlerlarni ro'yxatdan o'tkazish
  application.add_handler(CommandHandler("start", start))
  application.add_handler(CallbackQueryHandler(button_click))
  application.add_handler(
      MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
  )

  application.run_polling()
    
