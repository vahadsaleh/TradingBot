import os
import json
import requests
import telegram
from binance.client import Client
from telegram.ext import Updater, CommandHandler

# تحميل بيانات API من بيئة GitHub
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# إعداد Binance API
client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)

# إعداد بوت تيليجرام
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

# ملف تخزين بيانات المستخدمين
CONFIG_FILE = "config.json"

# تحميل بيانات المشتركين
def load_users():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    return {}

# حفظ بيانات المشتركين
def save_users(users):
    with open(CONFIG_FILE, "w") as file:
        json.dump(users, file)

# قائمة المشتركين
users = load_users()

# أمر بدء البوت
def start(update, context):
    user_id = str(update.message.chat_id)
    
    if user_id in users:
        update.message.reply_text("✅ أنت مشترك بالفعل! يمكنك استخدام الأوامر.")
    else:
        update.message.reply_text("👋 مرحبًا! هذا بوت تداول تلقائي.\n💰 الاشتراك مقابل 10 USDT.\n🔹 أرسل المبلغ إلى عنوان Binance التالي:\n`YOUR_BINANCE_ADDRESS`\n📤 بعد الدفع، أرسل `/verify` للتحقق.")

# أمر التحقق من الدفع
def verify(update, context):
    user_id = str(update.message.chat_id)

    users[user_id] = {"subscribed": True}
    save_users(users)
    update.message.reply_text("✅ تم تفعيل اشتراكك! استخدم /trade لبدء التداول.")

# أمر بدء التداول
def trade(update, context):
    user_id = str(update.message.chat_id)
    
    if user_id not in users or not users[user_id]["subscribed"]:
        update.message.reply_text("🚫 يجب عليك الاشتراك أولًا! استخدم /start.")
        return
    
    symbol = "BTCUSDT"
    price = float(client.get_symbol_ticker(symbol=symbol)["price"])
    
    if price < 40000:  # مثال: شراء إذا كان السعر أقل من 40,000$
        order = client.order_market_buy(symbol=symbol, quantity=0.001)
        update.message.reply_text(f"✅ تم شراء {symbol} بسعر {price}!")
    elif price > 45000:  # مثال: بيع إذا كان السعر أعلى من 45,000$
        order = client.order_market_sell(symbol=symbol, quantity=0.001)
        update.message.reply_text(f"🚀 تم بيع {symbol} بسعر {price}!")
    else:
        update.message.reply_text(f"📊 السعر الحالي لـ {symbol}: {price}.\nلا يوجد تداول الآن.")

# إعداد أوامر تيليجرام
updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("verify", verify))
dp.add_handler(CommandHandler("trade", trade))

# تشغيل البوت
updater.start_polling()
updater.idle()
