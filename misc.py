import io

import qrcode
from PIL import Image
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyzbar.pyzbar import decode

from main import db

edit_inl_kb = InlineKeyboardMarkup(row_width=1)
edit_inl_kb.add(InlineKeyboardButton(text='Изменить содержимое', callback_data='edit_items'))
edit_inl_kb.add(InlineKeyboardButton(text='Добавить в ящик', callback_data='edit_contents'))
edit_inl_kb.add(InlineKeyboardButton(text='QR код ящика', callback_data='qr_code'))
edit_inl_kb.add(InlineKeyboardButton(text='Изменить имя', callback_data='edit_name'))
edit_inl_kb.add(InlineKeyboardButton(text='Изменить место', callback_data='edit_place'))
edit_inl_kb.add(InlineKeyboardButton(text='Удалить содержимое', callback_data='delete_contents'))
edit_inl_kb.add(InlineKeyboardButton(text='Удалить ящик', callback_data='delete_box'))
edit_inl_kb.add(InlineKeyboardButton(text='Отмена', callback_data='cancel'))

menu_kb = InlineKeyboardMarkup(row_width=1)
menu_kb.add(InlineKeyboardButton(text='Меню', callback_data='menu'))

yn_kb = InlineKeyboardMarkup(row_width=3)
yn_kb.add(InlineKeyboardButton(text='Да', callback_data='yes'))
yn_kb.add(InlineKeyboardButton(text='Отмена', callback_data='cancel'))

cancel_kb = InlineKeyboardMarkup(row_width=1)
cancel_kb.add(InlineKeyboardButton(text='Отмена', callback_data='cancel'))


def edit_contents_inl(box_id: str, cb_data_prefix: str) -> InlineKeyboardMarkup:
    contents = db.select_all_contents(box_id)
    inl_kb = InlineKeyboardMarkup(row_width=1)
    for item in contents:
        inl_kb.add(InlineKeyboardButton(text=item[1], callback_data=f"{cb_data_prefix}{item[2]}"))
    inl_kb.add(InlineKeyboardButton(text='Назад', callback_data='back'))
    return inl_kb


async def qrcode_response(file):
    result = decode(Image.open(file))
    if result:
        c_data = result[0].data.decode("utf-8")
        return c_data[4:] if c_data.startswith('box_') else None
    else:
        return None


async def qr_code_maker(box_id):
    """QR code generator from string"""
    qr_img = qrcode.make(f'box_{box_id}')
    qr_in_io = io.BytesIO()
    qr_img.save(qr_in_io)
    qr_in_io.seek(0)
    return qr_in_io
