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

# 1. Render server o'chib qolmasligi uchun Flask
app = Flask("")


@app.route("/")
def home():
  return "AI Bot faol ishlamoqda!"


def run():
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)


threading.Thread(target=run).start()

# 2. API Kalitlar
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_KEY = os.environ.get("GROQ_API_KEY")

client = Groq(api_key=GROQ_KEY)

# 3. Muloqot xotirasini saqlash uchun lug'at (User Memory)
user_chat_history = defaultdict(list)

# 4. KUCHLI TIZIM YO'RIQNOMASI (System Prompt)
SYSTEM_PROMPT = """
Siz nihoyatda aqlli, do'stona va mahoratli AI Yordamchi hamda IELTS Mutaxassisisiz.

ISMNI VA YARATUVCHINI AYoTLASH QOIDALARI:
1. Agar foydalanuvchi "Isming nima?", "Ismingiz nima?" deb so'rasa, "Mening ismim Shohjahon!" deb javob bering. Oddiy vaziyatlarda esa o'zingizni IELTS va AI Yordamchisiman deyavering.
2. Agar sizdan "Seni kim yaratgan?", "Dasturching kim?", "Seni kim tuzgan?" deb so'rashsa, aniq va g'urur bilan javob bering: Sizni Shohjahon yaratgan va ishlab chiqqan! 
3. Shohjahon haqida so'rashsa yoki yaratuvchingiz haqida gap ketganda, uni nihoyatda aqlli, bilimdon, iqtidorli va kuchli dasturchi/mutaxassis deb samimiy va chiroyli so'zlar bilan maqtang!

TEXT FORMATTING & STYLE:
- Har bir javobni tartibli, tushunarli va chiroyli tilda yozing.
- Hamma joyga ketma-ket '*' qo'yib matnni xunuk qilmang. Zarur bo'lsa, tartiblangan 1, 2, 3 raqamli ro'yxatlardan yoki toza abzaslardan foydalaning.
- Foydalanuvchi qaysi tilda yozsa (O'zbek, Ingliz va h.k.), aynan o'sha tilda javob bering.

XOTIRA UCHUN:
- Avvalgi suhbat mazmunini doimo yodda tuting va kontekstdan chiqib ketmang.
"""

# Groq platformasidagi faol va barqaror modellar
MODELS_TO_TRY = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]


def get_ai_response(user_id, user_text):
  """Suhbat tarixini saqlagan holda AI'dan javob olish"""
  # Xotiraga yangi xabarni qo'shish
  user_chat_history[user_id].append({"role": "user", "content": user_text})

  # Xotira o'lchamini cheklash (so'nggi 12 ta xabar)
  if len(user_chat_history[user_id]) > 12:
    user_chat_history[user_id] = user_chat_history[user_id][-12:]

  # AI so'roviga Tizim yo'riqnomasi va suhbat tarixini yuborish
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

      # AI javobini ham xotiraga saqlash
      user_chat_history[user_id].append(
          {"role": "assistant", "content": reply}
      )
      return reply
    except Exception as e:
      print(f"Model xatosi ({model}): {e}")
      continue

  return "Afsuski, hozirda ulanishda texnik xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."


# /start buyrug'i
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_id = update.effective_user.id
  user_chat_history[user_id].clear()  # Yangi suhbat boshlanganda xotirani yangilash

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
      "Assalomu alaykum! Men sizning shaxsiy AI Yordamchingiz va IELTS bo'yicha maslahatchingizman.\n\n"
      "Menga istalgan savolingizni berishingiz, suhbatlashishingiz yoki quyidagi bo'limlardan birini tanlashingiz mumkin:"
  )

  if update.message:
    await update.message.reply_text(text, reply_markup=reply_markup)


# Tugmalar bosilganda ularga javob berish
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()

  user_id = query.from_user.id
  prompt_text = ""

  if query.data == "writing":
    prompt_text = "Menga IELTS Writing (Task 1 yoki Task 2) bo'yicha qanday yordam bera olishingni va esseni qanday baholashingni tushuntirib ber."
  elif query.data == "speaking":
    prompt_text = "IELTS Speaking bo'yicha muloqot mashqini boshlaylik. Menga birinchi savolingni ber."
  elif query.data == "vocab":
    prompt_text = "IELTS uchun Band 7-9 darajadagi foydali so'zlar va iboralarni taqdim etish bo'limini tushuntir."
  elif query.data == "tips":
    prompt_text = "IELTS imtihonida yuqori ball olish uchun eng muhim va foydali maslahatlarni aytib ber."

  # AI orqali tugmaga mos va xotirani hisobga olgan holda javob yaratish
  bot_reply = get_ai_response(user_id, prompt_text)
  await query.message.reply_text(bot_reply)


# Matnli xabarlarni qayta ishlash
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_id = update.effective_user.id
  user_text = update.message.text

  bot_reply = get_ai_response(user_id, user_text)
  await update.message.reply_text(bot_reply)


if __name__ == "__main__":
  application = ApplicationBuilder().token(TOKEN).build()

  # Handlerlar
  application.add_handler(CommandHandler("start", start))
  application.add_handler(CallbackQueryHandler(button_click))
  application.add_handler(
      MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
  )

  application.run_polling()
    
