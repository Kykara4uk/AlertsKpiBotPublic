import datetime
import random
import re
from functools import wraps
from typing import Union, List
import json
from xmlrpc.client import DateTime
import uuid
import json
import pytz

from geopy.distance import geodesic, great_circle
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, BotCommand, \
    BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats, BotCommandScopeChat, \
    BotCommandScopeDefault, MessageEntity, Message, BotCommandScopeChatMember

import keyboards

from keyboards import menu_cd
from loader import dp, bot

import asyncio

# @dp.message_handler(lambda msg: msg.new_chat_members!=None)
from states import NewGroup, SendAlert, EnterGroup, ChangeGroup
from utils.db_api.db_commands import get_user, is_name_busy, get_group_by_id, get_group_by_code
from utils.db_api.models import User, Group


@dp.errors_handler()
async def error(update: types.Update, exception):
    await bot.send_message(text="Ошибка в боте!", chat_id=243568187)
    await bot.send_message(text=update, chat_id=243568187)
    await bot.send_message(text=exception, chat_id=243568187)


async def set_bot_commands():
    commands = [BotCommand(command="menu", description="Меню пользователя"),
                BotCommand(command="my_groups", description="Мои группы"),
                BotCommand(command="enter_group", description="Войти в группу"),
                BotCommand(command="create_group", description="Создать группу"),
                ]
    await bot.set_my_commands(commands=commands, scope=BotCommandScopeDefault())







@dp.message_handler(commands=["cancel"], state ="*")
async def cancel(message: types.Message, state: FSMContext):
    await message.answer("Отмена", reply_markup=ReplyKeyboardRemove())
    user = types.User.get_current()
    #await admin_menu(message)
    await state.reset_state()
    markup = await keyboards.menu_markup(user.id)
    await message.answer(text="Выбери, что хочешь сделать", reply_markup=markup)





async def set_empty_message_to_delete_markup(message: types.Message):
    mess = await message.answer(text="­", reply_markup=ReplyKeyboardRemove())
    try:
        await mess.delete()
    except Exception as e:
        await bot.send_message(text="Ошибка в боте!", chat_id=243568187)
        await bot.send_message(text=message, chat_id=243568187)
        await bot.send_message(text=e, chat_id=243568187)

@dp.message_handler(Command("create_group"))
async def create_group(message: Union[types.Message, types.CallbackQuery], **kwargs):
    user = types.User.get_current()
    text = "Пришли мне название твоей новой комнаты. Для отмены нажми /cancel"
    if type(message) == types.Message:
        await message.answer(text=text)
    else:
        await message.message.edit_text(text=text)
    await NewGroup.Name.set()


async def group_menu(call: types.CallbackQuery, id, **kwargs):
    user = types.User.get_current()
    markup = await keyboards.group_markup(group_id=id, user_id=user.id)
    group = await get_group_by_id(int(id))
    bot_username = (await bot.get_me()).username
    if user.id == group.owner:
        await call.message.edit_text(text=f"*{group.name}*\n\nКол-во участников: {len(json.loads(group.users))}\nКод доступа: `{group.code}`\nСсылка-приглашение: https://t.me/{bot_username}?start={group.code}", reply_markup=markup, parse_mode='Markdown')
    else:
        await call.message.edit_text(text=f"*{group.name}*", reply_markup=markup, parse_mode='Markdown')


async def exit_from_group_user(call: types.CallbackQuery, id, **kwargs):
    user = types.User.get_current()

    group = await get_group_by_id(int(id))
    user_in_DB = await get_user(user.id)
    user_groups = json.loads(user_in_DB.groups)
    group_users = json.loads(group.users)
    user_groups.remove(group.group_id)
    group_users.remove(user.id)
    if len(user_groups) != 0:
        await user_in_DB.update(groups=json.dumps(user_groups)).apply()
    else:
        await user_in_DB.update(groups=None).apply()
    if len(group_users) != 0:
        await group.update(users=json.dumps(group_users)).apply()
    else:
        await group.update(users=None).apply()
    try:
        await call.message.edit_text(text=f"Вы вышли из группы *{group.name}*", parse_mode='Markdown')
    except:
        pass
    if user_in_DB.groups is not None:

        markup = await keyboards.my_groups_markup(json.loads(user_in_DB.groups))

        await call.message.answer(text="Выбери группу", reply_markup=markup)

    else:
        text = "Выбери, что хочешь сделать"
        markup = await keyboards.menu_markup(user.id)
        await call.message.answer(text=text, reply_markup=markup)

