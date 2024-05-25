import os
import requests
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from keep_alive import keep_alive
import fcntl

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

LOCK_FILE_PATH = "bot.lock"

def acquire_lock():
    try:
        lock_file = open(LOCK_FILE_PATH, "w")
        fcntl.lockf(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_file
    except IOError:
        logger.error("Failed to acquire lock. Another instance may be running.")
        return None

def release_lock(lock_file):
    lock_file.close()
    os.remove(LOCK_FILE_PATH)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hello! Use /leaderboard <wallet_address1> <wallet_address2> ... to get the leaderboard data.')

def get_leaderboard_data(wallet_address: str):
    try:
        # Convert the wallet address to lowercase
        wallet_address = wallet_address.lower()
        
        response = requests.get(f'https://api.pixelpals.ai/rest/v1/leaderboard_habitat_view?wallet_address=eq.{wallet_address}&order=date.desc&limit=1')
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Request failed for wallet {wallet_address}: {e}")
        return None

def leaderboard(update: Update, context: CallbackContext) -> None:
    wallet_addresses = context.args
    if not wallet_addresses:
        update.message.reply_text('Please provide at least one wallet address.')
        return

    for wallet_address in wallet_addresses:
        data = get_leaderboard_data(wallet_address)
        if data:
            reply_text = ""
            for entry in data:
                if entry['date'] == '2024-04-29':
                    reply_text += f"Wallet Address: {entry['wallet_address']}\n"
                    reply_text += f"Date: {entry['date']}\n"
                    reply_text += f"Rank: {entry['rank']}\n"
                    reply_text += f"Habitat Value: {entry['habitat_value']}\n"
                    reply_text += f"Pet Level: {entry['pet_level']}\n"
                    reply_text += f"Pet Point: {entry['pet_point']}\n"
                    reply_text += f"Season ID: {entry['season_id']}\n\n"
            if reply_text:
                update.message.reply_text(reply_text)
        else:
            update.message.reply_text(f"Error: Failed to fetch data for wallet address {wallet_address}")

def main():
    # Try to acquire the lock
    lock_file = acquire_lock()
    if not lock_file:
        return

    try:
        # Keep the server alive
        keep_alive()

        # Read the bot token from environment variable
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")

        # Create the Updater and pass it your bot's token.
        updater = Updater(bot_token)

        # Get the dispatcher to register handlers
        dispatcher = updater.dispatcher

        # Register the command handlers
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("leaderboard", leaderboard))

        # Start the Bot
        updater.start_polling()

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT.
        updater.idle()
    finally:
        # Release the lock
        if lock_file:
            release_lock(lock_file)

if __name__ == '__main__':
    main()
