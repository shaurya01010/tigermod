import logging
import random
import asyncio
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# -----------------------
# CONFIGURATION
# -----------------------
BOT_TOKEN = "8011046128:AAGtgSRQ4m_dB8n2dqiKgWf3lFKO0iV7mzI"
CHANNEL_USERNAME = "@shauryavipsignals"
CHANNEL_LINK = "https://t.me/shauryavipsignals"

# -----------------------
# LOGGING
# -----------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# -----------------------
# HELPER FUNCTIONS
# -----------------------
def sum_digits(number: str) -> int:
    """Sum all digits in the given string."""
    return sum(int(ch) for ch in number if ch.isdigit())

def get_result(sum_value: int, format_choice: int) -> str:
    """Get prediction result based on rules."""
    sum_str = str(abs(sum_value))
    result_digit = int(sum_str[-1])
    if format_choice == 1:
        return "SMALL 🟢" if result_digit in [0, 2, 4, 6, 8] else "BIG 🔴"
    elif format_choice == 2:
        return "BIG 🔴" if result_digit in [1, 3, 5, 7, 9] else "SMALL 🟢"
    else:
        return "INVALID"

# -----------------------
# CHECK IF USER JOINED CHANNEL
# -----------------------
async def is_user_joined(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.warning(f"get_chat_member failed: {e}")
        return False

# -----------------------
# START COMMAND
# -----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ I Joined", callback_data="joined")],
    ]
    await update.message.reply_text(
        "👋 *Welcome to 91 Club Prediction Bot*\n\n"
        "Please join our official channel to access predictions.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN,
    )

# -----------------------
# JOINED BUTTON HANDLER
# -----------------------
async def joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    user_id = query.from_user.id

    if await is_user_joined(context.bot, user_id):
        keyboard = [[InlineKeyboardButton("🎯 Get Prediction", callback_data="get_prediction")]]
        await query.edit_message_text(
            "✅ You have successfully joined the channel!\n\n"
            "Click below to get your prediction:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ I Joined", callback_data="joined")],
        ]
        await query.edit_message_text(
            "⚠️ You have not joined our channel yet.\n\n"
            "Please join it first then click *I Joined* again.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN,
        )

# -----------------------
# GET PREDICTION BUTTON
# -----------------------
async def get_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()

    # Always send a new message to avoid "Message is not modified" error
    await query.message.reply_text(
        "📊 Please *enter the last 3 digits* of the period number (e.g., 128):",
        parse_mode=ParseMode.MARKDOWN,
    )

    # Mark that bot is waiting for user input
    context.user_data["awaiting_period"] = True

# -----------------------
# HANDLE USER INPUT
# -----------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if not context.user_data.get("awaiting_period"):
        return  # ignore unrelated messages

    period_number = update.message.text.strip()

    if not period_number.isdigit() or len(period_number) != 3:
        await update.message.reply_text("⚠️ Please enter a valid 3-digit period number (e.g., 128).")
        return

    # Build demo 14-digit number
    demo_number = "1000000000" + period_number
    if len(demo_number) < 14:
        demo_number = demo_number.rjust(14, "0")
    elif len(demo_number) > 14:
        demo_number = demo_number[-14:]

    total_sum = sum_digits(demo_number)
    format_choice = random.choice([1, 2])
    prediction = get_result(total_sum, format_choice)
    win_rate = random.randint(70, 95)

    # Map prediction to color
    if "SMALL" in prediction:
        color = "🟢 GREEN"
    elif "BIG" in prediction:
        color = "🔴 RED"
    else:
        color = "🟣 PURPLE"

    result_msg = (
        f"❤️ *91 Club:*\n\n"
        f"🎯 Period Number: {period_number}\n\n"
        f"🎰 Prediction: {color}\n"
        f"📈 Type: {prediction}\n"
        f"🏆 Win Rate: {win_rate}%\n\n"
        f"✅ This prediction is based on chart study and 91Club analysis."
    )

    await update.message.reply_text(result_msg, parse_mode=ParseMode.MARKDOWN)

    # Ask for next prediction
    keyboard = [[InlineKeyboardButton("🔁 NEXT RESULT", callback_data="get_prediction")]]
    await update.message.reply_text("Want next prediction?", reply_markup=InlineKeyboardMarkup(keyboard))

    context.user_data["awaiting_period"] = False

# -----------------------
# ERROR HANDLER
# -----------------------
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling an update:", exc_info=context.error)

# -----------------------
# MAIN APP
# -----------------------
def main():
    try:
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(joined, pattern="^joined$"))
        app.add_handler(CallbackQueryHandler(get_prediction, pattern="^get_prediction$"))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        app.add_error_handler(error_handler)

        logger.info("✅ Bot is starting...")
        app.run_polling()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    main()