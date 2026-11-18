import os
import io
import html
import time
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone, timedelta

import qrcode
import telebot
from telebot import types

# ==========================================
# CONFIGURATION
# ==========================================
BOT_TOKEN = "8677868565:AAEm_q6UNYr_mqStJFyms1sHrBfwOSicjV8"  
UPI_ID = "8016922924@ibl"                    
ADMIN_PASSWORD = "743405"                   
DEVELOPER_USERNAME = "@ai_brain_box_2"      
DB_NAME = "bot_data.db"

# ==========================================
# INITIALIZATION
# ==========================================
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
db_lock = threading.Lock()
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
conn.row_factory = sqlite3.Row

BOT_USERNAME = ""
try:
    BOT_USERNAME = bot.get_me().username
except Exception:
    BOT_USERNAME = ""

user_states = {}       
qr_sessions = {}       

def ist_now():
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).strftime("%d-%m-%Y %I:%M %p")

# ==========================================
# MULTI-LANGUAGE COMPLETE TRANSLATIONS
# ==========================================
LANGS = {
    "en": {
        "welcome": "👋 Welcome <b>{name}</b>!\n\nPlease choose an option from the menu below 👇",
        "free_prod": "🆓 Free Products",
        "paid_prod": "💎 Paid Products",
        "raffle": "🎟 Raffle Status",
        "pur_hist": "📜 Purchase History",
        "raf_hist": "📋 Raffle History",
        "wallet": "👛 Wallet",
        "dev": "👨‍💻 Developer",
        "admin_login": "🔐 Admin Login",
        "support": "🆘 Help Support",
        "lang_btn": "🌐 Change Language",
        "no_prod": "❌ No products available right now.",
        "wallet_title": "👛 <b>My Wallet</b>\n\n💵 <b>Rs. Balance:</b> ₹{rs:.2f}\n🪙 <b>Coin Balance:</b> {coin} 🪙",
        "choose_lang": "🌐 <b>Select your language:</b>",
        "lang_changed": "✅ Language successfully changed to <b>English</b>!",
    },
    "hi": {
        "welcome": "👋 स्वागत है <b>{name}</b>!\n\nकृपया नीचे दिए गए मेनू से एक विकल्प चुनें 👇",
        "free_prod": "🆓 मुफ्त उत्पाद",
        "paid_prod": "💎 पेड उत्पाद",
        "raffle": "🎟 रैफल स्थिति",
        "pur_hist": "📜 खरीदारी का इतिहास",
        "raf_hist": "📋 रैफल इतिहास",
        "wallet": "👛 वॉलेट",
        "dev": "👨‍💻 डेवलपर",
        "admin_login": "🔐 एडमिन लॉगिन",
        "support": "🆘 सहायता समर्थन",
        "lang_btn": "🌐 भाषा बदलें",
        "no_prod": "❌ वर्तमान में कोई उत्पाद उपलब्ध नहीं है।",
        "wallet_title": "👛 <b>मेरा वॉलेट</b>\n\n💵 <b>Rs. बैलेंस:</b> ₹{rs:.2f}\n🪙 <b>कॉइन बैलेंस:</b> {coin} 🪙",
        "choose_lang": "🌐 <b>अपनी भाषा चुनें:</b>",
        "lang_changed": "✅ भाषा सफलतापूर्वक बदलकर <b>हिन्दी</b> कर दी गई है!",
    },
    "bn": {
        "welcome": "👋 স্বাগতম <b>{name}</b>!\n\nনিচের মেনু থেকে আপনার পছন্দের অপশন বেছে নিন 👇",
        "free_prod": "🆓 ফ্রি প্রোডাক্টস",
        "paid_prod": "💎 পেইড প্রোডাক্টস",
        "raffle": "🎟 র‍্যাফেল স্ট্যাটাস",
        "pur_hist": "📜 পার্চেজ হিস্ট্রি",
        "raf_hist": "📋 র‍্যাফেল হিস্ট্রি",
        "wallet": "👛 ওয়ালেট",
        "dev": "👨‍💻 ডেভেলপার",
        "admin_login": "🔐 এডমিন লগইন",
        "support": "🆘 হেল্প সাপোর্ট",
        "lang_btn": "🌐 ভাষা পরিবর্তন",
        "no_prod": "❌ বর্তমানে কোনো প্রোডাক্ট নেই।",
        "wallet_title": "👛 <b>আমার ওয়ালেট</b>\n\n💵 <b>টাকা ব্যালেন্স:</b> ₹{rs:.2f}\n🪙 <b>কয়েন ব্যালেন্স:</b> {coin} 🪙",
        "choose_lang": "🌐 <b>আপনার ভাষা নির্বাচন করুন:</b>",
        "lang_changed": "✅ সফলভাবে ভাষা পরিবর্তন করে <b>বাংলা</b> করা হয়েছে!",
    }
}

def get_txt(user_id, key):
    user = get_user(user_id)
    lang = user["language"] if user and "language" in user.keys() else "en"
    return LANGS.get(lang, LANGS["en"]).get(key, LANGS["en"][key])

# ==========================================
# DATABASE SETUP
# ==========================================
fn_lang_added = False
try:
    c = conn.cursor()
    c.execute("SELECT language FROM users LIMIT 1")
    c.fetchone()
    fn_lang_added = True
except Exception:
    pass

def init_db():
    with db_lock:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                rs_balance REAL DEFAULT 0.0,
                coin_balance INTEGER DEFAULT 0,
                referred_by INTEGER DEFAULT NULL,
                total_raffles INTEGER DEFAULT 0,
                language TEXT DEFAULT 'en',
                joined_at TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ptype TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                image_id TEXT,
                file_type TEXT,
                file_value TEXT,
                file_name TEXT,
                tutorial_type TEXT DEFAULT 'none',
                tutorial_value TEXT,
                created_at TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER,
                ptype TEXT NOT NULL,
                product_name TEXT NOT NULL,
                price_paid REAL NOT NULL,
                file_type TEXT,
                file_value TEXT,
                file_name TEXT,
                tutorial_type TEXT DEFAULT 'none',
                tutorial_value TEXT,
                purchased_at TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS raffle_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_user_id INTEGER UNIQUE NOT NULL,
                referred_username TEXT,
                referred_name TEXT,
                joined_at TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS payment_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT,
                amount REAL NOT NULL,
                screenshot_file_id TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                reviewed_at TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                logged_in_at TEXT
            )
        """)
        conn.commit()

init_db()

if not fn_lang_added:
    try:
        with db_lock:
            conn.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'en'")
            conn.commit()
    except Exception:
        pass


def get_user(user_id):
    with db_lock:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return c.fetchone()


def register_or_update_user(tg_user, referrer_id=None):
    user_id = tg_user.id
    username = f"@{tg_user.username}" if tg_user.username else "No Username"
    full_name = f"{tg_user.first_name or ''} {tg_user.last_name or ''}".strip() or "User"

    existing = get_user(user_id)
    now = ist_now()
    new_referral_credited = False
    ref_old_coin = 0
    ref_new_coin = 0

    with db_lock:
        c = conn.cursor()
        if existing is None:
            valid_ref = None
            if referrer_id and referrer_id != user_id:
                c.execute("SELECT user_id, coin_balance FROM users WHERE user_id = ?", (referrer_id,))
                ref_row = c.fetchone()
                if ref_row:
                    valid_ref = referrer_id
                    ref_old_coin = ref_row["coin_balance"]

            c.execute("""
                INSERT INTO users (user_id, username, full_name, rs_balance, coin_balance, referred_by, total_raffles, language, joined_at)
                VALUES (?, ?, ?, 0.0, 0, ?, 0, 'en', ?)
            """, (user_id, username, full_name, valid_ref, now))

            if valid_ref:
                ref_new_coin = ref_old_coin + 1
                c.execute("""
                    UPDATE users
                    SET coin_balance = coin_balance + 1,
                        total_raffles = total_raffles + 1
                    WHERE user_id = ?
                """, (valid_ref,))
                c.execute("""
                    INSERT OR IGNORE INTO raffle_history
                    (referrer_id, referred_user_id, referred_username, referred_name, joined_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (valid_ref, user_id, username, full_name, now))
                new_referral_credited = True
        else:
            c.execute("""
                UPDATE users SET username = ?, full_name = ? WHERE user_id = ?
            """, (username, full_name, user_id))
        conn.commit()

    if new_referral_credited and referrer_id:
        try:
            bot.send_message(
                referrer_id,
                f"🎉 <b>New Raffle / Referral Joined!</b>\n\n"
                f"👤 <b>User Name:</b> {html.escape(full_name)}\n"
                f"🔗 <b>Username:</b> {html.escape(username)}\n\n"
                f"🪙 <b>Reward Earned:</b> +1 Coin\n"
                f"📊 <b>Old Coin Balance:</b> {ref_old_coin} 🪙\n"
                f"➕ <b>Added:</b> +1 🪙\n"
                f"💰 <b>Total Coin Balance:</b> <b>{ref_new_coin} 🪙</b>"
            )
        except Exception:
            pass