async def exit_from_group_admin(call: types.CallbackQuery, id, **kwargs):
    user = types.User.get_current()

    group = await get_group_by_id(int(id))
    user_in_DB = await get_user(user.id)
    user_groups = json.loads(user_in_DB.groups)
    group_users = json.loads(group.users)
    group_admins = json.loads(group.admins)
    user_groups.remove(group.group_id)
    group_users.remove(user.id)
    group_admins.remove(user.id)
    if len(group_users) != 0:
        group_users_list=json.dumps(group_users)
    else:
        group_users_list = None
    if len(group_admins) != 0:
        group_admins_list=json.dumps(group_admins)
    else:
        group_admins_list = None
    if len(user_groups) != 0:
        await user_in_DB.update(groups=json.dumps(user_groups)).apply()
    else:
        await user_in_DB.update(groups=None).apply()

    await group.update(users=group_users_list, admins=group_admins_list).apply()

    await call.message.edit_text(text=f"Вы вышли из группы *{group.name}*", parse_mode='Markdown')
    if user_in_DB.groups is not None:

        markup = await keyboards.my_groups_markup(json.loads(user_in_DB.groups))
        try:
            await call.message.answer(text="Выбери группу", reply_markup=markup)
        except:
            pass

    else:
        text = "Выбери, что хочешь сделать"
        markup = await keyboards.menu_markup(user.id)
        await call.message.answer(text=text, reply_markup=markup)



async def send_alert_text(call: types.CallbackQuery, id, **kwargs):
    user = types.User.get_current()
    group = await get_group_by_id(int(id))
    if group is not None:
        await call.message.edit_text(text=f"Пришли текст, который хочешь отослать участникам группы *{group.name}*. Для отмены нажми /cancel", parse_mode='Markdown')
        await SendAlert.Text.set()
        state = Dispatcher.get_current().current_state()
        await state.update_data(group_id=id)
    else:
        await call.message.edit_text("Похоже группы, в которую, ты пытаешься написать, не существует :(")
        text = "Выбери, что хочешь сделать"
        markup = await keyboards.menu_markup(user.id)
        await call.message.answer(text=text, reply_markup=markup)
        return

async def enter_group_by_code(call: types.CallbackQuery, **kwargs):
    user = types.User.get_current()
    await call.message.edit_text(text=f"Пришли код доступа группы")
    await EnterGroup.Code.set()

async def change_group_name(call: types.CallbackQuery, id, **kwargs):
    user = types.User.get_current()
    await call.message.edit_text(text=f"Пришли новое название группы")
    await ChangeGroup.Name.set()
    state = Dispatcher.get_current().current_state()
    await state.update_data(group_id=id)

async def change_group_code(call: types.CallbackQuery, id, **kwargs):
    user = types.User.get_current()
    group = await get_group_by_id(int(id))
    if group is not None:
        markup = await keyboards.group_markup(group_id=id, user_id=user.id)
        await group.update(code=uuid.uuid4().hex[:10]).apply()
        bot_username = (await bot.get_me()).username
        await bot.answer_callback_query(callback_query_id=call.id, text="Код доступа и ссылка обновлены", show_alert=False)
        if user.id == group.owner:
            await call.message.edit_text(
                text=f"*{group.name}*\n\nКол-во участников: {len(json.loads(group.users))}\nКод доступа: `{group.code}`\nСсылка-приглашение: https://t.me/{bot_username}?start={group.code}",
                reply_markup=markup, parse_mode='Markdown')
        else:
            await call.message.edit_text(text=f"*{group.name}*", reply_markup=markup, parse_mode='Markdown')
    else:
        await call.message.edit_text("Похоже группы, которую, ты пытаешься изменить, не существует :(")
        text = "Выбери, что хочешь сделать"
        markup = await keyboards.menu_markup(user.id)
        await call.message.answer(text=text, reply_markup=markup)
        return


async def change_group_open(call: types.CallbackQuery, id, **kwargs):
    user = types.User.get_current()
    group = await get_group_by_id(int(id))
    if group is not None:

        if group.isOpen:
            await group.update(isOpen=False).apply()
            await bot.answer_callback_query(callback_query_id=call.id, text="Теперь это закрытая группа",
                                            show_alert=False)
        else:
            await group.update(isOpen=True).apply()
            await bot.answer_callback_query(callback_query_id=call.id, text="Теперь это открытая группа",
                                            show_alert=False)
        bot_username = (await bot.get_me()).username
        markup = await keyboards.group_markup(group_id=id, user_id=user.id)

        if user.id == group.owner:
            await call.message.edit_text(
                text=f"*{group.name}*\n\nКол-во участников: {len(json.loads(group.users))}\nКод доступа: `{group.code}`\nСсылка-приглашение: https://t.me/{bot_username}?start={group.code}",
                reply_markup=markup, parse_mode='Markdown')
        else:
            await call.message.edit_text(text=f"*{group.name}*", reply_markup=markup, parse_mode='Markdown')
    else:
        await call.message.edit_text("Похоже группы, которую, ты пытаешься изменить, не существует :(")
        text = "Выбери, что хочешь сделать"
        markup = await keyboards.menu_markup(user.id)
        await call.message.answer(text=text, reply_markup=markup)
        return

