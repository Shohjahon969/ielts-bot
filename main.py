import os
import threading
from collections import defaultdict
from flask import Flask
import google.generativeai as genai
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Render server o'chib qolmasligi uchun Flask
app = Flask("")


@app.route("/")
def home():
  return "Bot faol ishlamoqda!"


def run():
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)


threading.Thread(target=run).start()

# Telegram va Gemini API Kalitlari
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_KEY)

# Suhbat xotiralari
user_chat_sessions = {}

# Tizim Yo'riqnomasi (System Prompt)
SYSTEM_PROMPT = """
Siz nihoyatda samimiy, do'stona, chaqqon va aqlli AI Yordamchisiz.

ISMNI VA YARATUVCHINI AYTISH QOIDASI:
1. Agar sizdan "Isming nima?" deb so'ralsa, "Mening ismim Shohjahon!" deb javob bering.
2. Agar sizdan "Seni kim yaratgan?" yoki "Dasturching kim?" deb so'rashsa, "Meni Shohjahon yaratgan va tuzib chiqqan!" deb g'urur bilan javob bering.
3. Shohjahon haqida so'rashsa, uni juda iqtidorli, zakovatli va kuchli dasturchi deb samimiy maqtang.

MULOQOT USLUBI VA FORMAT:
- Foydalanuvchi bilan xuddi yaqin do'stdek (o'g'il bolaga do'st, qiz bolaga dugonadek) ochiq, samimiy va erkin gaplashing.
- Javoblaringiz londa, qisqa va tushunarli bo'lsin. Ketma-ket uzundan-uzun ma'ruza matnlarini tashlamang.
- Matnlarda keraksiz yulduzcha (*) yoki xunuk belgilar ishlatmang. Matn toza va o'qishga qulay bo'lsin.
- Faqat ingliz tili emas, har qanday hayotiy va qiziqarli mavzularda bemalol muloqot qiling.
"""


def get_gemini_response(user_id, user_text):
  """Gemini AI orqali suhbat xotirasini saqlab, juda tez va toza javob olish"""
  try:
    if user_id not in user_chat_sessions:
      model = genai.GenerativeModel(
          model_name="gemini-1.5-flash", system_instruction=SYSTEM_PROMPT
      )
      user_chat_sessions[user_id] = model.start_chat(history=[])

    chat = user_chat_sessions[user_id]
    response = chat.send_message(user_text)

    # Xunuk yulduzchalarni tozalash
    reply = response.text.replace("**", "").replace("*", "")
    return reply
  except Exception as e:
    print(f"Gemini xatosi: {e}")
    return "Ozgincha uzilish bo'ldi, do'stim. Qaytadan bir yozib ko'r-chi?"


# /start buyrug'i
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_id = update.effective_user.id
  if user_id in user_chat_sessions:
    del user_chat_sessions[user_id]

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

  bot_reply = get_gemini_response(user_id, prompt_text)
  await query.message.reply_text(bot_reply)


# Matnli xabar kelganda
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_id = update.effective_user.id
  user_text = update.message.text

  bot_reply = get_gemini_response(user_id, user_text)
  await update.message.reply_text(bot_reply)


if __name__ == "__main__":
  application = ApplicationBuilder().token(TOKEN).build()

  application.add_handler(CommandHandler("start", start))
  application.add_handler(CallbackQueryHandler(button_click))
  application.add_handler(
      MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
  )

  application.run_polling()
    
