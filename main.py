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

# 1. Server o'chmasligi uchun Flask veb-serveri
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

# Moslashuvchan va do'stona System Prompt
SYSTEM_PROMPT = """
You are a friendly, intelligent AI assistant and IELTS Tutor.
RULES:
1. ALWAYS respond in the EXACT same language as the user's message. If the user writes in Uzbek, reply in natural Uzbek. If in English, reply in English.
2. Be conversational, natural, and friendly. Do NOT force or push the user into IELTS topics if they are just chatting or asking general questions.
3. If the user asks about general topics, answer naturally like a helpful friend.
4. If the user asks for IELTS practice, writing evaluation, grammar corrections, or speaking help, give expert IELTS guidance.
"""

# Hozirda Groq'da faol bo'lgan modellar
MODELS_TO_TRY = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]


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
      "👋 **Salom! Men sizning AI Yordamchingizman.**\n\n"
      "Istalgan mavzuda bemalol suhbatlashishimiz yoki IELTS bo'yicha mashq qilishimiz mumkin. "
      "Quyidagi tugmalardan birini tanlang yoki menga shunchaki xabar yozing!"
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
        "✍️ **IELTS Writing:** Esseingizni yuboring, uni tekshirib beraman!"
    )
  elif query.data == "speaking":
    await query.message.reply_text(
        "🗣 **IELTS Speaking:** Istalgan mavzuda inglizcha gaplashamiz!"
    )
  elif query.data == "vocab":
    await query.message.reply_text(
        "📚 **Vocabulary:** Qaysi mavzuda yangi so'zlar kerak?"
    )
  elif query.data == "tips":
    await query.message.reply_text(
        "💡 **IELTS Tips:** Qaysi bo'lim bo'yicha maslahat kerak?"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_text = update.message.text
  bot_reply = None

  for model_name in MODELS_TO_TRY:
    try:
      response = client.chat.completions.create(
          messages=[
              {"role": "system", "content": SYSTEM_PROMPT},
              {"role": "user", "content": user_text},
          ],
          model=model_name,
      )
      bot_reply = response.choices[0].message.content
      break
    except Exception:
      continue

  if bot_reply:
    await update.message.reply_text(bot_reply)
  else:
    await update.message.reply_text(
        "⚠️ Xatolik yuz berdi. Iltimos, bir ozdan so'ng qayta urinib ko'ring."
    )


if __name__ == "__main__":
  application = ApplicationBuilder().token(TOKEN).build()

  application.add_handler(CommandHandler("start", start))
  application.add_handler(CallbackQueryHandler(button_click))
  application.add_handler(
      MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
  )

  application.run_polling()
    