async def change_group_users(call: types.CallbackQuery, id, i,**kwargs):
    user = types.User.get_current()
    group = await get_group_by_id(int(id))
    if group is not None:
        markup = await keyboards.change_group_users_markup(group_id=id, i=i)
        try:
            await call.message.edit_text(text=f"Участники группы *{group.name}*", reply_markup=markup, parse_mode='Markdown')
        except Exception as e:
            pass
    else:
        await call.message.edit_text("Похоже группы, которую, ты пытаешься изменить, не существует :(")
        text = "Выбери, что хочешь сделать"
        markup = await keyboards.menu_markup(user.id)
        await call.message.answer(text=text, reply_markup=markup)
        return


async def change_group_to_admin_add(call: types.CallbackQuery, id, i=0,**kwargs):
    user = types.User.get_current()
    group = await get_group_by_id(int(id))
    if group is not None:
        markup = await keyboards.change_group_users_markup(group_id=id, i=i)
        try:
            await call.message.edit_text(text=f"Чтоб добавить администратора - выбери его среди участников и выдай права админа. Человек, которого ты выберешь, сможет публиковать уведомления в этой группе\n\nУчастники группы *{group.name}*", reply_markup=markup, parse_mode='Markdown')
        except Exception as e:
            pass
    else:
        await call.message.edit_text("Похоже группы, которую, ты пытаешься изменить, не существует :(")
        text = "Выбери, что хочешь сделать"
        markup = await keyboards.menu_markup(user.id)
        await call.message.answer(text=text, reply_markup=markup)
        return

async def change_group_admins(call: types.CallbackQuery, id, i=0,**kwargs):
    user = types.User.get_current()




    group = await get_group_by_id(int(id))
    if group is not None:
        markup = await keyboards.change_group_admins_markup(group_id=id, i=i)
        try:
            await call.message.edit_text(text=f"Администраторы группы *{group.name}*", reply_markup=markup, parse_mode='Markdown')
        except Exception as e:
            pass
    else:
        await call.message.edit_text("Похоже группы, которую, ты пытаешься изменить, не существует :(")
        text = "Выбери, что хочешь сделать"
        markup = await keyboards.menu_markup(user.id)
        await call.message.answer(text=text, reply_markup=markup)
        return

async def change_group_delete(call: types.CallbackQuery, id, **kwargs):
    user = types.User.get_current()




    group = await get_group_by_id(int(id))
    if group is not None:
        markup = await keyboards.confirm_group_delete_markup(group_id=id)
        try:
            await call.message.edit_text(text=f"Ты уверен, что хочешь удалить группу? *{group.name}*", reply_markup=markup, parse_mode='Markdown')
        except Exception as e:
            pass
    else:
        await call.message.edit_text("Похоже группы, которую, ты пытаешься изменить, не существует :(")
        text = "Выбери, что хочешь сделать"
        markup = await keyboards.menu_markup(user.id)
        await call.message.answer(text=text, reply_markup=markup)
        return

async def change_group_delete_confirm(call: types.CallbackQuery, id, **kwargs):
    user = types.User.get_current()




    group = await get_group_by_id(int(id))
    if group is not None:
        users = json.loads(group.users)
        counter = 0
        for user_to_del in users:
            user_in_db = await get_user(int(user_to_del))
            user_groups = json.loads(user_in_db.groups)
            user_groups.remove(int(group.group_id))
            if len(user_groups) != 0:
                await user_in_db.update(groups=json.dumps(user_groups)).apply()
            else:
                await user_in_db.update(groups=None).apply()
            if user_in_db.tg_id != group.owner:
                await bot.send_message(chat_id=user_in_db.tg_id, text=f"Группа *{group.name}* удалена. Вы больше не будете получать уведомления из этой группы", parse_mode='Markdown')
            else:
                await bot.answer_callback_query(callback_query_id=call.id, text=f"Группа {group.name} удалена", show_alert=True)
            counter+=1
            if counter>10:
                await asyncio.sleep(1)
                counter = 0
        await group.delete()
        text = "Выбери, что хочешь сделать"
        markup = await keyboards.menu_markup(user.id)
        await call.message.edit_text(text=text, reply_markup=markup)
    else:
        await call.message.edit_text("Похоже группы, которую, ты пытаешься изменить, не существует :(")
        text = "Выбери, что хочешь сделать"
        markup = await keyboards.menu_markup(user.id)
        await call.message.answer(text=text, reply_markup=markup)
        return