def is_admin(user_id):
    with db_lock:
        c = conn.cursor()
        c.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
        return c.fetchone() is not None


def set_admin(user_id, active=True):
    with db_lock:
        c = conn.cursor()
        if active:
            c.execute("INSERT OR REPLACE INTO admins (user_id, logged_in_at) VALUES (?, ?)", (user_id, ist_now()))
        else:
            c.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
        conn.commit()


def get_all_admins():
    with db_lock:
        c = conn.cursor()
        c.execute("SELECT user_id FROM admins")
        return [row["user_id"] for row in c.fetchall()]


def clear_state(user_id):
    user_states.pop(user_id, None)


# ==========================================
# KEYBOARDS (DYNAMIC LANGUAGE SUPPORTED)
# ==========================================
def main_menu_keyboard(user_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(get_txt(user_id, "free_prod"), get_txt(user_id, "paid_prod"))
    kb.row(get_txt(user_id, "raffle"))
    kb.row(get_txt(user_id, "pur_hist"), get_txt(user_id, "raf_hist"))
    kb.row(get_txt(user_id, "wallet"))
    kb.row(get_txt(user_id, "lang_btn"))
    kb.row(get_txt(user_id, "dev"), get_txt(user_id, "admin_login"))
    kb.row(get_txt(user_id, "support"))
    return kb


def admin_menu_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("➕ Add products", callback_data="adm_add_prod"),
        types.InlineKeyboardButton("🛠 Management products", callback_data="adm_manage_prod")
    )
    kb.row(types.InlineKeyboardButton("📊 Dashboard", callback_data="adm_dashboard"))
    kb.row(
        types.InlineKeyboardButton("👥 Users", callback_data="adm_users_0"),
        types.InlineKeyboardButton("💳 Add money history", callback_data="adm_money_hist")
    )
    kb.row(types.InlineKeyboardButton("🎁 Send bonus", callback_data="adm_bonus"))
    kb.row(
        types.InlineKeyboardButton("📢 Send notification", callback_data="adm_notify"),
        types.InlineKeyboardButton("🏆 Raffle leaderboard", callback_data="adm_leaderboard")
    )
    kb.row(types.InlineKeyboardButton("📥 Payment request", callback_data="adm_pay_reqs"))
    kb.row(types.InlineKeyboardButton("🚪 Logout Admin", callback_data="adm_logout"))
    return kb


# ==========================================
# START & MAIN MENU HANDLERS
# ==========================================
@bot.message_handler(commands=["start"])
def handle_start(message):
    clear_state(message.from_user.id)
    user_id = message.from_user.id
    referrer_id = None
    parts = message.text.split()
    if len(parts) > 1 and parts[1].startswith("ref_"):
        try:
            referrer_id = int(parts[1].replace("ref_", ""))
        except ValueError:
            referrer_id = None

    register_or_update_user(message.from_user, referrer_id)
    name = html.escape(message.from_user.first_name or "User")

    if is_admin(user_id):
        bot.send_message(
            message.chat.id,
            f"🔐 <b>Admin Panel</b>\nস্বাগতম অ্যাডমিন {name}!",
            reply_markup=admin_menu_keyboard()
        )
    else:
        welcome_text = get_txt(user_id, "welcome").format(name=name)
        bot.send_message(
            message.chat.id,
            welcome_text,
            reply_markup=main_menu_keyboard(user_id)
        )


def send_raffle_status(chat_id, user_id):
    user = get_user(user_id)
    if not user:
        return
    bot_uname = BOT_USERNAME or bot.get_me().username
    raffle_link = f"https://t.me/{bot_uname}?start=ref_{user_id}"

    text = (
        f"🎟 <b>Raffle & Referral Dashboard</b>\n\n"
        f"👤 <b>Name:</b> {html.escape(user['full_name'])}\n"
        f"🔗 <b>Username:</b> {html.escape(user['username'])}\n"
        f"👥 <b>Total Raffles / Joins:</b> <b>{user['total_raffles']}</b>\n"
        f"🪙 <b>Total Coins Balance:</b> <b>{user['coin_balance']} 🪙</b>\n"
        f"💰 <b>Earnings Per Referral:</b> +1 🪙\n\n"
        f"🔗 <b>Your Exclusive Raffle Link:</b>\n<code>{raffle_link}</code>"
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📤 Share Link Now", url=f"https://t.me/share/url?url={raffle_link}&text=Join%20this%20amazing%20bot%20and%20get%20free%20rewards!"))
    bot.send_message(chat_id, text, reply_markup=kb)


def send_wallet(chat_id, user_id):
    user = get_user(user_id)
    if not user:
        return
    text = get_txt(user_id, "wallet_title").format(rs=user['rs_balance'], coin=user['coin_balance'])
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("➕ Add Rs.", callback_data="wallet_add_rs"),
        types.InlineKeyboardButton("🔙 Back", callback_data="wallet_back")
    )
    bot.send_message(chat_id, text, reply_markup=kb)


def show_products_list(chat_id, ptype, user_id):
    with db_lock:
        c = conn.cursor()
        c.execute("SELECT id, name, price FROM products WHERE ptype = ? ORDER BY id DESC", (ptype,))
        rows = c.fetchall()

    title = "🆓 <b>Free Products</b>" if ptype == "free" else "💎 <b>Paid Products</b>"
    if not rows:
        bot.send_message(chat_id, f"{title}\n\n{get_txt(user_id, 'no_prod')}")
        return

    kb = types.InlineKeyboardMarkup()
    for r in rows:
        price_str = f"{int(r['price'])} 🪙" if ptype == "free" else f"₹{r['price']:.2f}"
        kb.add(types.InlineKeyboardButton(f"{r['name']} ({price_str})", callback_data=f"view_prod_{r['id']}"))

    bot.send_message(chat_id, f"{title}\n\nপ্রোডাক্ট দেখতে নামের উপর ক্লিক করুন 👇", reply_markup=kb)


def deliver_product_file(chat_id, prod_name, file_type, file_value, file_name, tut_type, tut_value, tut_cb):
    kb = types.InlineKeyboardMarkup()
    if tut_type != "none" and tut_value:
        kb.add(types.InlineKeyboardButton("🎬 Tutorial Video", callback_data=tut_cb))

    caption = f"✅ <b>Product:</b> {html.escape(prod_name)}\n📁 <b>File Name:</b> {html.escape(file_name or prod_name)}"
    try:
        if file_type == "document" and file_value:
            bot.send_document(chat_id, file_value, caption=caption, reply_markup=kb if tut_type != "none" else None)
        elif file_type == "video" and file_value:
            bot.send_video(chat_id, file_value, caption=caption, reply_markup=kb if tut_type != "none" else None)
        elif file_type == "audio" and file_value:
            bot.send_audio(chat_id, file_value, caption=caption, reply_markup=kb if tut_type != "none" else None)
        elif file_type == "photo" and file_value:
            bot.send_photo(chat_id, file_value, caption=caption, reply_markup=kb if tut_type != "none" else None)
        else:
            bot.send_message(chat_id, f"{caption}\n🔗 <b>Download/Access:</b> {html.escape(file_value or 'N/A')}", reply_markup=kb if tut_type != "none" else None)
    except Exception as e:
        bot.send_message(chat_id, f"{caption}\n⚠️ ফাইল পাঠাতে সমস্যা হয়েছে: {html.escape(str(e))}")


