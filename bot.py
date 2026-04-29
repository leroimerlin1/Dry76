import logging
import json
import os
import asyncio
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
    ContextTypes
)

# =============================================================
# CONFIGURATION
# =============================================================

TOKEN = "8586174802:AAEJ294yeBBufP9O29wJOHHTdFoLciQtmgE"

CHANNEL_ID = -1003798159205          # ID du canal (avec -100...)
CHANNEL_LINK = "https://t.me/+xkLrkV6xQBQ2OTQ0"

MINI_APP_URL = "https://leroimerlin1.github.io/Dry76/"

IMAGE_WELCOME = "chat.jpg"           # ← fichier à placer dans le même dossier

# ⚠️ Mets ton propre Telegram user ID ici (pour protéger /broadcast)
ADMIN_ID = 8313494819  # ← REMPLACE PAR TON VRAI ID

# Fichier où les utilisateurs sont sauvegardés
USERS_FILE = "users.json"

# Texte Informations
INFO_TEXT = """Information de Dry.Coffee76

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

# Message du broadcast
BROADCAST_TEXT = """Salut 👋 l'équipe

Nouvelle mise à jour sur la mini-app, vous pouvez désormais mettre votre avis ⭐️ sur le canal en général et il y a un nouveau chat 📝 pour la communauté"""

# =============================================================
# LOGGING
# =============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# =============================================================
# GESTION DES UTILISATEURS (stockage JSON)
# =============================================================

def load_users() -> set:
    """Charge les utilisateurs depuis le fichier JSON."""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def save_user(user_id: int):
    """Ajoute un utilisateur et sauvegarde dans le fichier JSON."""
    users = load_users()
    users.add(user_id)
    with open(USERS_FILE, "w") as f:
        json.dump(list(users), f)


# =============================================================
# FONCTIONS UTILITAIRES
# =============================================================

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Erreur vérif abonnement : {e}")
        return False


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
    """
    Envoie exactement le même message de bienvenue que /start (photo + texte + boutons)
    """
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
        logger.warning(f"Image introuvable : {IMAGE_WELCOME}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "Bienvenue chez Bart Coffee76 🔥\n\n"
                f"(image '{IMAGE_WELCOME}' introuvable dans le dossier)\n\n"
                "Choisis une option :"
            ),
            reply_markup=get_main_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Erreur envoi photo : {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="Bienvenue chez Bart Coffee76 🔥\n\nChoisis une option :",
            reply_markup=get_main_menu_keyboard()
        )


# =============================================================
# HANDLERS
# =============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    # ✅ Sauvegarde automatique de l'utilisateur
    save_user(user.id)

    is_sub = await check_subscription(user.id, context)

    if not is_sub:
        keyboard = [
            [InlineKeyboardButton("🔔 Rejoindre le canal", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ Vérifier l'abonnement", callback_data="check_sub")]
        ]
        await update.message.reply_text(
            "🤴 Bart Coffee76\n\n"
            "✅ Boutique privée premium\n\n"
            "⚠️ Pour accéder à la boutique, rejoins notre canal officiel d'abord.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Abonné → menu avec photo
    await send_welcome_menu(update.effective_chat.id, context)


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Commande /broadcast — réservée à l'admin.
    Envoie le message BROADCAST_TEXT à tous les utilisateurs enregistrés.
    """
    user = update.effective_user
    if not user or user.id != ADMIN_ID:
        await update.message.reply_text("❌ Tu n'as pas la permission d'utiliser cette commande.")
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
            await context.bot.send_message(chat_id=chat_id, text=BROADCAST_TEXT)
            sent += 1
        except Exception as e:
            logger.warning(f"Impossible d'envoyer à {chat_id} : {e}")
            failed += 1
        await asyncio.sleep(0.05)  # Respect du rate limit Telegram

    await update.message.reply_text(
        f"✅ Broadcast terminé !\n\n"
        f"• Envoyés : {sent}\n"
        f"• Échecs : {failed}"
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if not await check_subscription(user_id, context):
        await query.answer("❌ Tu dois être abonné au canal.", show_alert=True)
        return

    # ──────────────── RETOUR → même message que /start ────────────────
    if data == "back":
        try:
            await query.message.delete()
        except Exception:
            pass

        await send_welcome_menu(query.message.chat_id, context)
        return

    # ──────────────── Contact ────────────────
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

    # ──────────────── Informations ────────────────
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

    # ──────────────── Vérification abonnement ────────────────
    if data == "check_sub":
        if await check_subscription(user_id, context):
            try:
                await query.message.delete()
            except Exception:
                pass
            await send_welcome_menu(query.message.chat_id, context)
        else:
            await query.answer("❌ Toujours pas abonné au canal.", show_alert=True)


# =============================================================
# LANCEMENT
# =============================================================

def main():
    app = ApplicationBuilder() \
        .token(TOKEN) \
        .build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))  # ← Nouveau
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot démarré → Bart Coffee76  |  Image : chat.jpg")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
