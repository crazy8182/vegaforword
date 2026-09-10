#Dont Remove My Credit @Silicon_Bot_Update 
#This Repo Is By @Silicon_Official 
# For Any Kind Of Error Ask Us In Support Group @Silicon_Botz 

import re
import asyncio 
from .utils import STS
from database import db
from config import temp 
from translation import Translation
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait 
from pyrogram.errors.exceptions.not_acceptable_406 import ChannelPrivate as PrivateChat
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified, ChannelPrivate
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
 
 #Dont Remove My Credit @Silicon_Bot_Update 
#This Repo Is By @Silicon_Official 
# For Any Kind Of Error Ask Us In Support Group @Silicon_Botz 
 
#===================Run Function===================#

@Client.on_message(filters.private & filters.command(["fwd", "forward"]))
async def run(bot, message):
    buttons = []
    btn_data = {}
    user_id = message.from_user.id
    bot_list = await db.get_bots(user_id)
    if not bot_list:
      return await message.reply("<code>__**You didn't added any bot. Please add a bot using /settings !**__</code>")

    # Each forwarding task is assigned to ONE selected forwarding bot.
    # This allows up to 3 completely independent tasks using 3 different bots.
    if len(bot_list) > 1:
       for saved in bot_list[:3]:
          kind = "🤖" if saved.get('is_bot') else "👤"
          label = f"{kind} {saved.get('name', 'Bot')} (@{saved.get('username') or saved.get('id')})"
          buttons.append([KeyboardButton(label)])
          btn_data[label] = int(saved['id'])
       buttons.append([KeyboardButton("cancel")])
       chosen = await bot.ask(user_id, "<b>ᴄʜᴏᴏsᴇ ᴡʜɪᴄʜ ғᴏʀᴡᴀʀᴅɪɴɢ ʙᴏᴛ ᴡɪʟʟ ʜᴀɴᴅʟᴇ ᴛʜɪs ᴛᴀsᴋ:</b>", reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True))
       if not chosen.text or chosen.text.lower().startswith(('/', 'cancel')):
          return await chosen.reply_text(Translation.CANCEL, reply_markup=ReplyKeyboardRemove())
       selected_bot_id = btn_data.get(chosen.text)
       if not selected_bot_id:
          return await chosen.reply_text("wrong bot choosen !", reply_markup=ReplyKeyboardRemove())
       _bot = next(b for b in bot_list if int(b['id']) == selected_bot_id)
    else:
       _bot = bot_list[0]
       selected_bot_id = int(_bot['id'])

    channels = await db.get_user_channels(user_id)
    if not channels:
       return await message.reply_text("Please set a to channel in /settings before forwarding", reply_markup=ReplyKeyboardRemove())
    if len(channels) > 1:
       for channel in channels:
          buttons.append([KeyboardButton(f"{channel['title']}")])
          btn_data[channel['title']] = channel['chat_id']
       buttons.append([KeyboardButton("cancel")])
       _toid = await bot.ask(message.chat.id, Translation.TO_MSG.format(_bot['name'], _bot['username']), reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True))
       if _toid.text.startswith(('/', 'cancel')):
          return await message.reply_text(Translation.CANCEL, reply_markup=ReplyKeyboardRemove())
       to_title = _toid.text
       toid = btn_data.get(to_title)
       if not toid:
          return await message.reply_text("wrong channel choosen !", reply_markup=ReplyKeyboardRemove())
    else:
       toid = channels[0]['chat_id']
       to_title = channels[0]['title']

    fromid = await bot.ask(message.chat.id, Translation.FROM_MSG, reply_markup=ReplyKeyboardRemove())
    if fromid.text and fromid.text.startswith('/'):
        await message.reply(Translation.CANCEL); return
    if fromid.text and not fromid.forward_date:
        regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
        match = regex.match(fromid.text.replace("?single", ""))
        if not match:
            return await message.reply('Invalid link')
        chat_id = match.group(4); last_msg_id = int(match.group(5))
        if chat_id.isnumeric(): chat_id = int(("-100" + chat_id))
    elif fromid.forward_from_chat.type in [enums.ChatType.CHANNEL]:
        last_msg_id = fromid.forward_from_message_id
        chat_id = fromid.forward_from_chat.username or fromid.forward_from_chat.id
        if last_msg_id is None:
           return await message.reply_text("**This may be a forwarded message from a group and sended by anonymous admin. instead of this please send last message link from group**")
    else:
        await message.reply_text("**invalid !**"); return
    try:
        title = (await bot.get_chat(chat_id)).title
    except (PrivateChat, ChannelPrivate, ChannelInvalid):
        title = "private" if fromid.text else fromid.forward_from_chat.title
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply('Invalid Link specified.')
    except Exception as e:
        return await message.reply(f'Errors - {e}')

    skipno = await bot.ask(message.chat.id, Translation.SKIP_MSG)
    if skipno.text.startswith('/'):
        await message.reply(Translation.CANCEL); return
    try:
        skip_value = int(skipno.text)
    except ValueError:
        return await skipno.reply("<b>Skip must be a number.</b>")

    forward_id = f"{user_id}-{skipno.id}"
    buttons = [[InlineKeyboardButton('Yes', callback_data=f"start_public_{forward_id}"), InlineKeyboardButton('No', callback_data="close_btn")]]
    await message.reply_text(
        text=Translation.DOUBLE_CHECK.format(botname=_bot['name'], botuname=_bot['username'], from_chat=title, to_chat=to_title, skip=skipno.text),
        disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(buttons))
    STS(forward_id).store(chat_id, toid, skip_value, int(last_msg_id), selected_bot_id)

