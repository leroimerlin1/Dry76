import logging
import json
import os
import asyncio
import sqlite3
from datetime import time, timezone, timedelta
from telegram import (
   Update,
   InlineKeyboardButton,
   InlineKeyboardMarkup,
   WebAppInfo
)
from telegram.ext import (
   ApplicationBuilder,
   CommandHandler,
   CallbackQueryHandler,
   ContextTypes,
   JobQueue
)

# =============================================================
# CONFIGURATION
# =============================================================

TOKEN = "8586174802:AAEJ294yeBBufP9O29wJOHHTdFoLciQtmgE"
MINI_APP_URL = "https://leroimerlin1.github.io/Dry76/"
IMAGE_WELCOME = "chat.jpg"
ADMIN_ID = 7457384429
DB_PATH = "users.db"

DAILY_MESSAGE = """✅ Les commandes sont ouvertes 📦

📍 Meet-Up Dispo ✅

🚚 Livraison Dispo ✅

Fait /start pour relancer le bot 🤖"""

INFO_TEXT = """Information de Bart.Coffee76

Pour toutes commande, une carte d'identité 🪪 est nécessaire et une photo 📸 de vous.

Contact secrétaire : @sav_Bart76

Info Livraison 🚚

Zone de livraison
76 / 27 / 14

• Sur Rouen : 70€
• Moins de 10 km de Rouen : 100€
• Supérieur à 10 km : 150€
• Supérieur à 25 km : 270€

Frais de livraison obligatoire s'il n'y a pas de tournée !

Info Meet-up 📍

Nous sommes situé sur Rouen Rive Gauche 📍

50€ de commande minimum pour venir sur place"""

# =============================================================
# LOGGING
# =============================================================

logging.basicConfig(
   format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
   level=logging.INFO
)
logger = logging.getLogger(__name__)

# =============================================================
# GESTION DES UTILISATEURS (SQLite)
# =============================================================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            first_name TEXT,
            username TEXT
        )
    """)
    conn.commit()
    return conn

def save_user(user_id: int, first_name: str = "?", username: str = None):
    conn = get_db()
    conn.execute("""
        INSERT INTO users (user_id, first_name, username)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            first_name=excluded.first_name,
            username=excluded.username
    """, (str(user_id), first_name, username or "?"))
    conn.commit()
    conn.close()

def load_users() -> dict:
    conn = get_db()
    rows = conn.execute("SELECT user_id, first_name, username FROM users").fetchall()
    conn.close()
    return {row[0]: {"first_name": row[1], "username": row[2]} for row in rows}

# =============================================================
# FONCTIONS UTILITAIRES
# =============================================================

def get_main_menu_keyboard():
   keyboard = [
       [InlineKeyboardButton("🛍 Ouvrir la boutique", web_app=WebAppInfo(url=MINI_APP_URL))],
       [
           InlineKeyboardButton("📍 Meet-up", callback_data="meetup"),
           InlineKeyboardButton("🚚 Livraison", callback_data="delivery")
       ],
       [
           InlineKeyboardButton("📩 Contact", callback_data="contact"),
           InlineKeyboardButton("ℹ️ Informations", callback_data="info")
       ]
   ]
   return InlineKeyboardMarkup(keyboard)


async def delete_previous_message(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Supprime l'ancien message du bot"""
    last_msg_id = context.user_data.get('last_bot_message_id')
    if last_msg_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=last_msg_id)
        except Exception:
            pass
        context.user_data['last_bot_message_id'] = None


