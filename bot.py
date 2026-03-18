import logging
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

# Texte Informations
INFO_TEXT = """Information de Dry.Coffee76

Pour toutes commande, une carte d’identité 🪪 est nécessaire et une photo 📸 de vous.

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
            pass  # on continue même si suppression échoue

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
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot démarré → Bart Coffee76  |  Image : chat.jpg")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
