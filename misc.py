import io

import qrcode
from PIL import Image
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from pyzbar.pyzbar import decode

from main import db

cb_kb = CallbackData('kb', 'box_id', 'action')

cancel_inl_kb = InlineKeyboardMarkup(row_width=1)
cancel_inl_kb.add(InlineKeyboardButton(text='отмена', callback_data=cb_kb.new(box_id='cancel', action='cancel')))


def inl_kb_generator(box_id: str,
                     menu_only: bool = False,
                     box_menu: bool = False,
                     confirm_menu: bool = False) -> InlineKeyboardMarkup:
    menu_dict = {'Изменить содержимое': 'edit_items', 'Добавить в ящик': 'edit_contents', 'QR код ящика': 'qr_code',
                 'Изменить имя': 'edit_name', 'Изменить место': 'edit_place', 'Удалить содержимое': 'delete_contents',
                 'Удалить ящик': 'delete_confirm'}  # , 'Назад': 'back'
    inl_kb = InlineKeyboardMarkup(row_width=1)
    if menu_only:
        inl_kb.add(InlineKeyboardButton(text='Меню', callback_data=cb_kb.new(box_id=box_id, action='menu')))
    elif box_menu:
        for key, value in menu_dict.items():
            inl_kb.add(InlineKeyboardButton(text=key, callback_data=cb_kb.new(box_id=box_id, action=value)))
    elif confirm_menu:
        inl_kb = InlineKeyboardMarkup(row_width=2)
        inl_kb.add(InlineKeyboardButton(text='Да', callback_data=cb_kb.new(box_id=box_id, action='confirm')),
                   InlineKeyboardButton(text='Назад', callback_data=cb_kb.new(box_id=box_id, action='back')))
    return inl_kb


def box_from_db(box_id):
    box = db.select_box(box_id)
    if box:
        contents = db.select_all_contents(box_id=box_id, list_view=True)
        msg = f"<b>№ {box[0]}: {box[1]}\n{box[2]}</b>\n\n" \
              "Сейчас в ящике:\n" \
              f"{contents if contents else 'ничего'}"
        return msg
    else:
        return ''


def edit_contents_inl(box_id: str, cb_data_prefix: str) -> InlineKeyboardMarkup:
    """Генерирует inline клавиатуру с кнопками-содержимое ящика"""
    contents = db.select_all_contents(box_id)
    contents_kb = InlineKeyboardMarkup(row_width=1)
    for item in contents:
        contents_kb.add(InlineKeyboardButton(text=item[1],
                                             callback_data=cb_kb.new(
                                                 box_id=box_id,
                                                 action=f"{cb_data_prefix}{item[2]}")))
    contents_kb.add(InlineKeyboardButton(text='Назад', callback_data=cb_kb.new(box_id=box_id, action='back')))
    return contents_kb


async def qrcode_response(file: io.BytesIO):
    """Распознает QR коды из file-like file io.BytesIO и возвращает номер ящика или None"""
    result = decode(Image.open(file))
    if result:
        c_data = result[0].data.decode("utf-8")
        return c_data[4:] if c_data.startswith('box_') else None
    else:
        return None


async def qr_code_create(box_id: str) -> io.BytesIO:
    """QR code generator from string box_id and return io.BytesIO filelike object"""
    qr_img = qrcode.make(f'/box_{box_id}')
    qr_in_io = io.BytesIO()
    qr_img.save(qr_in_io)
    qr_in_io.seek(0)
    return qr_in_io


def boxes_list(boxes_tuple: tuple = ()) -> str:
    box_list = boxes_tuple if boxes_tuple else db.get_all_box()
    boxes = '\n'.join(f'{box[0]}: {box[1]}: {box[2]} /box_{box[0]}' for box in box_list)
    return f"id : Имя : Место\n\n{boxes if boxes else 'Нет ящиков.'}\n\nДобавить новую /add_box"
