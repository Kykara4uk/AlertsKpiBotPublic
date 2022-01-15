from aiogram.types import BotCommand

from handlers.handlers import set_bot_commands
from loader import bot

from utils.db_api.database import create_db
from utils.notify_admins import on_shutdown_notify, on_startup_notify
import traceback

async def on_startup(dp):

    print("Bot is running...")
    await create_db()
    await set_bot_commands()
    #await bot.send_message(ADMIN_CHAT_ID, '@MatanHackBot LOG: Bot started')

async def on_shutdown(dp):
    pass


if __name__ == '__main__':
    from aiogram import executor
    from handlers import dp
    
    try:
        executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)


    except Exception as e:
        var = traceback.format_exc()
        print(var)



    