# ==========================================
# MAIN TEXT HANDLER (ALL LANGUAGES)
# ==========================================
@bot.message_handler(content_types=["text"])
def handle_text(message):
    user_id = message.from_user.id
    text = message.text.strip()
    register_or_update_user(message.from_user)

    # Universal Language Button Check across all 3 languages
    if text in [LANGS["en"]["lang_btn"], LANGS["hi"]["lang_btn"], LANGS["bn"]["lang_btn"]]:
        clear_state(user_id)
        kb = types.InlineKeyboardMarkup()
        kb.row(
            types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            types.InlineKeyboardButton("🇮🇳 हिन्दी", callback_data="lang_hi"),
            types.InlineKeyboardButton("🇧🇩 বাংলা", callback_data="lang_bn")
        )
        bot.send_message(message.chat.id, get_txt(user_id, "choose_lang"), reply_markup=kb)
        return

    # Check menu selections dynamically based on any active language
    is_free = text in [LANGS["en"]["free_prod"], LANGS["hi"]["free_prod"], LANGS["bn"]["free_prod"]]
    is_paid = text in [LANGS["en"]["paid_prod"], LANGS["hi"]["paid_prod"], LANGS["bn"]["paid_prod"]]
    is_raffle = text in [LANGS["en"]["raffle"], LANGS["hi"]["raffle"], LANGS["bn"]["raffle"]]
    is_pur = text in [LANGS["en"]["pur_hist"], LANGS["hi"]["pur_hist"], LANGS["bn"]["pur_hist"]]
    is_raf = text in [LANGS["en"]["raf_hist"], LANGS["hi"]["raf_hist"], LANGS["bn"]["raf_hist"]]
    is_wal = text in [LANGS["en"]["wallet"], LANGS["hi"]["wallet"], LANGS["bn"]["wallet"]]
    is_dev = text in [LANGS["en"]["dev"], LANGS["hi"]["dev"], LANGS["bn"]["dev"]]
    is_sup = text in [LANGS["en"]["support"], LANGS["hi"]["support"], LANGS["bn"]["support"]]
    is_adm = text in [LANGS["en"]["admin_login"], LANGS["hi"]["admin_login"], LANGS["bn"]["admin_login"]]

    if is_free or is_paid or is_raffle or is_pur or is_raf or is_wal or is_dev or is_sup or is_adm:
        clear_state(user_id)

        if is_free:
            show_products_list(message.chat.id, "free", user_id)
        elif is_paid:
            show_products_list(message.chat.id, "paid", user_id)
        elif is_raffle:
            send_raffle_status(message.chat.id, user_id)
        elif is_pur:
            kb = types.InlineKeyboardMarkup()
            kb.row(
                types.InlineKeyboardButton("🆓 Free", callback_data="phist_free"),
                types.InlineKeyboardButton("💎 Paid", callback_data="phist_paid")
            )
            bot.send_message(message.chat.id, "📜 <b>Purchase History</b>\n\nকোন ধরনের প্রোডাক্ট হিস্ট্রি দেখতে চান?", reply_markup=kb)
        elif is_raf:
            with db_lock:
                c = conn.cursor()
                c.execute("""
                    SELECT referred_name, referred_username, joined_at
                    FROM raffle_history
                    WHERE referrer_id = ?
                    ORDER BY id DESC
                """, (user_id,))
                rows = c.fetchall()

            if not rows:
                bot.send_message(message.chat.id, "📋 <b>Raffle History</b>\n\nএখনো কেউ আপনার Raffle লিংক দিয়ে জয়েন করেনি।")
            else:
                lines = ["📋 <b>Raffle & Referral History</b>\n"]
                for idx, r in enumerate(rows[:30], 1):
                    lines.append(
                        f"{idx}. 👤 <b>{html.escape(r['referred_name'])}</b> "
                        f"({html.escape(r['referred_username'])})\n"
                        f"   🕒 Join Time: {r['joined_at']}"
                    )
                if len(rows) > 30:
                    lines.append(f"\n<i>...এবং আরও {len(rows) - 30} জন।</i>")
                bot.send_message(message.chat.id, "\n".join(lines))
        elif is_wal:
            send_wallet(message.chat.id, user_id)
        elif is_dev:
            bot.send_message(message.chat.id, f"👨‍💻 <b>Developer Information</b>\n\n📩 Contact: {DEVELOPER_USERNAME}")
        elif is_sup:
            bot.send_message(message.chat.id, f"🆘 <b>Help & Support</b>\n\nযেকোনো সমস্যা বা সাহায্যের জন্য যোগাযোগ করুন:\n📩 {DEVELOPER_USERNAME}")
        elif is_adm:
            if is_admin(user_id):
                bot.send_message(message.chat.id, "🔐 <b>Admin Panel</b>\nনিচের অপশনগুলো ব্যবহার করুন:", reply_markup=admin_menu_keyboard())
            else:
                user_states[user_id] = {"state": "awaiting_admin_pass", "data": {}}
                bot.send_message(message.chat.id, "🔐 <b>Admin Login</b>\nদয়া করে Admin Password দিন:")
        return

    # ==========================================
    # STATE MACHINE
    # ==========================================
    st = user_states.get(user_id)
    if not st:
        return

    state = st["state"]
    data = st["data"]

    if state == "awaiting_admin_pass":
        clear_state(user_id)
        if text == ADMIN_PASSWORD:
            set_admin(user_id, True)
            bot.send_message(message.chat.id, "✅ <b>Admin Login Successful!</b>", reply_markup=admin_menu_keyboard())
        else:
            bot.send_message(message.chat.id, "❌ ভুল পাসওয়ার্ড! আবার চেষ্টা করুন।")

    elif state == "awaiting_add_rs_amount":
        try:
            amount = float(text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            bot.send_message(message.chat.id, "❌ সঠিক টাকার পরিমাণ লিখুন (যেমন: 50 বা 100):")
            return

        clear_state(user_id)
        start_qr_payment_session(message.chat.id, user_id, amount)

    # Admin Add Product
    elif state == "adm_prod_name":
        data["name"] = text
        st["state"] = "adm_prod_desc"
        bot.send_message(message.chat.id, "📝 প্রোডাক্টের <b>Description</b> লিখুন:")

    elif state == "adm_prod_desc":
        data["description"] = text
        st["state"] = "adm_prod_price"
        unit = "🪙 Coin" if data["ptype"] == "free" else "₹ Rs."
        bot.send_message(message.chat.id, f"💰 প্রোডাক্টের দাম লিখুন ({unit} সংখ্যায়):")

    elif state == "adm_prod_price":
        try:
            price = float(text)
            if price < 0:
                raise ValueError
            if data["ptype"] == "free":
                price = int(price)
        except ValueError:
            bot.send_message(message.chat.id, "❌ সঠিক সংখ্যা লিখুন (যেমন: 5 বা 100):")
            return
        data["price"] = price
        st["state"] = "adm_prod_image"
        
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("⏭ Skip Image", callback_data="skip_step_img"))
        bot.send_message(message.chat.id, "🖼 প্রোডাক্টের <b>Image (Photo)</b> পাঠান অথবা স্কিপ করতে নিচের বাটনে ক্লিক করুন:", reply_markup=kb)

    elif state == "adm_prod_file":
        data["file_type"] = "link"
        data["file_value"] = text
        data["file_name"] = data["name"]
        st["state"] = "adm_prod_tutorial"
        
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("⏭ Skip Tutorial", callback_data="skip_step_tut"))
        bot.send_message(message.chat.id, "🎬 এখন <b>Tutorial Video</b> আপলোড করুন অথবা ভিডিও লিংক দিন (অথবা স্কিপ করুন):", reply_markup=kb)

    # Admin Edit Product
    elif state == "adm_edit_name":
        pid = data["pid"]
        with db_lock:
            conn.execute("UPDATE products SET name = ? WHERE id = ?", (text, pid))
            conn.commit()
        clear_state(user_id)
        bot.send_message(message.chat.id, "✅ প্রোডাক্টের নাম আপডেট হয়েছে!", reply_markup=admin_menu_keyboard())

    elif state == "adm_edit_desc":
        pid = data["pid"]
        with db_lock:
            conn.execute("UPDATE products SET description = ? WHERE id = ?", (text, pid))
            conn.commit()
        clear_state(user_id)
        bot.send_message(message.chat.id, "✅ Description আপডেট হয়েছে!", reply_markup=admin_menu_keyboard())

    elif state == "adm_edit_price":
        try:
            price = float(text)
            if price < 0:
                raise ValueError
        except ValueError:
            bot.send_message(message.chat.id, "❌ সঠিক সংখ্যা লিখুন:")
            return
        pid = data["pid"]
        with db_lock:
            conn.execute("UPDATE products SET price = ? WHERE id = ?", (price, pid))
            conn.commit()
        clear_state(user_id)
        bot.send_message(message.chat.id, "✅ দাম আপডেট হয়েছে!", reply_markup=admin_menu_keyboard())

    elif state == "adm_edit_file":
        pid = data["pid"]
        with db_lock:
            conn.execute("UPDATE products SET file_type = 'link', file_value = ?, file_name = 'Link' WHERE id = ?", (text, pid))
            conn.commit()
        clear_state(user_id)
        bot.send_message(message.chat.id, "✅ ফাইল লিংক আপডেট হয়েছে!", reply_markup=admin_menu_keyboard())

    elif state == "adm_edit_tut":
        pid = data["pid"]
        with db_lock:
            conn.execute("UPDATE products SET tutorial_type = 'link', tutorial_value = ? WHERE id = ?", (text, pid))
            conn.commit()
        clear_state(user_id)
        bot.send_message(message.chat.id, "✅ Tutorial আপডেট হয়েছে!", reply_markup=admin_menu_keyboard())

    # Admin Send Bonus
    elif state == "adm_bonus_target":
        target = text.strip()
        if target.upper() != "ALL":
            try:
                uid = int(target)
                if not get_user(uid):
                    bot.send_message(message.chat.id, "❌ এই User ID ডাটাবেজে পাওয়া যায়নি। আবার দিন অথবা <code>ALL</code> লিখুন:")
                    return
            except ValueError:
                bot.send_message(message.chat.id, "❌ সঠিক User ID দিন অথবা সবার জন্য <code>ALL</code> লিখুন:")
                return
        data["target"] = target.upper() if target.upper() == "ALL" else int(target)
        st["state"] = "adm_bonus_amount"
        unit = "₹ Rs." if data["btype"] == "rs" else "🪙 Coins"
        bot.send_message(message.chat.id, f"💰 কত {unit} বোনাস পাঠাতে চান? (সংখ্যা লিখুন):")

    elif state == "adm_bonus_amount":
        try:
            amt = float(text)
            if amt <= 0:
                raise ValueError
            if data["btype"] == "coin":
                amt = int(amt)
        except ValueError:
            bot.send_message(message.chat.id, "❌ সঠিক সংখ্যা লিখুন:")
            return

        target = data["target"]
        btype = data["btype"]
        clear_state(user_id)

        with db_lock:
            c = conn.cursor()
            if target == "ALL":
                c.execute("SELECT user_id FROM users")
                uids = [r["user_id"] for r in c.fetchall()]
                if btype == "rs":
                    c.execute("UPDATE users SET rs_balance = rs_balance + ?", (amt,))
                else:
                    c.execute("UPDATE users SET coin_balance = coin_balance + ?", (amt,))
            else:
                uids = [target]
                if btype == "rs":
                    c.execute("UPDATE users SET rs_balance = rs_balance + ? WHERE user_id = ?", (amt, target))
                else:
                    c.execute("UPDATE users SET coin_balance = coin_balance + ? WHERE user_id = ?", (amt, target))
            conn.commit()

        unit_txt = f"₹{amt:.2f}" if btype == "rs" else f"{amt} 🪙"
        sent = 0
        for uid in uids:
            try:
                bot.send_message(uid, f"🎁 <b>Bonus Received!</b>\nঅ্যাডমিনের পক্ষ থেকে আপনি <b>{unit_txt}</b> বোনাস পেয়েছেন!")
                sent += 1
            except Exception:
                pass

        bot.send_message(message.chat.id, f"✅ বোনাস পাঠানো সম্পন্ন! ({sent} জন ইউজারকে নোটিফিকেশন দেওয়া হয়েছে)", reply_markup=admin_menu_keyboard())

    # Admin Broadcast with Statistics
    elif state == "adm_broadcast":
        clear_state(user_id)
        with db_lock:
            c = conn.cursor()
            c.execute("SELECT user_id FROM users")
            uids = [r["user_id"] for r in c.fetchall()]

        total_users = len(uids)
        sent, failed = 0, 0
        for uid in uids:
            try:
                bot.send_message(uid, f"📢 <b>Notification</b>\n\n{html.escape(text)}")
                sent += 1
            except Exception:
                failed += 1

        report = (
            f"📊 <b>Broadcast Report</b>\n\n"
            f"👥 Total Users: <b>{total_users}</b>\n"
            f"📤 Total Sent: <b>{total_users}</b>\n"
            f"✔️ Success: <b>{sent}</b>\n"
            f"❌ Error/Failed: <b>{failed}</b>"
        )
        bot.send_message(message.chat.id, report, reply_markup=admin_menu_keyboard())


