#Dont Remove My Credit @Silicon_Bot_Update 
#This Repo Is By @Silicon_Official 
# For Any Kind Of Error Ask Us In Support Group @Silicon_Botz 

import os
import sys 
import math
import time
import asyncio 
import logging
from .utils import STS
from database import db 
from .test import CLIENT , start_clone_bot
from config import Config, temp
from translation import Translation
from pyrogram import Client, filters 
#from pyropatch.utils import unpack_new_file_id
from pyrogram.errors import FloodWait, MessageNotModified, RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message 

CLIENT = CLIENT()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
TEXT = Translation.TEXT


#Dont Remove My Credit @Silicon_Bot_Update 
#This Repo Is By @Silicon_Official 
# For Any Kind Of Error Ask Us In Support Group @Silicon_Botz 

@Client.on_callback_query(filters.regex(r'^start_public'))
async def pub_(bot, message):
    user = message.from_user.id
    temp.CANCEL[user] = False
    frwd_id = message.data.split("_")[2]
    sts = STS(frwd_id)
    if not sts.verify():
      await message.answer("ᴏʟᴅ ᴏʀ ɪɴᴠᴀʟɪᴅ ᴛᴀsᴋ.", show_alert=True)
      return await message.message.delete()
    i = sts.get(full=True)

    # A target can have only one active forwarding task for this user.
    if i.TO in temp.IS_FRWD_CHAT:
      return await message.answer("ᴛʜɪs ᴛᴀʀɢᴇᴛ ɪs ᴀʟʀᴇᴀᴅʏ ʙᴇɪɴɢ ᴜsᴇᴅ.", show_alert=True)

    m = await msg_edit(message.message, "<i><b>ᴠᴇʀɪғʏɪɴɢ ʏᴏᴜʀ ᴅᴀᴛᴀ ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ.</b></i>")
    bots, caption, forward_tag, data, protect, button = await sts.get_data(user)
    bot_list = await db.get_bots(user)
    if not bot_list:
      return await msg_edit(m, "<code>ʏᴏᴜ ᴅɪᴅ ɴᴏᴛ ᴀᴅᴅᴇᴅ ᴀɴʏ ʙᴏᴛ ʏᴇᴛ. ᴜsᴇ /settings</code>", wait=True)

    # Use up to three saved bots. The existing forwarding/copy functions are
    # intentionally unchanged; workers only split the source ID range.
    bot_list = bot_list[:3]
    await msg_edit(m, f"<b>ᴘʀᴇᴘᴀʀɪɴɢ {len(bot_list)} ғᴏʀᴡᴀʀᴅɪɴɢ ᴡᴏʀᴋᴇʀ(s)...</b>")

    # Build persistent task before starting workers so a restart can recover it.
    task_id = frwd_id
    start_id = int(i.skip)
    end_id = int(i.limit)
    total_ids = max(0, end_id - start_id + 1)
    worker_count = min(len(bot_list), max(1, total_ids))
    workers = []
    base, extra = divmod(total_ids, worker_count)
    cursor = start_id
    for idx in range(worker_count):
      size = base + (1 if idx < extra else 0)
      w_start = cursor
      w_end = cursor + size - 1
      cursor = w_end + 1
      workers.append({
        'index': idx, 'bot_id': int(bot_list[idx]['id']), 'start': w_start,
        'end': w_end, 'next': w_start, 'fetched': 0, 'forwarded': 0,
        'deleted': 0, 'duplicate': 0, 'filtered': 0, 'status': 'pending'
      })

    task = {
      '_id': task_id, 'user_id': int(user), 'FROM': i.FROM, 'TO': i.TO,
      'start': start_id, 'end': end_id, 'status': 'running',
      'forward_tag': bool(forward_tag), 'caption': caption, 'protect': protect,
      'button': button,
      # Snapshot filter settings into the task so they remain stable across restarts.
      'filters': dict(data.get('filters') or {}),
      'keywords': list(data.get('keywords') or []),
      'extensions': list(data.get('extensions') or []),
      'media_size': data.get('media_size'), 'workers': workers, 'control_chat': int(user),
      'created_at': time.time(), 'updated_at': time.time()
    }
    await db.create_forward_task(task)

    temp.lock[user] = True
    temp.IS_FRWD_CHAT.append(i.TO)
    temp.forwardings += 1
    await db.add_frwd(user)
    await send(client=bot, user=user, text=f"<b>🚥 ғᴏʀᴡᴀʀᴅɪɴɢ sᴛᴀʀᴛᴇᴅ ᴡɪᴛʜ {worker_count} ʙᴏᴛs</b>")

    try:
      results = await asyncio.gather(*[
        run_worker(task, idx, bot_list[idx], m, frwd_id)
        for idx in range(worker_count)
      ], return_exceptions=True)
      errors = [r for r in results if isinstance(r, Exception)]
      current = await db.get_forward_task(task_id)
      if errors:
        err = "; ".join(str(e) for e in errors[:3])
        await db.set_forward_task(task_id, status='paused', error=err, updated_at=time.time())
        await msg_edit(m, f'<b>ᴛᴀsᴋ ᴘᴀᴜsᴇᴅ:</b>\n<code>{err}</code>', wait=True)
      elif current and current.get('status') == 'running':
        await db.set_forward_task(task_id, status='completed', updated_at=time.time())
        await send(bot, user, "<b>🎉 ғᴏʀᴡᴀʀᴅɪɴɢ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</b>")
        await edit(m, 'ᴄᴏᴍᴘʟᴇᴛᴇᴅ', 'ᴄᴏᴍᴘʟᴇᴛᴇᴅ', sts)
    finally:
      if i.TO in temp.IS_FRWD_CHAT:
        temp.IS_FRWD_CHAT.remove(i.TO)
      temp.lock[user] = False
      temp.CANCEL[user] = False
      temp.forwardings = max(0, temp.forwardings - 1)
      await db.rmve_frwd(user)