async def send_welcome_menu(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
   await delete_previous_message(chat_id, context)

   try:
       with open(IMAGE_WELCOME, "rb") as photo_file:
           msg = await context.bot.send_photo(
               chat_id=chat_id,
               photo=photo_file,
               caption="Bienvenue chez Bart Coffee76 🔥\n\nChoisis une option ci-dessous :",
               reply_markup=get_main_menu_keyboard()
           )
           context.user_data['last_bot_message_id'] = msg.message_id
   except FileNotFoundError:
       msg = await context.bot.send_message(
           chat_id=chat_id,
           text="Bienvenue chez Bart Coffee76 🔥\n\nChoisis une option :",
           reply_markup=get_main_menu_keyboard()
       )
       context.user_data['last_bot_message_id'] = msg.message_id


# =============================================================
# JOB QUOTIDIEN
# =============================================================

async def daily_message_job(context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    if not users:
        logger.info("Aucun utilisateur pour le message quotidien.")
        return

    sent = 0
    failed = 0
    for chat_id in users:
        try:
            await context.bot.send_message(chat_id=int(chat_id), text=DAILY_MESSAGE)
            sent += 1
        except Exception as e:
            logger.warning(f"Impossible d'envoyer à {chat_id} : {e}")
            failed += 1
        await asyncio.sleep(0.05)

    logger.info(f"Message quotidien → {sent} succès, {failed} échecs")


# =============================================================
# HANDLERS
# =============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
   user = update.effective_user
   if not user:
       return
   save_user(user.id, first_name=user.first_name or "?", username=user.username)
   await send_welcome_menu(update.effective_chat.id, context)


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id != ADMIN_ID:
        await update.message.reply_text("❌ Tu n'as pas la permission.")
        return

    text = update.message.text.partition("/broadcast")[2].strip()
    if not text:
        await update.message.reply_text("⚠️ Écris ton message après /broadcast")
        return

    users = load_users()
    sent = failed = 0
    await update.message.reply_text(f"📤 Envoi à {len(users)} utilisateurs...")

    for chat_id in users:
        try:
            await context.bot.send_message(chat_id=int(chat_id), text=text)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await update.message.reply_text(f"✅ Broadcast terminé !\nEnvoyés : {sent}\nÉchecs : {failed}")


async def users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id != ADMIN_ID:
        await update.message.reply_text("❌ Accès refusé.")
        return

    users = load_users()
    if not users:
        await update.message.reply_text("Aucun utilisateur.")
        return

    lines = [f"👥 Utilisateurs : {len(users)}\n"]
    for i, (uid, info) in enumerate(users.items(), 1):
        name = info.get("first_name", "?")
        uname = f"@{info.get('username')}" if info.get("username") != "?" else "pas de @"
        lines.append(f"{i}. {name} ({uname}) — {uid}")

    await update.message.reply_text("\n".join(lines))


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
   query = update.callback_query
   await query.answer()
   data = query.data
   chat_id = query.message.chat_id

   await delete_previous_message(chat_id, context)

   if data == "back":
       await send_welcome_menu(chat_id, context)
       return

   if data == "contact":
       keyboard = [
           [InlineKeyboardButton("💬 Contacter le support", url="https://t.me/sav_Bart76")],
           [InlineKeyboardButton("← Retour", callback_data="back")]
       ]
       msg = await context.bot.send_message(chat_id=chat_id, text="Tu veux parler à l'équipe ?", reply_markup=InlineKeyboardMarkup(keyboard))
       context.user_data['last_bot_message_id'] = msg.message_id
       return

   if data == "info":
       keyboard = [[InlineKeyboardButton("← Retour", callback_data="back")]]
       msg = await context.bot.send_message(chat_id=chat_id, text=INFO_TEXT, reply_markup=InlineKeyboardMarkup(keyboard))
       context.user_data['last_bot_message_id'] = msg.message_id
       return

   if data == "meetup":
       keyboard = [[InlineKeyboardButton("← Retour", callback_data="back")]]
       msg = await context.bot.send_message(chat_id=chat_id, text="📍 **Meet-up**\n\nRouen Rive Gauche\nMinimum 50€ de commande.", reply_markup=InlineKeyboardMarkup(keyboard))
       context.user_data['last_bot_message_id'] = msg.message_id
       return

   if data == "delivery":
       keyboard = [[InlineKeyboardButton("← Retour", callback_data="back")]]
       msg = await context.bot.send_message(chat_id=chat_id, text="🚚 **Livraison**\n\nZone : 76/27/14\n\n• Rouen : 70€\n• <10km : 100€\n• +10km : 150€\n• +25km : 270€", reply_markup=InlineKeyboardMarkup(keyboard))
       context.user_data['last_bot_message_id'] = msg.message_id
       return


# =============================================================
# LANCEMENT
# =============================================================

def main():
   app = ApplicationBuilder().token(TOKEN).build()

   app.add_handler(CommandHandler("start", start))
   app.add_handler(CommandHandler("broadcast", broadcast))
   app.add_handler(CommandHandler("users", users_list))
   app.add_handler(CallbackQueryHandler(button_handler))

   PARIS = timezone(timedelta(hours=2))
   app.job_queue.run_daily(
       daily_message_job,
       time=time(hour=11, minute=0, second=0, tzinfo=PARIS)
   )

   print("🤖 Bot Bart Coffee76 démarré avec succès !")
   app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
   main()
