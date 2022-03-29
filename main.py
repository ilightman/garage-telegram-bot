import logging
from datetime import datetime
from os import getenv

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from db_api import DB

logging.basicConfig(format='%(asctime)s:%(funcName)s:%(message)s', level=logging.INFO)  # filename="app.log",
bot = Bot(token=getenv("BOT_TOKEN"), parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())
db = DB('db.sqlite')
admins = getenv("ADMINS").split()


async def admin_notify(dp: Dispatcher, key: str):
    try:
        await dp.bot.send_message(admins[0],
                                  f'{datetime.now().strftime("%d.%m.%Y-%H:%M:%S")} '
                                  f'{"Бот запущен и готов к работе" if key == "on" else "Бот выключается"}')
    except Exception as err:
        logging.exception(err)


async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand("help", "Помощь"),
        types.BotCommand("add_box", "Добавить ящик"),
        types.BotCommand("all_box", "Отобразить все ящики"),
    ])


async def on_startup(dp):
    db.create_db()
    await admin_notify(dp, key='on')
    await set_default_commands(dp)


async def on_shutdown(dp):
    await admin_notify(dp, key='off')


if __name__ == '__main__':
    from handlers import dp

    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown, skip_updates=True)