async def run_worker(task, worker_index, bot_data, status_msg=None, frwd_id=None):
    """Run one source-ID partition. Forwarding functions are unchanged."""
    user = int(task['user_id'])
    task_id = task['_id']
    worker = task['workers'][worker_index]
    client = None
    try:
      client = await start_clone_bot(CLIENT.client(bot_data))
      worker['status'] = 'running'
      await db.update_forward_worker(task_id, worker_index, status='running')
      await _worker_loop(client, task, worker_index, status_msg, frwd_id, bot_data)
      if temp.CANCEL.get(user) is True:
        await db.update_forward_worker(task_id, worker_index, status='paused', updated_at=time.time())
      else:
        await db.update_forward_worker(task_id, worker_index, status='completed', next=worker['end'] + 1, updated_at=time.time())
    except FloodWait as e:
      await asyncio.sleep(e.value + 1)
      return await run_worker(task, worker_index, bot_data, status_msg, frwd_id)
    except Exception as e:
      await db.update_forward_worker(task_id, worker_index, status='paused', error=str(e), updated_at=time.time())
      raise
    finally:
      if client:
        try: await client.stop()
        except: pass


async def _worker_loop(client, task, worker_index, status_msg=None, frwd_id=None, bot_data=None):
    task_id = task['_id']
    worker = task['workers'][worker_index]
    start = int(worker.get('next', worker['start']))
    end = int(worker['end'])
    if start > end:
      return

    # Keep the original timing/forwarding path intact.
    sleep = 0.5 if (bot_data or {}).get('is_bot', True) else 5
    MSG = []
    pending_checkpoint = 0
    fetched_local = int(worker.get('fetched', 0))
    forwarded_local = int(worker.get('forwarded', 0))
    async for message in client.iter_messages(client, chat_id=task['FROM'], limit=end, offset=start):
      if temp.CANCEL.get(int(task['user_id'])) is True:
        await db.set_forward_task(task_id, status='paused', updated_at=time.time())
        return
      fetched_local += 1
      worker['fetched'] = fetched_local
      if frwd_id:
        try: STS(frwd_id).add('fetched')
        except Exception: pass
      worker['next'] = getattr(message, 'id', start) + 1

      if message.empty or message.service:
        worker['deleted'] = int(worker.get('deleted', 0)) + 1
        pending_checkpoint += 1
      elif not message_matches_filters(message, task):
        worker['filtered'] = int(worker.get('filtered', 0)) + 1
        if frwd_id:
          try: STS(frwd_id).add('filtered')
          except Exception: pass
        pending_checkpoint += 1
      elif task.get('forward_tag'):
        MSG.append(message.id)
        if len(MSG) >= 100 or message.id >= end:
          await forward(client, MSG, status_msg, STS(frwd_id) if frwd_id else STS(task_id), task.get('protect'))
          forwarded_local += len(MSG)
          worker['forwarded'] = forwarded_local
          if frwd_id:
            try: STS(frwd_id).add('total_files', len(MSG))
            except Exception: pass
          MSG = []
          pending_checkpoint = 100
          await db.update_forward_worker(task_id, worker_index,
              next=worker['next'], fetched=fetched_local, forwarded=forwarded_local,
              updated_at=time.time())
          await asyncio.sleep(2)
      else:
        new_caption = custom_caption(message, task.get('caption'))
        details = {'msg_id': message.id, 'media': media(message), 'caption': new_caption,
                   'button': task.get('button'), 'protect': task.get('protect')}
        await copy(client, details, status_msg, STS(frwd_id) if frwd_id else STS(task_id))
        forwarded_local += 1
        worker['forwarded'] = forwarded_local
        if frwd_id:
          try: STS(frwd_id).add('total_files')
          except Exception: pass
        pending_checkpoint += 1
        await asyncio.sleep(sleep)

      # Persistent checkpoint. At most ~25 processed IDs need replay after a hard restart.
      if pending_checkpoint >= 25:
        await db.update_forward_worker(task_id, worker_index,
            next=worker['next'], fetched=fetched_local,
            forwarded=forwarded_local, deleted=worker.get('deleted', 0),
            duplicate=worker.get('duplicate', 0), filtered=worker.get('filtered', 0),
            updated_at=time.time())
        pending_checkpoint = 0

    if MSG:
      await forward(client, MSG, status_msg, STS(frwd_id) if frwd_id else STS(task_id), task.get('protect'))
      forwarded_local += len(MSG)
    await db.update_forward_worker(task_id, worker_index, next=end + 1,
        fetched=fetched_local, forwarded=forwarded_local, status='completed', updated_at=time.time())