# ==========================================
# MEDIA HANDLERS
# ==========================================
@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    user_id = message.from_user.id
    register_or_update_user(message.from_user)
    file_id = message.photo[-1].file_id

    st = user_states.get(user_id)
    if st:
        state = st["state"]
        data = st["data"]

        if state == "adm_prod_image":
            data["image_id"] = file_id
            st["state"] = "adm_prod_file"
            bot.send_message(message.chat.id, "📁 ছবি সেভ হয়েছে! এখন প্রোডাক্টের <b>File</b> আপলোড করুন অথবা ডাউনলোড <b>Link</b> পাঠান:")
            return

        elif state == "adm_prod_file":
            data["file_type"] = "photo"
            data["file_value"] = file_id
            data["file_name"] = data["name"] + ".jpg"
            st["state"] = "adm_prod_tutorial"
            
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("⏭ Skip Tutorial", callback_data="skip_step_tut"))
            bot.send_message(message.chat.id, "🎬 ফাইল সেভ হয়েছে! এখন <b>Tutorial Video</b> আপলোড করুন অথবা লিংক দিন (অথবা স্কিপ করুন):", reply_markup=kb)
            return

        elif state == "adm_edit_file":
            with db_lock:
                conn.execute("UPDATE products SET file_type = 'photo', file_value = ?, file_name = 'Image File' WHERE id = ?", (file_id, data["pid"]))
                conn.commit()
            clear_state(user_id)
            bot.send_message(message.chat.id, "✅ প্রোডাক্ট ফাইল আপডেট হয়েছে!", reply_markup=admin_menu_keyboard())
            return

        elif state == "adm_broadcast":
            clear_state(user_id)
            caption = message.caption or ""
            with db_lock:
                c = conn.cursor()
                c.execute("SELECT user_id FROM users")
                uids = [r["user_id"] for r in c.fetchall()]
            
            total_users = len(uids)
            sent, failed = 0, 0
            for uid in uids:
                try:
                    bot.send_photo(uid, file_id, caption=f"📢 <b>Notification</b>\n\n{html.escape(caption)}")
                    sent += 1
                except Exception:
                    failed += 1

            report = (
                f"📊 <b>Broadcast Report (Photo)</b>\n\n"
                f"👥 Total Users: <b>{total_users}</b>\n"
                f"📤 Total Sent: <b>{total_users}</b>\n"
                f"✔️ Success: <b>{sent}</b>\n"
                f"❌ Error/Failed: <b>{failed}</b>"
            )
            bot.send_message(message.chat.id, report, reply_markup=admin_menu_keyboard())
            return

    # QR Payment Screenshot Processing
    qrs = qr_sessions.get(user_id)
    if qrs and qrs.get("active"):
        if time.time() > qrs["expires_at"]:
            qrs["active"] = False
            bot.send_message(message.chat.id, "❌ এই QR কোডের ১০ মিনিট সময় শেষ হয়ে গেছে! দয়া করে Wallet থেকে আবার <b>Add Rs.</b> করুন।")
            return

        qrs["active"] = False
        amount = qrs["amount"]
        user = get_user(user_id)
        now = ist_now()

        with db_lock:
            c = conn.cursor()
            c.execute("""
                INSERT INTO payment_requests (user_id, username, full_name, amount, screenshot_file_id, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'pending', ?)
            """, (user_id, user["username"], user["full_name"], amount, file_id, now))
            req_id = c.lastrowid
            conn.commit()

        bot.send_message(
            message.chat.id,
            f"✅ <b>Payment Request Submitted!</b>\n\n"
            f"🆔 Request ID: #{req_id}\n"
            f"💵 Amount: ₹{amount:.2f}\n"
            f"⏳ আপনার রিকোয়েস্ট Admin-এর কাছে পাঠানো হয়েছে। অ্যাপ্রুভ হলে ব্যালেন্স যুক্ত হবে।"
        )

        kb = types.InlineKeyboardMarkup()
        kb.row(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"pay_app_{req_id}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"pay_rej_{req_id}")
        )
        for adm_id in get_all_admins():
            try:
                bot.send_photo(
                    adm_id,
                    file_id,
                    caption=(
                        f"🔔 <b>New Payment Request #{req_id}</b>\n\n"
                        f"👤 Name: {html.escape(user['full_name'])}\n"
                        f"🔗 Username: {html.escape(user['username'])}\n"
                        f"🆔 User ID: <code>{user_id}</code>\n"
                        f"💵 Amount: <b>₹{amount:.2f}</b>\n"
                        f"🕒 Time: {now}"
                    ),
                    reply_markup=kb
                )
            except Exception:
                pass