async def change_group_user_delete(call: types.CallbackQuery, id, id2, i=0,**kwargs):
    user = types.User.get_current()




    group = await get_group_by_id(int(id))
    if group is not None:
        user_in_db = await get_user(int(id2))
        group_users = json.loads(group.users)
        group_admins = json.loads(group.admins)
        user_groups = json.loads(user_in_db.groups)
        if int(id2) in group_admins:
            group_admins.remove(int(id2))

        user_groups.remove(int(id))
        group_users.remove(int(id2))
        await group.update(users=json.dumps(group_users), admins= json.dumps(group_admins)).apply()
        if len(user_groups) > 0:
            await user_in_db.update(groups=json.dumps(user_groups)).apply()
        else:
            await user_in_db.update(groups=None).apply()
        await bot.answer_callback_query(callback_query_id=call.id, text=f"Пользователь {user_in_db.fullname} удален",show_alert=False)
        await bot.send_message(chat_id=user_in_db.tg_id, text=f"Вас удалили из группы {group.name}. Вы больше не сможете получать уведомления из этой группы")
        markup = await keyboards.change_group_users_markup(group_id=id, i=0)
        try:
            await call.message.edit_text(text=f"Участники группы *{group.name}*", reply_markup=markup, parse_mode='Markdown')
        except Exception as e:
            pass
    else:
        await call.message.edit_text("Похоже группы, которую, ты пытаешься изменить, не существует :(")
        text = "Выбери, что хочешь сделать"
        markup = await keyboards.menu_markup(user.id)
        await call.message.answer(text=text, reply_markup=markup)
        return


async def change_group_admin_delete(call: types.CallbackQuery, id, id2, i=0,**kwargs):
    user = types.User.get_current()
    group = await get_group_by_id(int(id))
    if group is not None:
        user_in_db = await get_user(int(id2))
        group_admins = json.loads(group.admins)
        if int(id2) in group_admins:
            group_admins.remove(int(id2))

        await group.update(admins= json.dumps(group_admins)).apply()
        await bot.answer_callback_query(callback_query_id=call.id, text=f"С администратора {user_in_db.fullname} были сняты права",show_alert=False)
        await bot.send_message(chat_id=user_in_db.tg_id, text=f"Владелец группы {group.name} снял с вас права. Вы больше не сможете писать в эту группу")
        markup = await keyboards.user_markup(user_id=id2, i=i, group_id=id)
        user_from_db = await get_user(int(id2))
        text = '<a href="tg://user?id=' + str(
            user_from_db.tg_id) + '">' + str(user_from_db.fullname) + '</a>\n'
        text += "Роль: "
        if int(id) == group.owner:
            text += "Владелец группы"
        elif int(id) in json.loads(group.admins):
            text += "Администратор"
        else:
            text += "Участник"
        try:
            await call.message.edit_text(text=text, reply_markup=markup)
        except Exception as e:
            pass
    else:
        await call.message.edit_text("Похоже группы, которую, ты пытаешься изменить, не существует :(")
        text = "Выбери, что хочешь сделать"
        markup = await keyboards.menu_markup(user.id)
        await call.message.answer(text=text, reply_markup=markup)
        return



async def change_group_admin_add(call: types.CallbackQuery, id, id2, i, **kwargs):
    user = types.User.get_current()
    group = await get_group_by_id(int(id))
    if group is not None:
        user_in_db = await get_user(int(id2))
        group_admins = json.loads(group.admins)
        if int(id2) not in group_admins:
            group_admins.append(int(id2))

        await group.update(admins= json.dumps(group_admins)).apply()
        group = await get_group_by_id(int(id))
        print(group.admins)
        await bot.answer_callback_query(callback_query_id=call.id, text=f"Пользователь {user_in_db.fullname} теперь может писать уведомления в группу*{group.name}*",show_alert=False)
        await bot.send_message(chat_id=user_in_db.tg_id, text=f"Владелец группы {group.name} дал Вам права на публикацию уведомлений в группе *{group.name}*. Публиковать уведомления Вы можете из меню группы", parse_mode='Markdown')
        markup = await keyboards.user_markup(user_id=id2, i=i, group_id=id)

        text = '<a href="tg://user?id=' + str(
            user_in_db.tg_id) + '">' + str(user_in_db.fullname) + '</a>\n'
        text += "Роль: "
        if int(id2) == group.owner:
            text += "Владелец группы"
        elif int(id2) in json.loads(group.admins):
            text += "Администратор"
        else:
            text += "Участник"
        print(json.loads(group.admins)[1]==int(id))
        print(json.loads(group.admins)[1] == id)
        print(id)
        await call.message.edit_text(text=text, reply_markup=markup)
        try:
            await call.message.edit_text(text=text, reply_markup=markup)
        except Exception as e:
            pass
    else:
        await call.message.edit_text("Похоже группы, которую, ты пытаешься изменить, не существует :(")
        text = "Выбери, что хочешь сделать"
        markup = await keyboards.menu_markup(user.id)
        await call.message.answer(text=text, reply_markup=markup)
        return