async def recover_forward_tasks(app):
    """Resume every persisted running/paused task after a process restart."""
    tasks = await db.get_active_forward_tasks()
    for task in tasks:
      try:
        # A task with no unfinished workers is finalized instead of being duplicated.
        unfinished = [w for w in task.get('workers', []) if int(w.get('next', w.get('start', 0))) <= int(w.get('end', -1))]
        if not unfinished:
          await db.set_forward_task(task['_id'], status='completed', updated_at=time.time())
          continue
        await db.set_forward_task(task['_id'], status='recovering', updated_at=time.time())
        user = int(task['user_id'])
        if temp.lock.get(user):
          continue
        temp.lock[user] = True
        temp.CANCEL[user] = False
        temp.IS_FRWD_CHAT.append(task['TO'])
        temp.forwardings += 1
        await send(app, user, f"<b>♻️ ᴛᴀsᴋ ʀᴇsᴜᴍɪɴɢ ғʀᴏᴍ sᴀᴠᴇᴅ ᴘʀᴏɢʀᴇss ({len(unfinished)} ᴡᴏʀᴋᴇʀs)</b>")
        bots = await db.get_bots(user)
        by_id = {int(b['id']): b for b in bots}
        async def resume_one(w):
          b = by_id.get(int(w['bot_id']))
          if not b:
            raise RuntimeError(f"saved worker bot {w['bot_id']} is missing")
          await run_worker(task, int(w['index']), b, None, task['_id'])
        results = await asyncio.gather(*(resume_one(w) for w in unfinished), return_exceptions=True)
        errors = [r for r in results if isinstance(r, Exception)]
        if errors:
          await db.set_forward_task(task['_id'], status='paused', error='; '.join(str(e) for e in errors[:3]), updated_at=time.time())
        else:
          current = await db.get_forward_task(task['_id'])
          if current and current.get('status') in ('recovering', 'running'):
            await db.set_forward_task(task['_id'], status='completed', updated_at=time.time())
            await send(app, user, "<b>🎉 ғᴏʀᴡᴀʀᴅɪɴɢ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</b>")
      except Exception as e:
        logger.exception("recovery failed for %s: %s", task.get('_id'), e)
        await db.set_forward_task(task['_id'], status='paused', error=str(e), updated_at=time.time())
      finally:
        user = int(task['user_id'])
        if task.get('TO') in temp.IS_FRWD_CHAT:
          temp.IS_FRWD_CHAT.remove(task['TO'])
        temp.lock[user] = False
        temp.CANCEL[user] = False
        temp.forwardings = max(0, temp.forwardings - 1)
        await db.rmve_frwd(user)

