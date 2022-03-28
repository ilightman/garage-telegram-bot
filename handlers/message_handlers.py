import io
import logging

from aiogram import types
from aiogram.dispatcher import FSMContext

from main import dp, db, admins
from misc import inl_kb_generator, qr_code_create, qrcode_response, box_from_db, cancel_inl_kb, boxes_list


@dp.message_handler(commands=['start', 'help'], user_id=admins)
async def start_help(message: types.Message):
    msg = "Показать все ящики /all_box\n" \
          "Выбрать ящик /box_<b>номер ящика</b>\n" \
          "Добавить новый ящик /add_box\n" \
          "Для поиска отправь любое слово\n"
    await message.answer(msg)


@dp.message_handler(commands='all_box', user_id=admins)
async def all_box(message: types.Message):
    """Отображение всех ящиков с названием и расположением"""
    await message.answer(boxes_list())
    logging.info(f'{message.from_user.id}:{message.from_user.full_name}')


@dp.message_handler(regexp=r'(^(\d{1,2})$)|(^/box_(\d+)$)', user_id=admins)
async def select_box_by_number(message: types.Message):
    """Отображение ящика по команде /box_номерящика или номерящика"""
    box_id = message.text[5:] if message.text.startswith('/box_') else message.text
    msg = box_from_db(box_id)
    if msg:
        await message.answer(msg, reply_markup=inl_kb_generator(box_id, menu_only=True))
        logging.info(f'/box_{box_id}:{message.from_user.id}:{message.from_user.full_name}')
    else:
        await message.answer(f'<b>Ящик с таким id {box_id} - не найден.</b>\n'
                             'Показать все доступные ящики /all_box')
        logging.error(f'{box_id} not found:{message.from_user.id}:{message.from_user.full_name}')


@dp.message_handler(commands="add_box", user_id=admins)
async def add_box(message: types.Message, state: FSMContext):
    await message.answer("Введи имя нового ящика:", reply_markup=cancel_inl_kb)
    await state.set_state('qr_gen')
    logging.info(f'{message.from_user.id}:{message.from_user.full_name}')


@dp.message_handler(state="qr_gen", user_id=admins)
async def qr_gen_1(message: types.Message, state: FSMContext):
    box_name = message.text.title()
    if box_name.startswith('/'):
        await message.delete()
        await state.set_state('qr_gen')
        logging.error(f'failed:"/"in_name:{message.from_user.id}:{message.from_user.full_name}')
    elif box_name:
        box_id = db.create_box(box_name)
        if box_id:
            qr_code = await qr_code_create(box_id)
            await message.answer_photo(photo=qr_code)
            await message.answer(box_from_db(box_id), reply_markup=inl_kb_generator(box_id, menu_only=True))
            await state.finish()
            logging.info(f'success_gen_qr:{box_id}:{message.from_user.id}:{message.from_user.full_name}')
        else:
            await message.answer("Уже есть ящик с таким именем, давай еще раз")
            await state.set_state('qr_gen')


@dp.message_handler(state="add_contents", user_id=admins)
async def add_contents(message: types.Message, state: FSMContext):
    contents_to_add = [value.strip().lower() for value in message.text.split(',')]
    data = await state.get_data()
    box_id = data.get('box_id')
    db.add_contents_by_box_id(box_id, contents_to_add)
    await message.answer(box_from_db(box_id), reply_markup=inl_kb_generator(box_id, menu_only=True))
    await state.finish()
    logging.info(f'{message.from_user.id}:{message.from_user.full_name}')


@dp.message_handler(state="edit_item", user_id=admins)
async def edit_content_item(message: types.Message, state: FSMContext):
    content = await state.get_data('content_id')
    content_id = content.get('content_id')
    if message.text.startswith('/'):
        await message.delete()
        await state.set_state('edit_item')
        logging.error(f'failed:{message.from_user.id}:{message.from_user.full_name}')
    else:
        value = message.text
        box_id = db.update_content_by_content_id(content_id, value)
        await message.answer(box_from_db(box_id), reply_markup=inl_kb_generator(box_id, menu_only=True))
        await state.finish()
        logging.info(f'success:{message.from_user.id}:{message.from_user.full_name}')


@dp.message_handler(state="upd_name", user_id=admins)
@dp.message_handler(state="upd_place", user_id=admins)
async def update_name_place(message: types.Message, state: FSMContext):
    n_state = await state.get_state()
    message_text = message.text
    await message.delete()
    if message_text.startswith('/'):
        await state.set_state('upd_name' if n_state == 'upd_name' else 'upd_place')
        logging.error(f'failed:{message.from_user.id}:{message.from_user.full_name}')
    else:
        box_id = await state.get_data('box_id')
        box_id = box_id.get('box_id')
        if n_state == "upd_name":
            db.update_name_or_place(box_id, message_text, name=True)
        if n_state == "upd_place":
            db.update_name_or_place(box_id, message_text, place=True)
        await message.answer(f"Новое имя: {message_text}\n\n" + box_from_db(box_id),
                             reply_markup=inl_kb_generator(box_id, menu_only=True))
        await state.finish()
        logging.info(f'success:{message.from_user.id}:{message.from_user.full_name}')


@dp.message_handler(user_id=admins)
async def search(message: types.Message):
    """Поиск по содержимому ящиков при любом состоянии"""
    response = db.search_in_box(message.text)
    if response:
        await message.answer(f"<b>Найдено в:</b>\n\n{boxes_list(response)}")
    else:
        await message.answer("Не найдено")
    logging.info(f'{message.from_user.id}:{message.from_user.full_name}:{message.text}')


@dp.message_handler(content_types=['photo', 'document'], user_id=admins)
async def qr_response(message: types.Message):
    """Распознавание QR кода и отображение содержимого ящика"""
    with io.BytesIO() as file_in_io:
        await message.photo[-1].download(destination_file=file_in_io)
        file_in_io.seek(0)
        box_id = await qrcode_response(file_in_io)
    msg = box_from_db(box_id)
    if msg:
        await message.answer(msg, reply_markup=inl_kb_generator(box_id, menu_only=True))
        logging.info(f'{message.from_user.id}:{message.from_user.full_name}')
    else:
        await message.answer(f'<b>Ящик с таким id {box_id} - не найден.</b>\n'
                             'Показать все доступные ящики /all_box')
        logging.error(f'{message.from_user.id}:{message.from_user.full_name}')
