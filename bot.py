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
CHANNEL_LINK = "https://t.me/+xkLrkV6xQBQ2OTQ0"
MINI_APP_URL = "https://leroimerlin1.github.io/Dry76/"
IMAGE_WELCOME = "chat.jpg"
ADMIN_ID = 7457384429
DB_PATH = "users.db"  # Fichier base de données (remplace users.json)

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
       [
           InlineKeyboardButton("📩 Contact", callback_data="contact"),
           InlineKeyboardButton("ℹ️ Informations", callback_data="info"),
       ],
       [
           InlineKeyboardButton("🛍 Ouvrir la boutique", web_app=WebAppInfo(url=MINI_APP_URL))
       ]
   ]
   return InlineKeyboardMarkup(keyboard)


async def send_welcome_menu(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
   try:
       with open(IMAGE_WELCOME, "rb") as photo_file:
           await context.bot.send_photo(
               chat_id=chat_id,
               photo=photo_file,
               caption=(
                   "Bienvenue chez Bart Coffee76 🔥\n\n"
                   "Choisis une option ci-dessous :"
               ),
               reply_markup=get_main_menu_keyboard()
           )
   except FileNotFoundError:
       await context.bot.send_message(
           chat_id=chat_id,
           text="Bienvenue chez Bart Coffee76 🔥\n\nChoisis une option :",
           reply_markup=get_main_menu_keyboard()
       )

# =============================================================
# JOB QUOTIDIEN 11H
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

    logger.info(f"Message quotidien envoyé → {sent} succès, {failed} échecs")

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
        await update.message.reply_text("❌ Tu n'as pas la permission d'utiliser cette commande.")
        return

    text = update.message.text.partition("/broadcast")[2].strip()
    if not text:
        await update.message.reply_text(
            "⚠️ Écris ton message après la commande !\n\nExemple :\n/broadcast Salut tout le monde 🔥"
        )
        return

    users = load_users()
    if not users:
        await update.message.reply_text("⚠️ Aucun utilisateur enregistré pour l'instant.")
        return

    sent = 0
    failed = 0
    await update.message.reply_text(f"📤 Envoi en cours à {len(users)} utilisateurs...")

    for chat_id in users:
        try:
            await context.bot.send_message(chat_id=int(chat_id), text=text)
            sent += 1
        except Exception as e:
            logger.warning(f"Impossible d'envoyer à {chat_id} : {e}")
            failed += 1
        await asyncio.sleep(0.05)

    await update.message.reply_text(
        f"✅ Broadcast terminé !\n\n• Envoyés : {sent}\n• Échecs : {failed}"
    )


async def users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id != ADMIN_ID:
        await update.message.reply_text("❌ Tu n'as pas la permission d'utiliser cette commande.")
        return

    users = load_users()
    if not users:
        await update.message.reply_text("⚠️ Aucun utilisateur enregistré pour l'instant.")
        return

    lines = [f"👥 Utilisateurs enregistrés : {len(users)}\n"]
    for i, (uid, info) in enumerate(users.items(), 1):
        first_name = info.get("first_name", "?")
        username = info.get("username", "?")
        uname_display = f"@{username}" if username != "?" else "pas de @"
        lines.append(f"{i}. {first_name} ({uname_display}) — {uid}")

    message = "\n".join(lines)
    if len(message) <= 4096:
        await update.message.reply_text(message)
    else:
        chunks = []
        current = ""
        for line in lines:
            if len(current) + len(line) + 1 > 4096:
                chunks.append(current)
                current = line
            else:
                current += "\n" + line
        if current:
            chunks.append(current)
        for chunk in chunks:
            await update.message.reply_text(chunk)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
   query = update.callback_query
   await query.answer()
   data = query.data

   if data == "back":
       try:
           await query.message.delete()
       except Exception:
           pass
       await send_welcome_menu(query.message.chat_id, context)
       return

   if data == "contact":
       try:
           await query.message.delete()
       except Exception:
           pass
       keyboard = [
           [InlineKeyboardButton("💬 Contacter le support", url="https://t.me/sav_Bart76")],
           [InlineKeyboardButton("← Retour", callback_data="back")]
       ]
       await context.bot.send_message(
           chat_id=query.message.chat_id,
           text="Tu veux parler à l'équipe ?\n\nClique ci-dessous pour ouvrir le chat privé :",
           reply_markup=InlineKeyboardMarkup(keyboard)
       )
       return

   if data == "info":
       try:
           await query.message.delete()
       except Exception:
           pass
       keyboard = [[InlineKeyboardButton("← Retour", callback_data="back")]]
       await context.bot.send_message(
           chat_id=query.message.chat_id,
           text=INFO_TEXT,
           reply_markup=InlineKeyboardMarkup(keyboard)
       )
       return

# =============================================================
# LANCEMENT
# =============================================================

def main():
   app = ApplicationBuilder() \
       .token(TOKEN) \
       .build()

   app.add_handler(CommandHandler("start", start))
   app.add_handler(CommandHandler("broadcast", broadcast))
   app.add_handler(CommandHandler("users", users_list))
   app.add_handler(CallbackQueryHandler(button_handler))

   PARIS = timezone(timedelta(hours=2))
   job_queue = app.job_queue
   job_queue.run_daily(
       daily_message_job,
       time=time(hour=11, minute=0, second=0, tzinfo=PARIS),
       name="daily_open_message"
   )

   print("Bot démarré → Bart Coffee76  |  Image : chat.jpg")
   app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
   main()