#Dont Remove My Credit @Silicon_Bot_Update 
#This Repo Is By @Silicon_Official 
# For Any Kind Of Error Ask Us In Support Group @Silicon_Botz 

async def copy(bot, msg, m, sts):
   try:                                  
     if msg.get("media") and msg.get("caption"):
        await bot.send_cached_media(
              chat_id=sts.get('TO'),
              file_id=msg.get("media"),
              caption=msg.get("caption"),
              reply_markup=msg.get('button'),
              protect_content=msg.get("protect"))
     else:
        await bot.copy_message(
              chat_id=sts.get('TO'),
              from_chat_id=sts.get('FROM'),    
              caption=msg.get("caption"),
              message_id=msg.get("msg_id"),
              reply_markup=msg.get('button'),
              protect_content=msg.get("protect"))
   except FloodWait as e:
     await edit(m, 'ᴘʀᴏɢʀᴇssɪɴɢ', e.value, sts)
     await asyncio.sleep(e.value)
     await edit(m, 'ᴘʀᴏɢʀᴇssɪɴɢ', 5, sts)
     await copy(bot, msg, m, sts)
   except Exception as e:
     print(e)
     sts.add('deleted')

#Dont Remove My Credit @Silicon_Bot_Update 
#This Repo Is By @Silicon_Official 
# For Any Kind Of Error Ask Us In Support Group @Silicon_Botz 

async def forward(bot, msg, m, sts, protect):
   try:                             
     await bot.forward_messages(
           chat_id=sts.get('TO'),
           from_chat_id=sts.get('FROM'), 
           protect_content=protect,
           message_ids=msg)
   except FloodWait as e:
     await edit(m, 'ᴘʀᴏɢʀᴇssɪɴɢ', e.value, sts)
     await asyncio.sleep(e.value)
     await edit(m, 'ᴘʀᴏɢʀᴇssɪɴɢ', 5, sts)
     await forward(bot, msg, m, sts, protect)

PROGRESS = """
📈 ᴘᴇʀᴄᴇɴᴛᴀɢᴇ : {0} %

⭕ ғᴇᴛᴄʜᴇᴅ : {1}

⚙️ ғᴏʀᴡᴀʀᴅᴇᴅ : {2}

🗞️ ʀᴇᴍᴀɴɪɴɢ : {3}

♻️ sᴛᴀᴛᴜs : {4}

⏳️ ᴇᴛᴀ : {5}
"""

async def msg_edit(msg, text, button=None, wait=None):
    try:
        return await msg.edit(text, reply_markup=button)
    except MessageNotModified:
        pass 
    except FloodWait as e:
        if wait:
           await asyncio.sleep(e.value)
           return await msg_edit(msg, text, button, wait)

#Dont Remove My Credit @Silicon_Bot_Update 
#This Repo Is By @Silicon_Official 
# For Any Kind Of Error Ask Us In Support Group @Silicon_Botz 

