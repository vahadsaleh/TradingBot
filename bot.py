import os
import json
import requests
import telegram
from binance.client import Client
from telegram.ext import Updater, CommandHandler
from solana.rpc.api import Client as SolanaClient
from solana.publickey import PublicKey

# 🔹 تحميل بيانات API من Secrets في GitHub
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PHANTOM_WALLET_ADDRESS = "YOUR_SOL_WALLET_ADDRESS"  # ضع عنوان محفظتك هنا
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"

# 🔹 إعداد Binance API
binance_client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)

# 🔹 إعداد Solana API
solana_client = SolanaClient(SOLANA_RPC_URL)

# 🔹 إعداد Telegram API
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

# 🔹 ملف تخزين بيانات المستخدمين
CONFIG_FILE = "config.json"

# 🔹 تحميل بيانات المشتركين
def load_users():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    return {}

# 🔹 حفظ بيانات المشتركين
def save_users(users):
    with open(CONFIG_FILE, "w") as file:
        json.dump(users, file)

users = load_users()

# 🔹 أمر بدء البوت
def start(update, context):
    user_id = str(update.message.chat_id)
    
    if user_id in users:
        update.message.reply_text("✅ أنت مشترك بالفعل! استخدم /trade لبدء التداول.")
    else:
        update.message.reply_text(
            "👋 مرحبًا! هذا بوت تداول تلقائي.\n"
            "💰 الاشتراك مقابل 0.1 SOL.\n"
            f"🔹 أرسل المبلغ إلى عنوان محفظة Phantom:\n`{PHANTOM_WALLET_ADDRESS}`\n"
            "📤 بعد الدفع، استخدم /check_payment للتحقق من اشتراكك."
        )

# 🔹 التحقق من عمليات الدفع في Phantom Wallet
def check_payment(update, context):
    user_id = str(update.message.chat_id)
    transactions = solana_client.get_confirmed_signature_for_address2(PublicKey(PHANTOM_WALLET_ADDRESS), limit=5)

    for tx in transactions['result']:
        if user_id in users and users[user_id].get("tx") == tx['signature']:
            update.message.reply_text("✅ تم التحقق من اشتراكك مسبقًا!")
            return
    
    update.message.reply_text("⏳ يتم التحقق من الدفع...")

    for tx in transactions['result']:
        transaction_info = solana_client.get_confirmed_transaction(tx['signature'])
        
        if transaction_info['result']:
            for instr in transaction_info['result']['transaction']['message']['instructions']:
                if 'parsed' in instr and instr['parsed']['info']['destination'] == PHANTOM_WALLET_ADDRESS:
                    amount = float(instr['parsed']['info']['lamports']) / 1_000_000_000  # تحويل من lamports إلى SOL
                    
                    if amount >= 0.1:  # الحد الأدنى للدفع
                        users[user_id] = {"subscribed": True, "tx": tx['signature']}
                        save_users(users)
                        update.message.reply_text(f"✅ تم تأكيد اشتراكك بعد دفع {amount} SOL!")
                        return
    
    update.message.reply_text("❌ لم يتم العثور على معاملة دفع صالحة.")

# 🔹 التداول التلقائي
def trade(update, context):
    user_id = str(update.message.chat_id)
    
    if user_id not in users or not users[user_id]["subscribed"]:
        update.message.reply_text("🚫 يجب عليك الاشتراك أولًا! استخدم /start.")
        return
    
    symbol = "BTCUSDT"
    price = float(binance_client.get_symbol_ticker(symbol=symbol)["price"])
    
    if price < 40000:  # مثال: شراء إذا كان السعر أقل من 40,000$
        order = binance_client.order_market_buy(symbol=symbol, quantity=0.001)
        update.message.reply_text(f"✅ تم شراء {symbol} بسعر {price}!")
    elif price > 45000:  # مثال: بيع إذا كان السعر أعلى من 45,000$
        order = binance_client.order_market_sell(symbol=symbol, quantity=0.001)
        update.message.reply_text(f"🚀 تم بيع {symbol} بسعر {price}!")
    else:
        update.message.reply_text(f"📊 السعر الحالي لـ {symbol}: {price}.\nلا يوجد تداول الآن.")

# 🔹 إعداد أوامر تيليجرام
updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("check_payment", check_payment))
dp.add_handler(CommandHandler("trade", trade))

# 🔹 تشغيل البوت
updater.start_polling()
updater.idle()

