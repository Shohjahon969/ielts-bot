import os
import threading
from collections import defaultdict
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

# Render uchun server
app = Flask("")


@app.route("/")
def home():
  return "Bot faol ishlamoqda!"


def run():
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)


threading.Thread(target=run).start()

# Kalitlar
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_KEY = os.environ.get("GROQ_API_KEY")

client = Groq(api_key=GROQ_KEY)

# Muloqot xotirasi
user_chat_history = defaultdict(list)

SYSTEM_PROMPT = """
Siz nihoyatda samimiy, do'stona, chaqqon va aqlli AI Yordamchisiz.

ISMNI VA YARATUVCHINI AYTISH QOIDASI:
1. Agar sizdan "Isming nima?" deb so'ralsa, "Mening ismim Shohjahon!" deb javob bering.
2. Agar sizdan "Seni kim yaratgan?" yoki "Dasturching kim?" deb so'rashsa, "Meni Shohjahon yaratgan va tuzib chiqqan!" deb g'urur bilan javob bering.
3. Shohjahon haqida so'rashsa, uni juda iqtidorli, zakovatli va kuchli dasturchi deb samimiy maqtang.

MULOQOT USLUBI:
- Foydalanuvchi bilan xuddi yaqin do'stdek ochiq va samimiy gaplashing.
- Javoblaringiz londa, qisqa va tushunarli bo'lsin.
- Matnlarda keraksiz yulduzcha (*) yoki xunuk belgilar ishlatmang. Matn toza bo'lsin.
"""

# Groq'da hozir HAKIQATAN ISHLAYDIGAN eng zo'r modellar:
FREE_MODELS = [
    "llama-3.3-70b-versatile",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
]


def clean_text(text):
  return text.replace("**", "").replace("*", "")


def get_ai_response(user_id, user_text):
  user_chat_history[user_id].append({"role": "user", "content": user_text})

  if len(user_chat_history[user_id]) > 10:
    user_chat_history[user_id] = user_chat_history[user_id][-10:]

  messages_to_send = [{"role": "system", "content": SYSTEM_PROMPT}] + list(
      user_chat_history[user_id]
  )

  last_err = ""
  for model in FREE_MODELS:
    try:
      response = client.chat.completions.create(
          messages=messages_to_send, model=model, temperature=0.7
      )
      reply = response.choices[0].message.content
      reply = clean_text(reply)

      user_chat_history[user_id].append(
          {"role": "assistant", "content": reply}
      )
      return reply
    except Exception as e:
      last_err = str(e)
      continue

  return f"Groq Xatosi: {last_err[:100]}"


# /start buyrug'i
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_id = update.effective_user.id
  user_chat_history[user_id].clear()

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
      "Salom! Men sizning shaxsiy AI Yordamchingizman.\n\n"
      "Istalgan mavzuda bemalol gaplashishimiz mumkin. "
      "Quyidagi tugmalardan birini tanlang yoki shunchaki xabar yozing!"
  )

  if update.message:
    await update.message.reply_text(text, reply_markup=reply_markup)


# Tugmalar bosilganda
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()

  user_id = query.from_user.id
  prompt_text = ""

  if query.data == "writing":
    prompt_text = (
        "IELTS Writing boyicha qanday yordam bera olasan? Qisqa tushuntir."
    )
  elif query.data == "speaking":
    prompt_text = "IELTS Speaking boyicha birgalikda muloqot qilaylik, menga bitta savol ber."
  elif query.data == "vocab":
    prompt_text = (
        "IELTS uchun foydali so'zlar bo'limi haqida qisqa ma'lumot ber."
    )
  elif query.data == "tips":
    prompt_text = "IELTS imtihoni uchun eng muhim 3 ta maslahatni aytib ber."

  bot_reply = get_ai_response(user_id, prompt_text)
  await query.message.reply_text(bot_reply)


# Matnli xabar kelganda
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_id = update.effective_user.id
  user_text = update.message.text

  bot_reply = get_ai_response(user_id, user_text)
  await update.message.reply_text(bot_reply)


if __name__ == "__main__":
  application = ApplicationBuilder().token(TOKEN).build()

  application.add_handler(CommandHandler("start", start))
  application.add_handler(CallbackQueryHandler(button_click))
  application.add_handler(
      MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
  )

  application.run_polling()
        
