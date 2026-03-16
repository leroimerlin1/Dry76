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
    ContextTypes,
    MessageHandler,
    filters
)

# 🔐 METS TON TOKEN ICI
token = "8586174802:AAEJ294yeBBufP9O29wJOHHTdFoLciQtmgE"

CHANNEL_ID = -1003798159205   # ← change si besoin
CHANNEL_LINK = "https://t.me/+xkLrkV6xQBQ2OTQ0"
MINI_APP_URL = "https://leroimerlin1.github.io/Dry76/"

# Ton texte d'information (exactement comme demandé)
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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ================================
# Vérification abonnement
# ================================
async def check_subscription(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logging.error(f"Erreur vérif abonnement : {e}")
        return False


# ================================
# Clavier principal (Contact + Infos)
# ================================
def get_main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("📩 Contact", callback_data="contact"),
            InlineKeyboardButton("ℹ️ Informations", callback_data="info")
        ],
        [InlineKeyboardButton("🛍 Ouvrir la boutique", web_app=WebAppInfo(url=MINI_APP_URL))]
    ]
    return InlineKeyboardMarkup(keyboard)


# ================================
# Commande /start
# ================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    is_subscribed = await check_subscription(user.id, context)

    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("🔔 Rejoindre le canal", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ Vérifier l'abonnement", callback_data="check_sub")]
        ]
        await update.message.reply_text(
            "🤴 Bart Coffee76\n\n"
            "✅ Boutique privée premium\n\n"
            "⚠️ Pour accéder à la boutique, rejoins notre canal officiel.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Abonné → menu principal
    await update.message.reply_text(
        "Bienvenue chez Bart Coffee76 🔥\n\n"
        "Choisis une option :",
        reply_markup=get_main_menu_keyboard()
    )


# ================================
# Gestion des boutons
# ================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    data = query.data

    # Vérif abonnement au cas où
    if not await check_subscription(user.id, context):
        await query.answer("❌ Tu dois être abonné au canal.", show_alert=True)
        return

    # ─────────────────────────────────────
    # Retour au menu principal
    # ─────────────────────────────────────
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

    # ─────────────────────────────────────
    # Contact → lien vers @sav_Bart76
    # ─────────────────────────────────────
    if data == "contact":
        try:
            await query.message.delete()
        except:
            pass

        keyboard = [[InlineKeyboardButton("← Retour", callback_data="back")]]
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Contacte le support ici :\n\n@sav_Bart76",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # ─────────────────────────────────────
    # Informations
    # ─────────────────────────────────────
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

    # Cas fallback (check_sub par ex.)
    if data == "check_sub":
        is_sub = await check_subscription(user.id, context)
        if is_sub:
            try:
                await query.message.delete()
            except:
                pass
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="✅ Accès autorisé !\n\nChoisis une option :",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await query.answer("❌ Pas encore abonné.", show_alert=True)


# ================================
# Lancement
# ================================
def main():
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot lancé 🚀")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
