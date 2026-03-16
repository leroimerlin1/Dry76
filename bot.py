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
# CONFIGURATION - À MODIFIER SI BESOIN
# =============================================================

TOKEN = "8586174802:AAEJ294yeBBufP9O29wJOHHTdFoLciQtmgE"

CHANNEL_ID = -1003798159205          # ID du canal Telegram (avec le -100...)
CHANNEL_LINK = "https://t.me/+xkLrkV6xQBQ2OTQ0"

MINI_APP_URL = "https://leroimerlin1.github.io/Dry76/"

# Fichier image de bienvenue (changé en .jpg)
IMAGE_WELCOME = "chat.jpg"

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
• Supérieur à 25 km : 380€

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
        logger.error(f"Erreur lors de la vérification d'abonnement : {e}")
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

    # Utilisateur abonné → photo + menu
    try:
        with open(IMAGE_WELCOME, "rb") as photo_file:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=photo_file,
                caption=(
                    "Bienvenue chez Bart Coffee76 🔥\n\n"
                    "Choisis une option ci-dessous :"
                ),
                reply_markup=get_main_menu_keyboard()
            )
    except FileNotFoundError:
        logger.warning(f"Image non trouvée : {IMAGE_WELCOME}")
        await update.message.reply_text(
            "Bienvenue chez Bart Coffee76 🔥\n\n"
            f"(image '{IMAGE_WELCOME}' introuvable dans le dossier du bot)\n\n"
            "Choisis une option :",
            reply_markup=get_main_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de la photo : {e}")
        await update.message.reply_text(
            "Bienvenue chez Bart Coffee76 🔥\n\n"
            "Choisis une option :",
            reply_markup=get_main_menu_keyboard()
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if not await check_subscription(user_id, context):
        await query.answer("❌ Tu dois être abonné au canal.", show_alert=True)
        return

    # ──────────────── Retour au menu principal ────────────────
    if data == "back":
        try:
            await query.message.delete()
        except:
            pass

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Menu principal :",
            reply_markup=get_main_menu_keyboard()
        )
        return

    # ──────────────── Contact ────────────────
    if data == "contact":
        try:
            await query.message.delete()
        except:
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
        except:
            pass

        keyboard = [[InlineKeyboardButton("← Retour", callback_data="back")]]

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=INFO_TEXT,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # ──────────────── Vérification abonnement (depuis l'écran non abonné) ────────────────
    if data == "check_sub":
        if await check_subscription(user_id, context):
            try:
                await query.message.delete()
            except:
                pass

            try:
                with open(IMAGE_WELCOME, "rb") as photo_file:
                    await context.bot.send_photo(
                        chat_id=query.message.chat_id,
                        photo=photo_file,
                        caption="✅ Accès autorisé !\n\nChoisis une option :",
                        reply_markup=get_main_menu_keyboard()
                    )
            except FileNotFoundError:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="✅ Accès autorisé !\n\n"
                         f"(image '{IMAGE_WELCOME}' introuvable)\n\n"
                         "Choisis une option :",
                    reply_markup=get_main_menu_keyboard()
                )
            except Exception as e:
                logger.error(f"Erreur envoi photo après check_sub : {e}")
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="✅ Accès autorisé !\n\nChoisis une option :",
                    reply_markup=get_main_menu_keyboard()
                )
        else:
            await query.answer("❌ Tu n'es toujours pas abonné.", show_alert=True)


# =============================================================
# LANCEMENT
# =============================================================

def main():
    app = ApplicationBuilder() \
        .token(TOKEN) \
        .build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot démarré → Bart Coffee76  |  Image utilisée : chat.jpg")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