async def change_group_user_info(call: types.CallbackQuery, id,id2, i=0,  **kwargs):
    user = types.User.get_current()




    group = await get_group_by_id(int(id2))
    if group is not None:
        markup = await keyboards.user_markup(user_id=id, i=i, group_id=id2)
        user_from_db= await get_user(int(id))
        text = '<a href="tg://user?id=' + str(
                user_from_db.tg_id) + '">' + str(user_from_db.fullname) + '</a>\n'
        text+="Роль: "
        if int(id) == group.owner:
            text+="Владелец группы"
        elif int(id) in json.loads(group.admins):
            text+="Администратор"
        else:
            text+="Участник"
        try:
            await call.message.edit_text(text=text, reply_markup=markup)
        except Exception as e:
            pass
    else:
        await call.message.edit_text("Похоже группы, которую, ты пытаешься изменить, не существует :(")
        text = "Выбери, что хочешь сделать"
        markup = await keyboards.menu_markup(user.id)
        await call.message.answer(text=text, reply_markup=markup)
        return

async def change_group_admin_info(call: types.CallbackQuery, id,id2, i=0,  **kwargs):
    user = types.User.get_current()




    group = await get_group_by_id(int(id2))
    if group is not None:
        markup = await keyboards.admin_markup(user_id=id, i=i, group_id=id2)
        user_from_db= await get_user(int(id))
        text = '<a href="tg://user?id=' + str(
                user_from_db.tg_id) + '">' + str(user_from_db.fullname) + '</a>\n'
        text+="Роль: "
        if int(id) == group.owner:
            text+="Владелец группы"
        elif int(id) in json.loads(group.admins):
            text+="Администратор"
        else:
            text+="Участник"
        try:
            await call.message.edit_text(text=text, reply_markup=markup)
        except Exception as e:
            pass
    else:
        await call.message.edit_text("Похоже группы, которую, ты пытаешься изменить, не существует :(")
        text = "Выбери, что хочешь сделать"
        markup = await keyboards.menu_markup(user.id)
        await call.message.answer(text=text, reply_markup=markup)
        return



async def enter_group_open(call: types.CallbackQuery, id,  **kwargs):
    user = types.User.get_current()
    group = await get_group_by_id(int(id))
    if group is not None:
        if group.isOpen:
            group_users = json.loads(group.users)
            if group_users is not None and user.id not in group_users:
                await call.message.edit_text(
                    f"Ты присоединился к группе {group.name}. Теперь ты будешь получать уведомления от этой группы")
                group_users.append(user.id)
                group_users_jsn = json.dumps(group_users)
                group.users = group_users_jsn
                await group.update(users=group_users_jsn).apply()
                user_in_DB = await get_user(user.id)

                if user_in_DB.groups is None:
                    user_groups_list = json.dumps([group.group_id])
                    await user_in_DB.update(groups=user_groups_list).apply()
                else:
                    user_groups = json.loads(user_in_DB.groups)
                    user_groups.append(group.group_id)
                    user_groups_list = json.dumps(user_groups)
                    await user_in_DB.update(groups=user_groups_list).apply()
                text = "Выбери, что хочешь сделать"
                markup = await keyboards.menu_markup(user.id)
                await call.message.answer(text=text, reply_markup=markup)
            else:
                await bot.answer_callback_query(callback_query_id=call.id,
                                                text=f"Ты уже состоишь в группе {group.name}",
                                                show_alert=False)
                markup = await keyboards.enter_group_markup(i=0, user_id=user.id)
                try:
                    await call.message.edit_text(text="Выбери группу для входа", reply_markup=markup)
                except Exception as e:
                    pass
        else:
            await bot.answer_callback_query(callback_query_id=call.id, text=f"Ошибка при присоединении в группе {group.name}. Похоже владелец огранчил доступ", show_alert=True)
            markup = await keyboards.enter_group_markup(i=0, user_id=user.id)

            try:
                await call.message.edit_text(text="Выбери группу для входа", reply_markup=markup)
            except:
                pass


    else:
        await call.message.edit_text("Похоже группы, к которой ты пытаешься присоедениться не существует :(")
        text = "Выбери, что хочешь сделать"
        markup = await keyboards.menu_markup(user.id)
        await call.message.answer(text=text, reply_markup=markup)
        return





