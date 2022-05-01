import logging
import os
import time
from datetime import datetime

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dotenv import load_dotenv

from db_api import DB

logging.basicConfig(filename="app.log", format='%(asctime)s:%(funcName)s:%(message)s', level=logging.INFO)

# os.environ["BOT_TOKEN"] = ""  # your telegram bot token
# os.environ["ADMINS"] = ""  # admins telegram id separate by space

load_dotenv()
bot = Bot(token=os.getenv("BOT_TOKEN"), parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())
db = DB('db.sqlite')
admins = os.getenv("ADMINS").split()


async def admin_notify(disp: Dispatcher, key: str):
    try:
        await disp.bot.send_message(admins[0],
                                    f'{datetime.now().strftime("%d.%m.%Y-%H:%M:%S")} '
                                    f'{"Бот запущен и готов к работе" if key == "on" else "Бот выключается"}')
        print(f'{"Бот запущен и готов к работе" if key == "on" else "Бот выключается"}')
    except Exception as err:
        logging.exception(err)


async def set_default_commands(disp):
    await disp.bot.set_my_commands([
        types.BotCommand("help", "Помощь"),
        types.BotCommand("add_box", "Добавить ящик"),
        types.BotCommand("all_box", "Отобразить все ящики"),
    ])


async def on_startup(disp):
    db.create_db()
    await admin_notify(disp, key='on')
    await set_default_commands(disp)
    logging.info('Бот запущен и работает')


async def on_shutdown(disp):
    await admin_notify(disp, key='off')
    logging.info('Бот выключается')
    time.sleep(3)


if __name__ == '__main__':
    from handlers import dp

    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown, skip_updates=True)