@bot.message_handler(content_types=["document", "video", "audio"])
def handle_media_files(message):
    user_id = message.from_user.id
    st = user_states.get(user_id)
    if not st:
        return

    state = st["state"]
    data = st["data"]

    if message.content_type == "document":
        ftype = "document"
        fval = message.document.file_id
        fname = message.document.file_name or "Document"
    elif message.content_type == "video":
        ftype = "video"
        fval = message.video.file_id
        fname = message.video.file_name or "Video.mp4"
    else:
        ftype = "audio"
        fval = message.audio.file_id
        fname = message.audio.file_name or "Audio.mp3"

    if state == "adm_prod_file":
        data["file_type"] = ftype
        data["file_value"] = fval
        data["file_name"] = fname
        st["state"] = "adm_prod_tutorial"
        
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("⏭ Skip Tutorial", callback_data="skip_step_tut"))
        bot.send_message(message.chat.id, "🎬 ফাইল সেভ হয়েছে! এখন <b>Tutorial Video</b> আপলোড করুন অথবা লিংক দিন (অথবা স্কিপ করুন):", reply_markup=kb)

    elif state == "adm_prod_tutorial":
        data["tutorial_type"] = "video" if ftype == "video" else ftype
        data["tutorial_value"] = fval
        save_new_product(message.chat.id, user_id, data)

    elif state == "adm_edit_file":
        with db_lock:
            conn.execute("UPDATE products SET file_type = ?, file_value = ?, file_name = ? WHERE id = ?", (ftype, fval, fname, data["pid"]))
            conn.commit()
        clear_state(user_id)
        bot.send_message(message.chat.id, "✅ প্রোডাক্ট ফাইল আপডেট হয়েছে!", reply_markup=admin_menu_keyboard())

    elif state == "adm_edit_tut":
        with db_lock:
            conn.execute("UPDATE products SET tutorial_type = 'video', tutorial_value = ? WHERE id = ?", (fval, data["pid"]))
            conn.commit()
        clear_state(user_id)
        bot.send_message(message.chat.id, "✅ Tutorial Video আপডেট হয়েছে!", reply_markup=admin_menu_keyboard())