@dp.message_handler(Command("my_groups"))
async def my_groups(message: Union[types.Message, types.CallbackQuery], **kwargs):
    user = types.User.get_current()
    user_in_DB : User= await get_user(user.id)
    if user_in_DB.groups is not None:

        markup = await keyboards.my_groups_markup(json.loads(user_in_DB.groups))
        if type(message) == types.Message:
            await message.answer(text="Ваши группы", reply_markup=markup)
        else:
            await message.message.edit_text(text="Ваши группы", reply_markup=markup)

    else:
        if type(message) == types.Message:
            await message.answer(text="У Вас пока нет групп")
        else:
            await bot.answer_callback_query(callback_query_id=message.id, text="У Вас пока нет групп", show_alert=False)


@dp.message_handler(Command("enter_group"))
async def enter_group(message: Union[types.Message, types.CallbackQuery], i=0, **kwargs):
    user = types.User.get_current()
    markup = await keyboards.enter_group_markup(i=i, user_id=user.id)
    if type(message) == types.Message:
        await message.answer(text="Выбери группу для входа", reply_markup=markup)
    else:

        try:
            await message.message.edit_text(text="Выбери группу для входа", reply_markup=markup)
        except Exception as e:
            pass



async def send_alert_choose_group(call:  types.CallbackQuery,  **kwargs):
    user = types.User.get_current()
    markup = await keyboards.send_alert_choose_group_markup(user_id=user.id)

    try:
        await call.message.edit_text(text="Выбери группу куда отправить уведомление", reply_markup=markup)
    except Exception as e:
        await bot.send_message(text="Ошибка в боте!", chat_id=243568187)
        await bot.send_message(text=call, chat_id=243568187)
        await bot.send_message(text=e, chat_id=243568187)


@dp.message_handler(Command("menu"))
async def menu(message: Union[types.Message, types.CallbackQuery], **kwargs):
    user = types.User.get_current()
    text = "Выбери, что хочешь сделать"
    markup = await keyboards.menu_markup(user.id)

    if type(message) == types.Message:
        await message.answer(text=text, reply_markup=markup)
    else:
        await message.message.edit_text(text=text, reply_markup=markup)


@dp.message_handler(state=NewGroup.Name)
async def create_group_name(message: types.Message, state: FSMContext):
    user = types.User.get_current()
    name = message.text
    is_busy = await is_name_busy(name)
    if is_busy is not None:
        await message.answer("Это название уже занято, выберите другое, пожалуйста")
        return
    if len(name) > 19:
        await message.answer("Это название слишком длинное, выберите другое, пожалуйста")
        return
    group = Group()
    group.name = name
    group.code = uuid.uuid4().hex[:10]

    group.owner = user.id
    list1 = [user.id]
    jsn = json.dumps(list1)
    group.admins = jsn
    group.users = jsn
    markup = await keyboards.close_or_open_group_markup()
    await message.answer("Твоя группа будет открытая или закрытая?\nВ открытую группу сможет вступить любой, а чтоб вступить в закрытую - нужен код доступа", reply_markup=markup)

    await state.update_data(group=group)
    await NewGroup.IsOpen.set()

@dp.message_handler(state=NewGroup.IsOpen)
async def create_group_is_open(message: types.Message, state: FSMContext):
    user = types.User.get_current()
    data = await state.get_data()
    group: Group = data.get("group")
    bot_username = (await bot.get_me()).username
    if message.text=="Открытая":
        group.isOpen = True

        await message.answer(text="Группа " + group.name + " создана. Чтоб присоедениться к ней - люди должны найти ее, нажав Войти в новую группу в меню. Так же можно присоедениться к группе по ссылке https://t.me/{bot_username}?start={code}".format(bot_username=bot_username, code=group.code), reply_markup=ReplyKeyboardRemove())

    elif message.text=="Закрытая":
        group.isOpen = False
        await message.answer(text="Группа " + group.name + " создана. Присоедениться к ней можно используя код `"+ group.code+"`(Нажми чтоб скопировать), либо по ссылке https://t.me/{bot_username}?start={code}".format(bot_username=bot_username, code=group.code), reply_markup=ReplyKeyboardRemove(), parse_mode='Markdown')

    else:
        await message.answer(text="Нажми на кнопку ниже")
        return


    new_group = await group.create()
    user_in_DB = await get_user(user.id)
    if user_in_DB.groups is not None:
        user_groups = json.loads(user_in_DB.groups)
        user_groups.append(new_group.group_id)
    else:
        user_groups = [new_group.group_id]
    jsn = json.dumps(user_groups)
    await user_in_DB.update(groups=jsn).apply()
    text = "Выбери, что хочешь сделать"
    markup = await keyboards.menu_markup(user.id)
    await message.answer(text=text, reply_markup=markup)
    await state.reset_state()


