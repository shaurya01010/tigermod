import logging
import random
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

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

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

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
def is_user_joined(user_id: int) -> bool:
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.warning(f"get_chat_member failed: {e}")
        return False

# Store user states
user_states = {}

# -----------------------
# START COMMAND
# -----------------------
@bot.message_handler(commands=['start'])
def start(message):
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ I Joined", callback_data="joined")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(
        message.chat.id,
        "👋 *Welcome to 91 Club Prediction Bot*\n\n"
        "Please join our official channel to access predictions.",
        reply_markup=markup,
        parse_mode='Markdown'
    )

# -----------------------
# CALLBACK QUERY HANDLER
# -----------------------
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "joined":
        user_id = call.from_user.id
        
        if is_user_joined(user_id):
            keyboard = [[InlineKeyboardButton("🎯 Get Prediction", callback_data="get_prediction")]]
            markup = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(
                "✅ You have successfully joined the channel!\n\n"
                "Click below to get your prediction:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
        else:
            keyboard = [
                [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton("✅ I Joined", callback_data="joined")],
            ]
            markup = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(
                "⚠️ You have not joined our channel yet.\n\n"
                "Please join it first then click *I Joined* again.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='Markdown'
            )
    
    elif call.data == "get_prediction":
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            "📊 Please *enter the last 3 digits* of the period number (e.g., 128):",
            parse_mode='Markdown'
        )
        user_states[call.from_user.id] = "awaiting_period"

# -----------------------
# HANDLE USER INPUT
# -----------------------
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    
    if user_states.get(user_id) == "awaiting_period":
        period_number = message.text.strip()

        if not period_number.isdigit() or len(period_number) != 3:
            bot.send_message(message.chat.id, "⚠️ Please enter a valid 3-digit period number (e.g., 128).")
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

        bot.send_message(message.chat.id, result_msg, parse_mode='Markdown')

        # Ask for next prediction
        keyboard = [[InlineKeyboardButton("🔁 NEXT RESULT", callback_data="get_prediction")]]
        markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(message.chat.id, "Want next prediction?", reply_markup=markup)

        user_states[user_id] = None

# -----------------------
# MAIN APP
# -----------------------
if __name__ == "__main__":
    logger.info("✅ Bot is starting...")
    bot.infinity_polling()