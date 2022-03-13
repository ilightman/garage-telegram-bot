import io
import logging
import sqlite3
from aiogram import types
from aiogram.dispatcher import FSMContext

from main import dp, db, admins, bot
from misc import edit_inl_kb, edit_contents_inl, qrcode_response, menu_kb, yn_kb, cancel_kb, qr_code_maker


# /all_box
@dp.message_handler(commands=['start', 'help'], user_id=admins, state=[None, 'edit'])
async def start_help(message: types.Message):
    msg = f"Показать все ящики /all_box\n" \
          f"Выбрать ящик /box_<b>номерящика</b>\n" \
          f"Добавить новый ящик /add_box\n" \
          f"Для поиска отправь любое слово\n"
    await message.answer(msg)


@dp.message_handler(commands='all_box', user_id=admins, state=[None, 'edit'])
async def all_box(message: types.Message):
    boxes = db.get_all_box()
    places = '\n'.join(f'{box[1]}: {box[2]} /box_{box[0]}' for box in boxes)
    await message.answer(f"Всего ящиков: {len(boxes)}\n"
                         f"Номер : Имя : Место\n\n"
                         f"{places}\n\n"
                         f"Добавить новую /add_box")
    logging.info(f'{message.from_user.id}:{message.from_user.full_name}')


@dp.message_handler(regexp=r'(^(\d+)$)|(^/box_(\d+)$)', user_id=admins, state=[None, 'edit'])
async def select_box_by_number(message: types.Message, state: FSMContext):
    box_id = message.text[5:] if message.text.startswith('/box_') else message.text
    box = db.select_box(box_id)
    if box:
        contents = db.select_all_contents(box_id, list_view=True)
        await message.answer(f"<b>№ {box[0]}: {box[1]}\n{box[2]}</b>\n\n"
                             f"Сейчас в ящике:\n"
                             f"{contents if contents else 'ничего'}",
                             reply_markup=menu_kb)  # inl_kb
        await state.update_data(box_id=box_id)
    else:
        await message.answer('<b>Ящик с таким номером не найден.</b>\n'
                             'Показать все доступные ящики /all_box')
    logging.info(f'/box_{box_id} {message.from_user.id}: {message.from_user.full_name}')


@dp.message_handler(commands="add_box", user_id=admins, state=[None, 'edit'])
@dp.message_handler(user_id=admins, state='qr_gen_0')
async def qr_gen(message: types.Message, state: FSMContext):
    await message.answer("Введи имя нового ящика:", reply_markup=cancel_kb)
    await state.set_state('qr_gen_1')
    logging.info(f' {message.from_user.id}: {message.from_user.full_name}')


@dp.message_handler(state='qr_gen_1', user_id=admins)
async def qr_gen_1(message: types.Message, state: FSMContext):
    box_name = message.text.title()
    if box_name.startswith('/'):
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await state.set_state('qr_gen_1')
        logging.info(f' failed: {message.from_user.id}: {message.from_user.full_name}')
    elif box_name:
        try:
            box_id = db.create_box(box_name)
            await state.update_data(box_id=box_id)
            qr_code = await qr_code_maker(box_id)
            await message.answer_photo(photo=qr_code)
            await message.answer(f"{box_name}", reply_markup=menu_kb)
            await state.set_state('edit')
        except sqlite3.IntegrityError:
            await message.answer("Уже есть ящик с таким именем, давай еще раз")
            await state.set_state('qr_gen_1')
        logging.info(f' success: {message.from_user.id}: {message.from_user.full_name}')


@dp.message_handler(state='edit_from_menu', user_id=admins)
async def message_during_edit_menu(message: types.Message, state: FSMContext):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    await state.set_state('edit_from_menu')


