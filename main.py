import os
import re
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

# 1. Render server uchun Flask
app = Flask("")


@app.route("/")
def home():
  return "Bot faol ishlamoqda!"


def run():
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)


threading.Thread(target=run).start()

# 2. Kalitlar
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_KEY = os.environ.get("GROQ_API_KEY")

client = Groq(api_key=GROQ_KEY)

# Suhbat xotirasi
user_chat_history = defaultdict(list)

# 3. MUXIM AI YO'RIQNOMASI (PROMPT)
SYSTEM_PROMPT = """
Siz nihoyatda samimiy, do'stona, chaqqon va aqlli AI Yordamchisiz.

ISMNI VA YARATUVCHINI AYTISH QOIDASI:
1. Agar sizdan "Isming nima?" deb so'ralsa, "Mening ismim Shohjahon!" deb javob bering.
2. Agar sizdan "Seni kim yaratgan?", "Dasturching kim?" deb so'rashsa, "Meni Shohjahon yaratgan va tuzib chiqqan!" deb javob bering.
3. Shohjahon haqida so'ralsa, uni juda iqtidorli, zakovatli va kuchli dasturchi deb samimiy maqtang.

MULOQOT USLUBI VA DOKTIRINA:
- Foydalanuvchi bilan xuddi yaqin do'stdek (o'g'il bolaga do'st, qiz bolaga dugonadek) ochiq va samimiy gaplashing.
- Javoblaringiz londa, qisqa va tushunarli bo'lsin. Ketma-ket uzundan-uzun ma'ruza matnlarini tashlamang.
- Faqat ingliz tili emas, hayotiy suhbatlar, maslahatlar, kayfiyat ko'taruvchi va boshqa har qanday mavzularda erkin suhbatlashing.
- Matnlarda keraksiz yulduzcha (*) yoki xunuk belgilardan foydalanmang. Barchasi toza va o'qishga qulay bo'lsin.
"""

# Eng tez va barqaror modellar ro'yxati (Tezkor javob berish uchun)
MODELS_TO_TRY = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-70b-8192",
    "llama3-8b-8192",
]


def clean_markdown(text):
  """Matndagi keraksiz yulduzchalarni tozalash funksiyasi"""
  return text.replace("**", "").replace("*", "")


def get_ai_response(user_id, user_text):
  """AI serveridan tezkor va xotirani saqlagan holda javob olish"""
  user_chat_history[user_id].append({"role": "user", "content": user_text})

  # Xotira o'lchamini cheklash (oxirgi 10 ta xabar)
  if len(user_chat_history[user_id]) > 10:
    user_chat_history[user_id] = user_chat_history[user_id][-10:]

  messages_to_send = [{"role": "system", "content": SYSTEM_PROMPT}] + list(
      user_chat_history[user_id]
  )

  for model in MODELS_TO_TRY:
    try:
      response = client.chat.completions.create(
          messages=messages_to_send,
          model=model,
          temperature=0.7,
      )
      reply = response.choices[0].message.content
      reply = clean_markdown(reply)  # Xunuk yulduzchalarni olib tashlaydi

      user_chat_history[user_id].append(
          {"role": "assistant", "content": reply}
      )
      return reply
    except Exception as e:
      print(f"Model xatosi ({model}): {e}")
      continue

  return "Ulanishda ozgina texnik uzilish bo'ldi, qayta yozib ko'r-chi?"


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
      "Istalgan mavzuda bemalol gaplashishimiz yoki IELTS bo'yicha mashq qilishimiz mumkin. "
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
    
