import logging

from aiogram import types
from aiogram.dispatcher import FSMContext

from main import dp, db, admins
from misc import cb_kb, inl_kb_generator, edit_contents_inl, qr_code_create, box_from_db, boxes_list


@dp.callback_query_handler(cb_kb.filter(), text_contains='edit_', user_id=admins)
async def edit_cb(cb: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await cb.answer()
    box_id, action = callback_data.get('box_id'), callback_data.get('action')
    if action == 'edit_contents':
        await cb.message.delete()
        await cb.message.answer(await box_from_db(box_id) + "\n\nЧто добавить (через запятую)?",
                                reply_markup=inl_kb_generator(box_id))
        await state.update_data(box_id=box_id)
        await state.set_state("add_contents")
    elif action in ('edit_name', 'edit_place'):
        box = db.select_box(box_id)
        await cb.message.delete()
        msg = f'имя: <code>{box[1]}</code>' if 'name' in action else f'место: <code>{box[2]}</code>'
        await cb.message.answer("Текущее " + msg + ".\nВведи новое",
                                reply_markup=inl_kb_generator(box_id))
        await state.update_data(box_id=box_id)
        await state.set_state("upd_name" if 'name' in action else "upd_place")
    elif action == 'edit_items':
        contents_inl_kb = await edit_contents_inl(box_id, 'edit_item_')
        await state.update_data(box_id='box_id')
        await cb.message.edit_reply_markup(reply_markup=contents_inl_kb)
    elif action.startswith('edit_item_'):
        content_id = action[10:]
        content = db.select_content(content_id)
        await cb.message.answer(f"<code>{content[1]}</code>\n"
                                f"нажми, чтобы скопировать и отправь мне исправленное")
        await state.update_data(content_id=content_id)
        await state.set_state('edit_item')


@dp.callback_query_handler(cb_kb.filter(), text_contains='delete_', user_id=admins)
async def delete_cb_handler(cb: types.CallbackQuery, callback_data: dict):
    await cb.answer()
    box_id, action = callback_data.get('box_id'), callback_data.get('action')
    if action == 'delete_contents':
        contents_inl_kb = await edit_contents_inl(box_id, 'delete_item_')
        await cb.message.edit_reply_markup(reply_markup=contents_inl_kb)
    elif action.startswith('delete_item_'):
        content_id = action[12:]
        db.delete_contents(content_id)
        await cb.message.edit_text(await box_from_db(box_id),
                                   reply_markup=inl_kb_generator(box_id, menu_only=True))
    elif action == 'delete_confirm':
        await cb.message.edit_text(f"Вы уверены что хотите \nудалить ящик № {box_id}",
                                   reply_markup=inl_kb_generator(box_id, confirm_menu=True))
    logging.info(f'{cb.data}:{cb.message.from_user.id}:{cb.message.from_user.full_name}')


@dp.callback_query_handler(cb_kb.filter(), state='*', user_id=admins)
async def cb_query(cb: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await cb.answer()
    box_id, action = callback_data.get('box_id'), callback_data.get('action')
    if action == 'menu':
        await cb.message.edit_reply_markup(reply_markup=inl_kb_generator(box_id, box_menu=True))
    elif action == 'qr_code':
        await cb.message.delete()
        qr_code = await qr_code_create(box_id)
        await cb.message.answer_photo(photo=qr_code, caption=f"Ящик № {box_id}")
        await cb.message.answer(await box_from_db(box_id), reply_markup=inl_kb_generator(box_id, menu_only=True))
    elif action == 'back':
        await cb.message.edit_reply_markup(reply_markup=inl_kb_generator(box_id, box_menu=True))
    elif action == 'confirm':
        db.delete_box(box_id)
        await cb.message.edit_text(f"Ящик № {box_id} удален.\n\n" + await boxes_list())
        await state.finish()
    elif action == 'cancel':
        await cb.message.delete()
        await state.finish()
    logging.info(f'{cb.data}:{cb.message.from_user.id}:{cb.message.from_user.full_name}')