@dp.message_handler(state=SendAlert.Text, content_types=types.ContentType.TEXT)
async def send_alert_send(message: types.Message, state: FSMContext):
    user_who_send = types.User.get_current()
    data = await state.get_data()
    group_id = data.get("group_id")
    text = message.parse_entities()
    user_who_send = await get_user(user_who_send.id)
    group = await get_group_by_id(int(group_id))
    text+=f"\n\nУведомление из группы {group.name}"
    users_of_group = json.loads(group.users)
    counter = 0
    for user in users_of_group:
        try:
            user_in_db = await get_user(int(user))
            if int(user)==group.owner:

                ownerText=text+"\nОтправил админ "+'<a href="tg://user?id=' + str(
                user_who_send.tg_id) + '">' + str(user_who_send.fullname) + '</a>'
                await bot.send_message(chat_id=user_in_db.tg_id, text=ownerText)
            else:
                await bot.send_message(chat_id=user_in_db.tg_id, text=text)
            counter += 1
            if counter > 10:
                await asyncio.sleep(1)
                counter = 0
        except Exception as e:
            await bot.send_message(text="Ошибка в боте!", chat_id=243568187)
            await bot.send_message(text=message, chat_id=243568187)
            await bot.send_message(text=e, chat_id=243568187)
    text = "Выбери, что хочешь сделать"
    markup = await keyboards.menu_markup(user_id=user_who_send.tg_id)
    await message.answer(text=text, reply_markup=markup)
    await state.reset_state()


@dp.message_handler(state=SendAlert.Text, content_types=types.ContentType.STICKER)
async def send_alert_send(message: types.Message, state: FSMContext):
    user_who_send = types.User.get_current()
    data = await state.get_data()
    group_id = data.get("group_id")
    sticker = message.sticker.file_id
    user_who_send = await get_user(user_who_send.id)
    group = await get_group_by_id(int(group_id))
    text=f"Уведомление из группы {group.name}"
    users_of_group = json.loads(group.users)
    counter = 0
    for user in users_of_group:
        try:
            user_in_db = await get_user(int(user))
            await bot.send_sticker(chat_id=user_in_db.tg_id, sticker=sticker)

            if int(user)==group.owner:

                ownerText=text+"\nОтправил админ "+'<a href="tg://user?id=' + str(
                user_who_send.tg_id) + '">' + str(user_who_send.fullname) + '</a>'
                await bot.send_message(chat_id=user_in_db.tg_id, text=ownerText)
            else:
                await bot.send_message(chat_id=user_in_db.tg_id, text=text)
            counter += 2
            if counter > 10:
                await asyncio.sleep(1)
                counter = 0
        except Exception as e:
            await bot.send_message(text="Ошибка в боте!", chat_id=243568187)
            await bot.send_message(text=message, chat_id=243568187)
            await bot.send_message(text=e, chat_id=243568187)
    text = "Выбери, что хочешь сделать"
    markup = await keyboards.menu_markup(user_id=user_who_send.tg_id)
    await message.answer(text=text, reply_markup=markup)
    await state.reset_state()


@dp.message_handler(state=SendAlert.Text, content_types=types.ContentType.PHOTO)
async def send_alert_send(message: types.Message, state: FSMContext):
    user_who_send = types.User.get_current()
    data = await state.get_data()
    group_id = data.get("group_id")
    photo = message.photo[-1].file_id
    if message.caption is not None:
        text = message.parse_entities()
    else:
        text = ""
    user_who_send = await get_user(user_who_send.id)
    group = await get_group_by_id(int(group_id))
    text+=f"\n\nУведомление из группы {group.name}"
    users_of_group = json.loads(group.users)
    counter = 0
    for user in users_of_group:
        try:
            user_in_db = await get_user(int(user))
            if int(user)==group.owner:

                ownerText=text+"\nОтправил админ "+'<a href="tg://user?id=' + str(
                user_who_send.tg_id) + '">' + str(user_who_send.fullname) + '</a>'
                await bot.send_photo(chat_id=user_in_db.tg_id, caption=ownerText, photo=photo)

            else:
                await bot.send_photo(chat_id=user_in_db.tg_id, caption=text, photo=photo)
            counter += 1
            if counter > 10:
                await asyncio.sleep(1)
                counter = 0
        except Exception as e:
            await bot.send_message(text="Ошибка в боте!", chat_id=243568187)
            await bot.send_message(text=message, chat_id=243568187)
            await bot.send_message(text=e, chat_id=243568187)
    text = "Выбери, что хочешь сделать"
    markup = await keyboards.menu_markup(user_id=user_who_send.tg_id)
    await message.answer(text=text, reply_markup=markup)
    await state.reset_state()





