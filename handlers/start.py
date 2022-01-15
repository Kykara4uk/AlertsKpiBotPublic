import json

from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart


from keyboards import  menu_markup
from loader import dp, bot
from utils.db_api.db_commands import get_user, add_user, get_group_by_code


@dp.message_handler(CommandStart(), state='*')
async def bot_start(message: types.Message):

    user = types.User.get_current()
    tg_id = user.id
    group_code = message.get_args()

    isUserAlreadyInDB = await get_user(tg_id)
    if isUserAlreadyInDB == None:
        await message.answer_sticker(sticker="CAACAgQAAxkBAAIGXV__bWFhszPnWYSQJvKthQoMiem8AAJrAAPOOQgNWWbqY3aSS9AeBA")
        first_name = user.first_name
        last_name = user.last_name
        full_name = user.full_name

        username = user.username
        await add_user(tg_id=tg_id, firstname=first_name, lastname = last_name, fullname=full_name,
                       username=username)
    if group_code:
        group = await get_group_by_code(code=group_code)
        if group is not None:
            group_users = json.loads(group.users)
            if group_users is not None and tg_id not in group_users:
                await message.answer(f"Ты присоединился к группе {group.name}. Теперь ты будешь получать уведомления от этой группы")
                group_users.append(tg_id)
                group_users_jsn = json.dumps(group_users)
                group.users = group_users_jsn
                await group.update(users=group_users_jsn).apply()
                user_in_DB = await get_user(tg_id)


                if user_in_DB.groups is  None:
                    user_groups_list = json.dumps([group.group_id])
                    await user_in_DB.update(groups=user_groups_list).apply()
                else:
                    user_groups = json.loads(user_in_DB.groups)
                    user_groups.append(group.group_id)
                    user_groups_list = json.dumps(user_groups)
                    await user_in_DB.update(groups=user_groups_list).apply()
            else:
                await message.answer(f"Ты уже состоишь в группе {group.name}")
        else:
            await message.answer("Похоже группы, к которой ты пытаешься присоедениться не существует :(")
    markup = await menu_markup(user.id)
    await message.answer(text="Выбери, что хочешь сделать", reply_markup=markup)