def save_new_product(chat_id, user_id, data):
    clear_state(user_id)
    with db_lock:
        c = conn.cursor()
        c.execute("""
            INSERT INTO products (ptype, name, description, price, image_id, file_type, file_value, file_name, tutorial_type, tutorial_value, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["ptype"],
            data["name"],
            data["description"],
            data["price"],
            data.get("image_id"),
            data["file_type"],
            data["file_value"],
            data["file_name"],
            data.get("tutorial_type", "none"),
            data.get("tutorial_value"),
            ist_now()
        ))
        conn.commit()
        
        c.execute("SELECT user_id FROM users")
        all_uids = [r["user_id"] for r in c.fetchall()]

    bot.send_message(chat_id, f"✅ প্রোডাক্ট <b>{html.escape(data['name'])}</b> সফলভাবে যুক্ত হয়েছে এবং ইউজারদের নোটিফিকেশন পাঠানো হচ্ছে!", reply_markup=admin_menu_keyboard())

    def notify_new_prod():
        prod_text = (
            f"🔥 <b>New Product Added!</b>\n\n"
            f"📦 <b>Name:</b> {html.escape(data['name'])}\n"
            f"📝 <b>Desc:</b> {html.escape(data['description'] or '')}\n"
            f"🏷 <b>Type:</b> {data['ptype'].upper()}"
        )
        for uid in all_uids:
            try:
                bot.send_message(uid, prod_text)
            except Exception:
                pass

    threading.Thread(target=notify_new_prod, daemon=True).start()


# ==========================================
# QR CODE & PAYMENT INSTRUCTION
# ==========================================
def start_qr_payment_session(chat_id, user_id, amount):
    upi_uri = f"upi://pay?pa={UPI_ID}&pn=TelegramStore&am={amount:.2f}&cu=INR"
    qr_img = qrcode.make(upi_uri)
    bio = io.BytesIO()
    bio.name = "payment_qr.png"
    qr_img.save(bio, "PNG")
    bio.seek(0)

    expires_at = time.time() + 600  # 10 minutes
    
    caption = (
        f"💳 <b>Scan QR Code to Pay</b>\n\n"
        f"💵 <b>Amount:</b> ₹{amount:.2f}\n"
        f"⏳ <b>Time Remaining:</b> 10:00 min"
    )
    msg = bot.send_photo(chat_id, bio, caption=caption)

    instruction_text = (
        f"📌 <b>Payment Instructions & UPI ID:</b>\n\n"
        f"1️⃣ এই QR কোড স্ক্যান করে অথবা নিচে দেওয়া UPI ID তে টাকা পাঠান:\n"
        f"🆔 UPI ID: <code>{UPI_ID}</code>\n"
        f"💵 টাকার পরিমাণ: <b>₹{amount:.2f}</b>\n\n"
        f"2️⃣ পেমেন্ট সফল হওয়ার পর পেমেন্টের <b>স্ক্রিনশট (Screenshot Image)</b> ঠিক এই চ্যাটে পাঠান।"
    )
    inst_msg = bot.send_message(chat_id, instruction_text)

    session = {
        "amount": amount,
        "expires_at": expires_at,
        "chat_id": chat_id,
        "msg_id": msg.message_id,
        "inst_msg_id": inst_msg.message_id,
        "active": True
    }
    qr_sessions[user_id] = session

    def timer_worker(uid, sess):
        for mins_left in [8, 5, 2, 1]:
            wait_sec = sess["expires_at"] - (mins_left * 60) - time.time()
            if wait_sec > 0:
                time.sleep(wait_sec)
            if not sess["active"]:
                return
            try:
                bot.edit_message_caption(
                    chat_id=sess["chat_id"],
                    message_id=sess["msg_id"],
                    caption=(
                        f"💳 <b>Scan QR Code to Pay</b>\n\n"
                        f"💵 <b>Amount:</b> ₹{sess['amount']:.2f}\n"
                        f"⏳ <b>Time Remaining:</b> ~{mins_left}:00 min"
                    )
                )
            except Exception:
                pass

        rem = sess["expires_at"] - time.time()
        if rem > 0:
            time.sleep(rem)
        if sess["active"]:
            sess["active"] = False
            try:
                bot.edit_message_caption(
                    chat_id=sess["chat_id"],
                    message_id=sess["msg_id"],
                    caption=(
                        f"❌ <b>QR Code Expired!</b>\n\n"
                        f"১০ মিনিট সময় শেষ হয়ে গেছে। আবার টাকা অ্যাড করতে Wallet থেকে চেষ্টা করুন।"
                    )
                )
            except Exception:
                pass

    threading.Thread(target=timer_worker, args=(user_id, session), daemon=True).start()


# ==========================================
# INLINE CALLBACK HANDLERS
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    data = call.data
    bot.answer_callback_query(call.id)

    if data.startswith("lang_"):
        lang_code = data.split("_")[-1]
        with db_lock:
            conn.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang_code, user_id))
            conn.commit()
        
        bot.send_message(
            chat_id,
            get_txt(user_id, "lang_changed"),
            reply_markup=main_menu_keyboard(user_id)
        )
        return

    if data == "skip_step_img":
        st = user_states.get(user_id)
        if st and st["state"] == "adm_prod_image":
            st["data"]["image_id"] = None
            st["state"] = "adm_prod_file"
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("⏭ Skip Tutorial", callback_data="skip_step_tut"))
            bot.send_message(chat_id, "📁 ছবি স্কিপ করা হয়েছে! এখন প্রোডাক্টের <b>File</b> আপলোড করুন অথবা ডাউনলোড <b>Link</b> পাঠান:", reply_markup=kb)
        return

    if data == "skip_step_tut":
        st = user_states.get(user_id)
        if st and st["state"] == "adm_prod_tutorial":
            st["data"]["tutorial_type"] = "none"
            st["data"]["tutorial_value"] = None
            save_new_product(chat_id, user_id, st["data"])
        return

    if data.startswith("view_prod_"):
        pid = int(data.split("_")[-1])
        with db_lock:
            c = conn.cursor()
            c.execute("SELECT * FROM products WHERE id = ?", (pid,))
            prod = c.fetchone()
        if not prod:
            bot.send_message(chat_id, "❌ প্রোডাক্টটি পাওয়া যায়নি।")
            return

        kb = types.InlineKeyboardMarkup()
        if prod["ptype"] == "free":
            text = (
                f"🆓 <b>{html.escape(prod['name'])}</b>\n\n"
                f"📝 {html.escape(prod['description'] or '')}\n\n"
                f"🪙 <b>Total Coin Price:</b> {int(prod['price'])} 🪙"
            )
            kb.row(
                types.InlineKeyboardButton("🪙 Earn Coin", callback_data="earn_coin_raffle"),
                types.InlineKeyboardButton("🛒 Buy", callback_data=f"buy_prod_{pid}")
            )
        else:
            text = (
                f"💎 <b>{html.escape(prod['name'])}</b>\n\n"
                f"📝 {html.escape(prod['description'] or '')}\n\n"
                f"💵 <b>Price:</b> ₹{prod['price']:.2f}"
            )
            kb.add(types.InlineKeyboardButton("🛒 Buy", callback_data=f"buy_prod_{pid}"))

        if prod["image_id"]:
            bot.send_photo(chat_id, prod["image_id"], caption=text, reply_markup=kb)
        else:
            bot.send_message(chat_id, text, reply_markup=kb)

    elif data == "earn_coin_raffle":
        send_raffle_status(chat_id, user_id)

    elif data.startswith("buy_prod_"):
        pid = int(data.split("_")[-1])
        user = get_user(user_id)
        with db_lock:
            c = conn.cursor()
            c.execute("SELECT * FROM products WHERE id = ?", (pid,))
            prod = c.fetchone()
        if not prod or not user:
            bot.send_message(chat_id, "❌ তথ্য পাওয়া যায়নি।")
            return

        kb = types.InlineKeyboardMarkup()
        if prod["ptype"] == "free":
            bal = user["coin_balance"]
            price = int(prod["price"])
            after = bal - price
            text = (
                f"🛒 <b>Purchase Confirmation</b>\n\n"
                f"📦 <b>Product:</b> {html.escape(prod['name'])}\n"
                f"🪙 <b>Your Coin Balance:</b> {bal} 🪙\n"
                f"🏷 <b>Product Price:</b> {price} 🪙\n"
                f"📊 <b>Balance After Buy:</b> {after} 🪙"
            )
            if after < 0:
                text += "\n\n❌ আপনার পর্যাপ্ত কয়েন নেই! কয়েন আয় করতে Earn Coin এ ক্লিক করুন।"
                kb.add(types.InlineKeyboardButton("🪙 Earn Coin", callback_data="earn_coin_raffle"))
            else:
                kb.add(types.InlineKeyboardButton("✅ Confirm", callback_data=f"conf_buy_{pid}"))
        else:
            bal = user["rs_balance"]
            price = prod["price"]
            after = bal - price
            text = (
                f"🛒 <b>Purchase Confirmation</b>\n\n"
                f"📦 <b>Product:</b> {html.escape(prod['name'])}\n"
                f"💵 <b>Your Rs. Balance:</b> ₹{bal:.2f}\n"
                f"🏷 <b>Product Price:</b> ₹{price:.2f}\n"
                f"📊 <b>Balance After Buy:</b> ₹{after:.2f}"
            )
            if after < 0:
                text += "\n\n❌ আপনার পর্যাপ্ত টাকা নেই! দয়া করে Wallet থেকে Add Rs. করুন।"
                kb.add(types.InlineKeyboardButton("➕ Add Rs.", callback_data="wallet_add_rs"))
            else:
                kb.add(types.InlineKeyboardButton("✅ Confirm", callback_data=f"conf_buy_{pid}"))

        bot.send_message(chat_id, text, reply_markup=kb)

    elif data.startswith("conf_buy_"):
        pid = int(data.split("_")[-1])
        with db_lock:
            c = conn.cursor()
            c.execute("SELECT * FROM products WHERE id = ?", (pid,))
            prod = c.fetchone()
            c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = c.fetchone()

            if not prod or not user:
                bot.send_message(chat_id, "❌ প্রোডাক্ট বা ইউজার পাওয়া যায়নি।")
                return

            if prod["ptype"] == "free":
                price = int(prod["price"])
                if user["coin_balance"] < price:
                    bot.send_message(chat_id, "❌ পর্যাপ্ত কয়েন নেই!")
                    return
                c.execute("UPDATE users SET coin_balance = coin_balance - ? WHERE user_id = ?", (price, user_id))
            else:
                price = prod["price"]
                if user["rs_balance"] < price:
                    bot.send_message(chat_id, "❌ পর্যাপ্ত Rs. ব্যালেন্স নেই!")
                    return
                c.execute("UPDATE users SET rs_balance = rs_balance - ? WHERE user_id = ?", (price, user_id))

            c.execute("""
                INSERT INTO purchases (user_id, product_id, ptype, product_name, price_paid, file_type, file_value, file_name, tutorial_type, tutorial_value, purchased_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, prod["id"], prod["ptype"], prod["name"], price,
                prod["file_type"], prod["file_value"], prod["file_name"],
                prod["tutorial_type"], prod["tutorial_value"], ist_now()
            ))
            pur_id = c.lastrowid
            conn.commit()

        deliver_product_file(
            chat_id, prod["name"], prod["file_type"], prod["file_value"],
            prod["file_name"], prod["tutorial_type"], prod["tutorial_value"], f"tut_pur_{pur_id}"
        )

    elif data.startswith("tut_pur_"):
        pur_id = int(data.split("_")[-1])
        with db_lock:
            c = conn.cursor()
            c.execute("SELECT product_name, tutorial_type, tutorial_value FROM purchases WHERE id = ?", (pur_id,))
            row = c.fetchone()
        if not row or row["tutorial_type"] == "none" or not row["tutorial_value"]:
            bot.send_message(chat_id, "ℹ️ এই প্রোডাক্টের জন্য কোনো Tutorial Video যুক্ত করা হয়নি।")
            return
        if row["tutorial_type"] == "video":
            bot.send_video(chat_id, row["tutorial_value"], caption=f"🎬 <b>Tutorial:</b> {html.escape(row['product_name'])}")
        else:
            bot.send_message(chat_id, f"🎬 <b>Tutorial Video ({html.escape(row['product_name'])}):</b>\n{html.escape(row['tutorial_value'])}")

    elif data in ("phist_free", "phist_paid"):
        ptype = "free" if data == "phist_free" else "paid"
        with db_lock:
            c = conn.cursor()
            c.execute("""
                SELECT id, product_name, purchased_at FROM purchases
                WHERE user_id = ? AND ptype = ?
                ORDER BY id DESC
            """, (user_id, ptype))
            rows = c.fetchall()

        if not rows:
            bot.send_message(chat_id, f"📜 আপনি এখনো কোনো {ptype.capitalize()} প্রোডাক্ট কেনেননি।")
            return

        kb = types.InlineKeyboardMarkup()
        for r in rows[:25]:
            kb.add(types.InlineKeyboardButton(f"📁 {r['product_name']} ({r['purchased_at']})", callback_data=f"hist_dl_{r['id']}"))
        bot.send_message(chat_id, f"📜 <b>{ptype.capitalize()} Purchase History</b>\nফাইল পেতে প্রোডাক্টে ক্লিক করুন 👇", reply_markup=kb)

    elif data.startswith("hist_dl_"):
        pur_id = int(data.split("_")[-1])
        with db_lock:
            c = conn.cursor()
            c.execute("SELECT * FROM purchases WHERE id = ? AND user_id = ?", (pur_id, user_id))
            row = c.fetchone()
        if not row:
            bot.send_message(chat_id, "❌ হিস্ট্রি পাওয়া যায়নি।")
            return
        deliver_product_file(
            chat_id, row["product_name"], row["file_type"], row["file_value"],
            row["file_name"], row["tutorial_type"], row["tutorial_value"], f"tut_pur_{pur_id}"
        )

    elif data == "wallet_add_rs":
        user_states[user_id] = {"state": "awaiting_add_rs_amount", "data": {}}
        bot.send_message(chat_id, "💵 আপনি কত টাকা (Rs.) অ্যাড করতে চান? পরিমাণ লিখুন (যেমন: 100):")

    elif data == "wallet_back":
        bot.send_message(chat_id, "🏠 মেইন মেনু:", reply_markup=main_menu_keyboard(user_id))

    elif data.startswith("adm_") or data.startswith("pay_"):
        if not is_admin(user_id):
            bot.send_message(chat_id, "🔒 আপনি Admin নন! প্রথমে Admin Login করুন।")
            return

        if data == "adm_logout":
            set_admin(user_id, False)
            clear_state(user_id)
            bot.send_message(chat_id, "👋 Admin থেকে লগআউট সম্পন্ন হয়েছে।", reply_markup=main_menu_keyboard(user_id))

        elif data == "adm_menu":
            clear_state(user_id)
            bot.send_message(chat_id, "🔐 <b>Admin Menu</b>", reply_markup=admin_menu_keyboard())

        elif data == "adm_add_prod":
            kb = types.InlineKeyboardMarkup()
            kb.row(
                types.InlineKeyboardButton("🆓 Free Product", callback_data="adm_new_free"),
                types.InlineKeyboardButton("💎 Paid Product", callback_data="adm_new_paid")
            )
            kb.add(types.InlineKeyboardButton("🔙 Back", callback_data="adm_menu"))
            bot.send_message(chat_id, "➕ কোন ধরনের প্রোডাক্ট যোগ করতে চান?", reply_markup=kb)

        elif data in ("adm_new_free", "adm_new_paid"):
            ptype = "free" if data == "adm_new_free" else "paid"
            user_states[user_id] = {"state": "adm_prod_name", "data": {"ptype": ptype}}
            bot.send_message(chat_id, f"📦 নতুন <b>{ptype.upper()}</b> প্রোডাক্টের <b>নাম (Title)</b> লিখুন:")

        elif data == "adm_manage_prod":
            with db_lock:
                c = conn.cursor()
                c.execute("SELECT id, ptype, name, price FROM products ORDER BY id DESC")
                rows = c.fetchall()
            if not rows:
                bot.send_message(chat_id, "❌ কোনো প্রোডাক্ট নেই।", reply_markup=admin_menu_keyboard())
                return
            kb = types.InlineKeyboardMarkup()
            for r in rows:
                tag = "🆓" if r["ptype"] == "free" else "💎"
                p_str = f"{int(r['price'])}🪙" if r["ptype"] == "free" else f"₹{r['price']:.0f}"
                kb.add(types.InlineKeyboardButton(f"{tag} {r['name']} ({p_str})", callback_data=f"adm_mp_{r['id']}"))
            kb.add(types.InlineKeyboardButton("🔙 Back", callback_data="adm_menu"))
            bot.send_message(chat_id, "🛠 <b>Manage Products</b>\nযে প্রোডাক্ট এডিট/ডিলিট করতে চান তাতে ক্লিক করুন:", reply_markup=kb)

        elif data.startswith("adm_mp_"):
            pid = int(data.split("_")[-1])
            with db_lock:
                c = conn.cursor()
                c.execute("SELECT * FROM products WHERE id = ?", (pid,))
                p = c.fetchone()
            if not p:
                bot.send_message(chat_id, "❌ প্রোডাক্ট পাওয়া যায়নি।")
                return
            kb = types.InlineKeyboardMarkup()
            kb.row(
                types.InlineKeyboardButton("✏️ Edit Name", callback_data=f"adm_en_{pid}"),
                types.InlineKeyboardButton("📝 Edit Desc", callback_data=f"adm_ed_{pid}")
            )
            kb.row(
                types.InlineKeyboardButton("💰 Edit Price", callback_data=f"adm_ep_{pid}"),
                types.InlineKeyboardButton("📁 Update File", callback_data=f"adm_ef_{pid}")
            )
            kb.row(
                types.InlineKeyboardButton("🎬 Update Tutorial", callback_data=f"adm_et_{pid}"),
                types.InlineKeyboardButton("🗑 Delete", callback_data=f"adm_del_{pid}")
            )
            kb.add(types.InlineKeyboardButton("🔙 Back", callback_data="adm_manage_prod"))
            bot.send_message(
                chat_id,
                f"🛠 <b>{html.escape(p['name'])}</b> ({p['ptype'].upper()})\n"
                f"💰 Price: {p['price']}\n"
                f"📝 Desc: {html.escape(p['description'] or '')}",
                reply_markup=kb
            )

        elif data.startswith("adm_en_"):
            pid = int(data.split("_")[-1])
            user_states[user_id] = {"state": "adm_edit_name", "data": {"pid": pid}}
            bot.send_message(chat_id, "✏️ প্রোডাক্টের নতুন নাম লিখুন:")

        elif data.startswith("adm_ed_"):
            pid = int(data.split("_")[-1])
            user_states[user_id] = {"state": "adm_edit_desc", "data": {"pid": pid}}
            bot.send_message(chat_id, "📝 প্রোডাক্টের নতুন Description লিখুন:")

        elif data.startswith("adm_ep_"):
            pid = int(data.split("_")[-1])
            user_states[user_id] = {"state": "adm_edit_price", "data": {"pid": pid}}
            bot.send_message(chat_id, "💰 নতুন দাম (সংখ্যা) লিখুন:")

        elif data.startswith("adm_ef_"):
            pid = int(data.split("_")[-1])
            user_states[user_id] = {"state": "adm_edit_file", "data": {"pid": pid}}
            bot.send_message(chat_id, "📁 নতুন ফাইল আপলোড করুন অথবা লিংক দিন:")

        elif data.startswith("adm_et_"):
            pid = int(data.split("_")[-1])
            user_states[user_id] = {"state": "adm_edit_tut", "data": {"pid": pid}}
            bot.send_message(chat_id, "🎬 নতুন Tutorial Video আপলোড করুন অথবা লিংক দিন:")

        elif data.startswith("adm_del_"):
            pid = int(data.split("_")[-1])
            with db_lock:
                conn.execute("DELETE FROM products WHERE id = ?", (pid,))
                conn.commit()
            bot.send_message(chat_id, "🗑 প্রোডাক্ট ডিলিট করা হয়েছে!", reply_markup=admin_menu_keyboard())

        elif data == "adm_dashboard":
            with db_lock:
                c = conn.cursor()
                total_users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                free_prods = c.execute("SELECT COUNT(*) FROM products WHERE ptype='free'").fetchone()[0]
                paid_prods = c.execute("SELECT COUNT(*) FROM products WHERE ptype='paid'").fetchone()[0]
                total_pur = c.execute("SELECT COUNT(*) FROM purchases").fetchone()[0]
                total_sales_rs = c.execute("SELECT COALESCE(SUM(price_paid), 0) FROM purchases WHERE ptype='paid'").fetchone()[0]
                total_added_rs = c.execute("SELECT COALESCE(SUM(amount), 0) FROM payment_requests WHERE status='approved'").fetchone()[0]
                pending_reqs = c.execute("SELECT COUNT(*) FROM payment_requests WHERE status='pending'").fetchone()[0]
                total_raffles = c.execute("SELECT COALESCE(SUM(total_raffles), 0) FROM users").fetchone()[0]

            bot.send_message(
                chat_id,
                f"📊 <b>Admin Dashboard</b>\n\n"
                f"👥 Total Users: <b>{total_users}</b>\n"
                f"🆓 Free Products: <b>{free_prods}</b>\n"
                f"💎 Paid Products: <b>{paid_prods}</b>\n"
                f"🛒 Total Purchases: <b>{total_pur}</b>\n"
                f"💰 Paid Sales Revenue: <b>₹{total_sales_rs:.2f}</b>\n"
                f"💳 Total Approved Deposits: <b>₹{total_added_rs:.2f}</b>\n"
                f"📥 Pending Payment Requests: <b>{pending_reqs}</b>\n"
                f"🎟 Total Raffles: <b>{total_raffles}</b>",
                reply_markup=admin_menu_keyboard()
            )

        elif data.startswith("adm_users_"):
            offset = int(data.split("_")[-1])
            limit = 15
            with db_lock:
                c = conn.cursor()
                total = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                rows = c.execute("SELECT * FROM users ORDER BY joined_at DESC LIMIT ? OFFSET ?", (limit, offset)).fetchall()

            lines = [f"👥 <b>Users List (Total: {total})</b>\n"]
            for u in rows:
                lines.append(
                    f"🆔 <code>{u['user_id']}</code> | {html.escape(u['full_name'])} ({html.escape(u['username'])})\n"
                    f"   💵 ₹{u['rs_balance']:.2f} | 🪙 {u['coin_balance']} | 🎟 {u['total_raffles']}"
                )
            kb = types.InlineKeyboardMarkup()
            nav = []
            if offset > 0:
                nav.append(types.InlineKeyboardButton("⬅️ Prev", callback_data=f"adm_users_{max(0, offset - limit)}"))
            if offset + limit < total:
                nav.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"adm_users_{offset + limit}"))
            if nav:
                kb.row(*nav)
            kb.add(types.InlineKeyboardButton("🔙 Back", callback_data="adm_menu"))
            bot.send_message(chat_id, "\n".join(lines), reply_markup=kb)

        elif data == "adm_money_hist":
            with db_lock:
                c = conn.cursor()
                rows = c.execute("SELECT * FROM payment_requests ORDER BY id DESC LIMIT 25").fetchall()
            if not rows:
                bot.send_message(chat_id, "💳 কোনো Add Money History নেই।", reply_markup=admin_menu_keyboard())
                return
            lines = ["💳 <b>Add Money History (Last 25)</b>\n"]
            for r in rows:
                st_icon = "✅" if r["status"] == "approved" else ("❌" if r["status"] == "rejected" else "⏳")
                lines.append(
                    f"{st_icon} <b>#{r['id']}</b> | ₹{r['amount']:.2f} | {html.escape(r['full_name'])} "
                    f"(<code>{r['user_id']}</code>) | {r['status'].upper()} | {r['created_at']}"
                )
            bot.send_message(chat_id, "\n".join(lines), reply_markup=admin_menu_keyboard())

        elif data == "adm_bonus":
            kb = types.InlineKeyboardMarkup()
            kb.row(
                types.InlineKeyboardButton("💵 Rs. Bonus", callback_data="adm_btype_rs"),
                types.InlineKeyboardButton("🪙 Coin Bonus", callback_data="adm_btype_coin")
            )
            kb.add(types.InlineKeyboardButton("🔙 Back", callback_data="adm_menu"))
            bot.send_message(chat_id, "🎁 কোন ধরনের বোনাস পাঠাতে চান?", reply_markup=kb)

        elif data in ("adm_btype_rs", "adm_btype_coin"):
            btype = "rs" if data == "adm_btype_rs" else "coin"
            user_states[user_id] = {"state": "adm_bonus_target", "data": {"btype": btype}}
            bot.send_message(chat_id, "👤 যাকে বোনাস দিতে চান তার <b>User ID</b> লিখুন (সবাইকে দিতে চাইলে <code>ALL</code> লিখুন):")

        elif data == "adm_notify":
            user_states[user_id] = {"state": "adm_broadcast", "data": {}}
            bot.send_message(chat_id, "📢 সব ইউজারকে পাঠানোর জন্য আপনার মেসেজ অথবা ক্যাপশনসহ ছবি পাঠান:")

        elif data == "adm_leaderboard":
            with db_lock:
                c = conn.cursor()
                rows = c.execute("""
                    SELECT user_id, full_name, username, total_raffles, coin_balance
                    FROM users
                    ORDER BY total_raffles DESC, coin_balance DESC
                    LIMIT 20
                """).fetchall()
            if not rows:
                bot.send_message(chat_id, "🏆 এখনো কোনো ইউজার নেই।", reply_markup=admin_menu_keyboard())
                return
            lines = ["🏆 <b>Raffle Leaderboard (Top 20)</b>\n"]
            for i, r in enumerate(rows, 1):
                lines.append(
                    f"{i}. <b>{html.escape(r['full_name'])}</b> ({html.escape(r['username'])})\n"
                    f"   🎟 Raffles: <b>{r['total_raffles']}</b> | 🪙 Coins: {r['coin_balance']}"
                )
            bot.send_message(chat_id, "\n".join(lines), reply_markup=admin_menu_keyboard())

        elif data == "adm_pay_reqs":
            with db_lock:
                c = conn.cursor()
                rows = c.execute("SELECT * FROM payment_requests WHERE status = 'pending' ORDER BY id ASC").fetchall()
            if not rows:
                bot.send_message(chat_id, "📥 কোনো Pending Payment Request নেই।", reply_markup=admin_menu_keyboard())
                return
            for r in rows:
                kb = types.InlineKeyboardMarkup()
                kb.row(
                    types.InlineKeyboardButton("✅ Approve", callback_data=f"pay_app_{r['id']}"),
                    types.InlineKeyboardButton("❌ Reject", callback_data=f"pay_rej_{r['id']}")
                )
                bot.send_photo(
                    chat_id,
                    r["screenshot_file_id"],
                    caption=(
                        f"📥 <b>Payment Request #{r['id']}</b>\n\n"
                        f"👤 Name: {html.escape(r['full_name'])}\n"
                        f"🔗 Username: {html.escape(r['username'])}\n"
                        f"🆔 User ID: <code>{r['user_id']}</code>\n"
                        f"💵 Amount: <b>₹{r['amount']:.2f}</b>\n"
                        f"🕒 Time: {r['created_at']}"
                    ),
                    reply_markup=kb
                )

        elif data.startswith("pay_app_") or data.startswith("pay_rej_"):
            approve = data.startswith("pay_app_")
            req_id = int(data.split("_")[-1])
            with db_lock:
                c = conn.cursor()
                c.execute("SELECT * FROM payment_requests WHERE id = ?", (req_id,))
                req = c.fetchone()
                if not req:
                    bot.send_message(chat_id, "❌ রিকোয়েস্ট পাওয়া যায়নি।")
                    return
                if req["status"] != "pending":
                    bot.send_message(chat_id, f"ℹ️ রিকোয়েস্ট #{req_id} আগেই {req['status'].upper()} করা হয়েছে।")
                    return

                new_status = "approved" if approve else "rejected"
                c.execute("UPDATE payment_requests SET status = ?, reviewed_at = ? WHERE id = ?", (new_status, ist_now(), req_id))
                if approve:
                    c.execute("UPDATE users SET rs_balance = rs_balance + ? WHERE user_id = ?", (req["amount"], req["user_id"]))
                conn.commit()

            if approve:
                try:
                    bot.edit_message_caption(
                        chat_id=chat_id,
                        message_id=call.message.message_id,
                        caption=f"✅ <b>APPROVED Request #{req_id}</b> | ₹{req['amount']:.2f} | User: <code>{req['user_id']}</code>"
                    )
                except Exception:
                    pass
                try:
                    bot.send_message(req["user_id"], f"✅ আপনার <b>₹{req['amount']:.2f}</b> পেমেন্ট রিকোয়েস্ট (#{req_id}) <b>Approved</b> হয়েছে এবং Wallet-এ টাকা যোগ হয়েছে!")
                except Exception:
                    pass
            else:
                try:
                    bot.edit_message_caption(
                        chat_id=chat_id,
                        message_id=call.message.message_id,
                        caption=f"❌ <b>REJECTED Request #{req_id}</b> | ₹{req['amount']:.2f} | User: <code>{req['user_id']}</code>"
                    )
                except Exception:
                    pass
                try:
                    bot.send_message(req["user_id"], f"❌ আপনার <b>₹{req['amount']:.2f}</b> পেমেন্ট রিকোয়েস্ট (#{req_id}) <b>Rejected</b> হয়েছে। বিস্তারিত জানতে সাপোর্টে যোগাযোগ করুন।")
                except Exception:
                    pass


# ==========================================
# WEB SERVER KEEP-ALIVE
# ==========================================
class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Telegram Bot is running!")

    def log_message(self, format, *args):
        return


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), KeepAliveHandler)
    server.serve_forever()


if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    print("Bot is running...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