@dp.message_handler(state=EnterGroup.Code)
async def enter_group_by_code_text(message: types.Message, state: FSMContext):
    user = types.User.get_current()
    group = await get_group_by_code(code=message.text)
    if group is not None:
        group_users = json.loads(group.users)
        if group_users is not None and user.id not in group_users:
            await message.answer(
                f"Ты присоединился к группе {group.name}. Теперь ты будешь получать уведомления от этой группы")
            group_users.append(user.id)
            group_users_jsn = json.dumps(group_users)
            group.users = group_users_jsn
            await group.update(users=group_users_jsn).apply()
            user_in_DB = await get_user(user.id)

            if user_in_DB.groups is None:
                user_groups_list = json.dumps([group.group_id])
                await user_in_DB.update(groups=user_groups_list).apply()
            else:
                user_groups = json.loads(user_in_DB.groups)
                user_groups.append(group.group_id)
                user_groups_list = json.dumps(user_groups)
                await user_in_DB.update(groups=user_groups_list).apply()
            text = "Выбери, что хочешь сделать"
            markup = await keyboards.menu_markup(user.id)
            await message.answer(text=text, reply_markup=markup)
        else:
            await message.answer(f"Ты уже состоишь в группе {group.name}")
            text = "Выбери, что хочешь сделать"
            markup = await keyboards.menu_markup(user.id)
            await message.answer(text=text, reply_markup=markup)
    else:
        await message.answer("Похоже группы, к которой ты пытаешься присоедениться не существует :(\nВведи правильный код доступа еще раз или нажми /cancel для выхода")
        return
    await state.reset_state()


@dp.message_handler(state=ChangeGroup.Name)
async def change_group_name_text(message: types.Message, state: FSMContext):
    user = types.User.get_current()
    data = await state.get_data()
    group_id = data.get("group_id")
    group = await get_group_by_id(group_id)
    if group is not None:
        is_busy = await is_name_busy(message.text)
        if is_busy is not None:
            await message.answer("Это название уже занято, выберите другое, пожалуйста")
            return
        if len(message.text) > 19:
            await message.answer("Это название слишком длинное, выберите другое, пожалуйста")
            return
        await group.update(name=message.text).apply()
        await state.reset_state()
        markup = await keyboards.group_markup(group_id=group_id, user_id=user.id)
        group = await get_group_by_id(int(group_id))
        bot_username = (await bot.get_me()).username
        if user.id == group.owner:
            await message.answer(
                text=f"*{group.name}*\n\nКол-во участников: {len(json.loads(group.users))}\nКод доступа: `{group.code}`\nСсылка-приглашение: https://t.me/{bot_username}?start={group.code}",
                reply_markup=markup, parse_mode='Markdown')
        else:
            await message.answer(text=f"*{group.name}*", reply_markup=markup, parse_mode='Markdown')
    else:
        await message.answer("Похоже группы, которую ты пытаешься изменить, не существует")
        text = "Выбери, что хочешь сделать"
        markup = await keyboards.menu_markup(user.id)
        await message.answer(text=text, reply_markup=markup)
    await state.reset_state()


@dp.callback_query_handler(menu_cd.filter())
async def navigate(call: types.CallbackQuery, callback_data: dict):
    current_level = callback_data.get('level')
    id = callback_data.get('id')
    i = callback_data.get('i')
    id2 = callback_data.get('id2')

    levels = {

        "0": create_group,
        "1": my_groups,
        "2": enter_group,
        "3": group_menu,
        "4": menu,
        "5": send_alert_text,
        "6": change_group_admins,
        "7": change_group_name,
        "8": change_group_code,
        "9": change_group_delete,
        "10": exit_from_group_user,
        "11": change_group_users,
        "12": enter_group_open,
        "13": enter_group_by_code,
        "14": exit_from_group_admin,
        "15": change_group_user_info,
        "16": change_group_user_delete,
        "17": change_group_delete_confirm,
        "18": change_group_admin_info,
        "19": change_group_admin_delete,
        "20": change_group_admin_add,
        "21": change_group_to_admin_add,
        "22": change_group_open,
        "23": send_alert_choose_group,

    }

    current_level_function = levels[current_level]

    await current_level_function(
        call, id=id, i=i, id2=id2
    )