@dp.callback_query_handler(state='*', user_id=admins)
async def cb_query(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    if cb.data in ['menu', 'back']:
        await cb.message.edit_reply_markup(reply_markup=edit_inl_kb)
        await state.set_state('edit_from_menu')
    else:
        await bot.edit_message_text(cb.message.text, reply_markup=None,
                                    chat_id=cb.message.chat.id,
                                    message_id=cb.message.message_id)
    n_state = await state.get_state()
    if n_state in ['edit', 'edit_from_menu']:
        data = await state.get_data()
        box_id = data.get('box_id')
        if cb.data == 'edit_contents':
            contents = db.select_all_contents(box_id, list_view=True)
            if n_state == 'edit':
                await cb.message.answer(f"Сейчас в ящике № {box_id}: \n{contents if contents else 'ничего'}")
            await cb.message.answer("Что добавить (через зяпятую)?")
            await state.set_state("add_contents")
        elif cb.data == 'edit_name':
            box_name = db.select_box(box_id, name=True)
            await cb.message.answer(f"Текущее имя: {box_name}.\nВведи новое", reply_markup=cancel_kb)
            await state.set_state("update_name")
        elif cb.data == 'edit_place':
            box_name = db.select_box(box_id, name=True)
            await cb.message.answer(f"Текущее место: {box_name}.\nВведи новое", reply_markup=cancel_kb)
            await state.set_state("update_place")
        elif cb.data == 'edit_items':
            contents_inl_kb = edit_contents_inl(box_id, 'edit_item_')
            await cb.message.edit_reply_markup(reply_markup=contents_inl_kb)
        elif cb.data == 'delete_contents':
            contents_inl_kb = edit_contents_inl(box_id, 'delete_item_')
            await cb.message.edit_reply_markup(reply_markup=contents_inl_kb)
        elif cb.data == 'qr_code':
            await bot.delete_message(chat_id=cb.message.chat.id, message_id=cb.message.message_id)
            qr_code = await qr_code_maker(box_id)
            await cb.message.answer_photo(photo=qr_code)
            contents = db.select_all_contents(box_id, list_view=True)
            await cb.message.answer(f"{box_id}: Сейчас в ящике:\n"
                                    f"{contents if contents else 'ничего'}",
                                    reply_markup=menu_kb)
            await state.set_state('edit')
        elif cb.data.startswith('edit_item_'):
            content_id = cb.data[10:]
            content = db.select_content(content_id)
            await cb.message.answer(f"<code>{content[1]}</code>\n"
                                    f"нажми, чтобы скопировать и отправь мне исправленное")
            await state.update_data(content_id=content_id)
            await state.set_state('edit_item')
        elif cb.data.startswith('delete_item_'):
            content_id = cb.data[12:]
            db.delete_contents(content_id)
            contents = db.select_all_contents(box_id, list_view=True)
            await cb.message.edit_text(f"Сейчас в ящике № {box_id}: \n{contents if contents else 'ничего'}",
                                       reply_markup=menu_kb)
        elif cb.data == 'delete_box':
            await cb.message.answer(f"Вы уверены что хотите удалить ящик № {box_id}",
                                    reply_markup=yn_kb)
        elif cb.data == 'yes':
            db.delete_box(box_id)
            await cb.message.edit_text(f"Ящик № {box_id} удален. /all_box")
            await state.finish()
    if cb.data == 'cancel':
        await state.finish()
    logging.info(f' {cb.data}: state-{n_state}: {cb.message.from_user.id}: {cb.message.from_user.full_name}')


@dp.message_handler(state="add_contents", user_id=admins)
async def add_contents(message: types.Message, state: FSMContext):
    contents_to_add = [value.strip().lower() for value in message.text.split(',')]
    data = await state.get_data()
    box_id = data.get('box_id')
    db.add_contents_by_box_id(box_id, contents_to_add)
    contents = db.select_all_contents(box_id, list_view=True)
    await message.answer(f"Теперь в ящике {box_id}:\n {contents}", reply_markup=menu_kb)
    await state.set_state('edit')
    logging.info(f' {message.from_user.id}: {message.from_user.full_name}')


@dp.message_handler(state=["edit_item"], user_id=admins)
async def edit_item(message: types.Message, state: FSMContext):
    content = await state.get_data('content_id')
    content_id = content.get('content_id')
    if message.text.startswith('/'):
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await state.set_state('edit_item')
        logging.info(f' failed: {message.from_user.id}: {message.from_user.full_name}')
    else:
        value = message.text
        box_id = db.update_content_by_content_id(content_id, value)
        contents = db.select_all_contents(box_id, list_view=True)
        await message.answer(f"Теперь в ящике {box_id}:\n{contents}", reply_markup=menu_kb)
        await state.set_state('edit')
        logging.info(f' success: {message.from_user.id}: {message.from_user.full_name}')


@dp.message_handler(state=["update_name", "update_place"], user_id=admins)
async def update_name(message: types.Message, state: FSMContext):
    box_id = await state.get_data('box_id')
    box_id = box_id.get('box_id')
    n_state = await state.get_state()
    box = None
    if message.text.startswith('/'):
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await state.set_state('update_name')
        logging.info(f' failed: {message.from_user.id}: {message.from_user.full_name}')
    else:
        if n_state == "update_name":
            box = db.update_name_or_place(box_id, message.text, name=True)
        elif n_state == "update_place":
            box = db.update_name_or_place(box_id, message.text, place=True)
        contents = db.select_all_contents(box_id, list_view=True)
        await message.answer(f"<b>№ {box[0]}: {box[1]}\n{box[2]}</b>\n\n"
                             f"Сейчас в ящике:\n"
                             f"{contents if contents else 'ничего'}",
                             reply_markup=menu_kb)
        await state.set_state('edit')
        logging.info(f' success: {message.from_user.id}: {message.from_user.full_name}')


# поиск
@dp.message_handler(user_id=admins, state=[None, 'edit'])
async def search(message: types.Message):
    item = message.text
    response = db.search_in_box(item)
    if response:
        boxes = '\n'.join(f'{box[1]}: {box[2]} /box_{box[0]}' for box in response)
        await message.answer(f"Найдено в:\n{boxes}")
    else:
        await message.answer("Не найдено")
    logging.info(f' {message.from_user.id}: {message.from_user.full_name}: {message.text}')


@dp.message_handler(user_id=admins, content_types=['photo', 'document'], state=[None, 'edit'])
async def qr_response(message: types.Message, state: FSMContext):
    with io.BytesIO() as file_in_io:
        await message.photo[-1].download(destination_file=file_in_io)
        file_in_io.seek(0)
        box_id = await qrcode_response(file_in_io)
    box = db.select_box(box_id)
    if box:
        contents = db.select_all_contents(box_id, list_view=True)
        await message.answer(f"<b>№ {box[0]}: {box[1]}\n{box[2]}</b>\n\n"
                             f"Сейчас в ящике:\n"
                             f"{contents if contents else 'ничего'}",
                             reply_markup=menu_kb)
        await state.update_data(box_id=box_id)
    else:
        await message.answer(f'{box_id}\n<b>Ящик с таким номером не найден.</b>\n'
                             'Показать все доступные ящики /all_box')
    logging.info(f' {message.from_user.id}: {message.from_user.full_name}')