async def edit(msg, title, status, sts):
   i = sts.get(full=True)
   status = 'ғᴏʀᴡᴀʀᴅɪɴɢ' if status == 10 else f"sʟᴇᴇᴘɪɴɢ {status} s" if str(status).isnumeric() else status
   percentage = "{:.0f}".format(float(i.fetched)*100/float(i.total))

   now = time.time()
   diff = int(now - i.start)
   speed = sts.divide(i.fetched, diff)
   elapsed_time = round(diff) * 1000
   time_to_completion = round(sts.divide(i.total - i.fetched, int(speed))) * 1000
   estimated_total_time = elapsed_time + time_to_completion  
   
   progress = "▰{0}{1}".format(
       ''.join(["▰" for i in range(math.floor(int(percentage) / 10))]),
       ''.join(["▱" for i in range(10 - math.floor(int(percentage) / 10))]))
   button =  [[InlineKeyboardButton(progress, f'fwrdstatus#{status}#{estimated_total_time}#{percentage}#{i.id}')]]
   estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)
   estimated_total_time = estimated_total_time if estimated_total_time != '' else '0 s'

   text = TEXT.format(i.total, i.fetched, i.total_files, i.duplicate, i.deleted, i.skip, i.filtered, status, percentage, title)
   if status in ["ᴄᴀɴᴄᴇʟʟᴇᴅ", "ᴄᴏᴍᴘʟᴇᴛᴇᴅ"]:
      button.append(
         [InlineKeyboardButton('💟sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ💟', url='https://t.me/Silicon_Botz')])
      button.append(
         [InlineKeyboardButton('💠ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ💠', url='https://t.me/Silicon_Bot_Update')]
         )
   else:
      button.append([InlineKeyboardButton('• ᴄᴀɴᴄᴇʟ', 'terminate_frwd')])
   await msg_edit(msg, text, InlineKeyboardMarkup(button))

async def is_cancelled(client, user, msg, sts):
   if temp.CANCEL.get(user)==True:
      temp.IS_FRWD_CHAT.remove(sts.TO)
      await edit(msg, "ᴄᴀɴᴄᴇʟʟᴇᴅ", "ᴄᴏᴍᴘʟᴇᴛᴇᴅ", sts)
      await send(client, user, "<b>❌ ғᴏʀᴡᴀʀᴅɪɴɢ ᴄᴀɴᴄᴇʟʟᴇᴅ</b>")
      await stop(client, user)
      return True 
   return False 

#Dont Remove My Credit @Silicon_Bot_Update 
#This Repo Is By @Silicon_Official 
# For Any Kind Of Error Ask Us In Support Group @Silicon_Botz 

async def stop(client, user):
   try:
     await client.stop()
   except:
     pass 
   await db.rmve_frwd(user)
   temp.forwardings -= 1
   temp.lock[user] = False 

async def send(bot, user, text):
   try:
      await bot.send_message(user, text=text)
   except:
      pass 

#Dont Remove My Credit @Silicon_Bot_Update 
#This Repo Is By @Silicon_Official 
# For Any Kind Of Error Ask Us In Support Group @Silicon_Botz 


def _message_media_info(msg):
  """Return (type, file_name, file_size) for filter evaluation."""
  if getattr(msg, 'text', None) is not None or getattr(msg, 'caption', None) is not None:
    # Media messages are classified by their media first; plain text below.
    pass
  media_type = getattr(getattr(msg, 'media', None), 'value', None)
  if media_type:
    obj = getattr(msg, media_type, None)
    return media_type, getattr(obj, 'file_name', '') if obj else '', getattr(obj, 'file_size', 0) if obj else 0
  return 'text', '', 0

def message_matches_filters(msg, task):
  """Apply Settings -> Filters to a source message. False means do not forward."""
  filters_cfg = task.get('filters') or {}
  media_type, file_name, file_size = _message_media_info(msg)
  if not filters_cfg.get(media_type, True):
    return False

  # Extensions are an exclusion list. Accept both .mkv and mkv.
  extensions = task.get('extensions') or []
  if file_name and extensions:
    name = file_name.lower().strip()
    for ext in extensions:
      ext = str(ext).strip().lower()
      if not ext:
        continue
      if not ext.startswith('.'):
        ext = '.' + ext
      if name.endswith(ext):
        return False

  # Keywords are an inclusion list: if configured, filename must contain one.
  keywords = [str(x).strip().lower() for x in (task.get('keywords') or []) if str(x).strip()]
  if keywords and file_name:
    if not any(k in file_name.lower() for k in keywords):
      return False
  elif keywords and media_type not in ('text',):
    return False

  # Size filter is [MB threshold, None/True/False].
  media_size = task.get('media_size')
  if media_size and file_size:
    try:
      threshold_mb, mode = media_size
      threshold = float(threshold_mb) * 1024 * 1024
      current = float(file_size)
      if mode is True and current <= threshold:
        return False
      if mode is False and current >= threshold:
        return False
    except (TypeError, ValueError):
      pass
  return True

def custom_caption(msg, caption):
  if msg.media:
    if (msg.video or msg.document or msg.audio or msg.photo):
      media = getattr(msg, msg.media.value, None)
      if media:
        file_name = getattr(media, 'file_name', '')
        file_size = getattr(media, 'file_size', '')
        fcaption = getattr(msg, 'caption', '')
        if fcaption:
          fcaption = fcaption.html
        if caption:
          return caption.format(filename=file_name, size=get_size(file_size), caption=fcaption)
        return fcaption
  return None

#Dont Remove My Credit @Silicon_Bot_Update 
#This Repo Is By @Silicon_Official 
# For Any Kind Of Error Ask Us In Support Group @Silicon_Botz 

def get_size(size):
  units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
  size = float(size)
  i = 0
  while size >= 1024.0 and i < len(units):
     i += 1
     size /= 1024.0
  return "%.2f %s" % (size, units[i]) 

def media(msg):
  if msg.media:
     media = getattr(msg, msg.media.value, None)
     if media:
        return getattr(media, 'file_id', None)
  return None 
  
#Dont Remove My Credit @Silicon_Bot_Update 
#This Repo Is By @Silicon_Official 
# For Any Kind Of Error Ask Us In Support Group @Silicon_Botz 

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]

def retry_btn(id):
    return InlineKeyboardMarkup([[InlineKeyboardButton('♻️ ʀᴇᴛʀʏ ♻️', f"start_public_{id}")]])

@Client.on_callback_query(filters.regex(r'^terminate_frwd$'))
async def terminate_frwding(bot, m):
    user_id = m.from_user.id 
    temp.lock[user_id] = False
    temp.CANCEL[user_id] = True 
    await m.answer("ғᴏʀᴡᴀʀᴅɪɴɢ ᴄᴀɴᴄᴇʟʟᴇᴅ !", show_alert=True)

#Dont Remove My Credit @Silicon_Bot_Update 
#This Repo Is By @Silicon_Official 
# For Any Kind Of Error Ask Us In Support Group @Silicon_Botz 

@Client.on_callback_query(filters.regex(r'^fwrdstatus'))
async def status_msg(bot, msg):
    _, status, est_time, percentage, frwd_id = msg.data.split("#")
    sts = STS(frwd_id)
    if not sts.verify():
       fetched, forwarded, remaining, skipped = 0
    else:
       total = sts.get('total')
       skipped = sts.get('skip')
       fetched, forwarded = sts.get('fetched'), sts.get('total_files')
       remaining = total - forwarded - skipped
    est_time = TimeFormatter(milliseconds=est_time)
    est_time = est_time if (est_time != '' or status not in ['completed', 'cancelled']) else '0 s'
    return await msg.answer(PROGRESS.format(percentage, fetched, forwarded, remaining, status, est_time), show_alert=True)

#Dont Remove My Credit @Silicon_Bot_Update 
#This Repo Is By @Silicon_Official 
# For Any Kind Of Error Ask Us In Support Group @Silicon_Botz 

@Client.on_message(filters.command("stop"))
async def stop_forwarding(bot, message):
    user_id = message.from_user.id
    if temp.lock.get(user_id):
        temp.lock[user_id] = False
        temp.CANCEL[user_id] = True
        await message.reply("🛑 ғᴏʀᴡᴀʀᴅɪɴɢ ᴄᴀɴᴄᴇʟʟᴇᴅ !", quote=True)
        # Optionally, notify the user in a more detailed way.
    else:
        await message.reply("❌ ɴᴏ ᴏɴɢᴏɪɴɢ ғᴏʀᴡᴀʀᴅɪɴɢ ᴘʀᴏᴄᴇss ᴛᴏ ᴄᴀɴᴄᴇʟ.", quote=True)

@Client.on_callback_query(filters.regex(r'^close_btn$'))
async def close(bot, update):
    await update.answer()
    await update.message.delete()
    
 #Dont Remove My Credit @Silicon_Bot_Update 
#This Repo Is By @Silicon_Official 
# For Any Kind Of Error Ask Us In Support Group @Silicon_Botz 
