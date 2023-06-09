
# (c) @AbirHasan2005 | X-Noid

import traceback
import datetime
import asyncio
import string
import random
import time
import os
import aiofiles
import aiofiles.os
from database.access import clinton
from pyrogram import filters
from pyrogram import Client as Clinton
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid

from config import Config
broadcast_ids = {}


async def send_msg(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return 200, None
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return send_msg(user_id, message)
    except InputUserDeactivated:
        return 400, f"{user_id} : desactivada\n"
    except UserIsBlocked:
        return 400, f"{user_id} : bloqueó el bot\n"
    except PeerIdInvalid:
        return 400, f"{user_id} : ID de usuario inválida\n"
    except Exception as e:
        return 500, f"{user_id} : {traceback.format_exc()}\n"


@Clinton.on_message(filters.private & filters.command('broadcast') & filters.reply)
async def broadcast_(c, m):
    if m.from_user.id != Config.OWNER_ID:
        return
    all_users = await clinton.get_all_users()

    broadcast_msg = m.reply_to_message

    while True:
        broadcast_id = ''.join(
            [random.choice(string.ascii_letters) for i in range(3)])
        if not broadcast_ids.get(broadcast_id):
            break

    out = await m.reply_text(
        text=f"¡Transmisión iniciada! Se le notificará con el archivo de registro cuando se notifique a todos los usuarios."
    )
    start_time = time.time()
    total_users = await clinton.total_users_count()
    done = 0
    failed = 0
    success = 0

    broadcast_ids[broadcast_id] = dict(
        total=total_users,
        current=done,
        failed=failed,
        success=success
    )

    async with aiofiles.open('broadcast.txt', 'w') as broadcast_log_file:
        async for user in all_users:

            sts, msg = await send_msg(
                user_id=int(user['id']),
                message=broadcast_msg
            )
            if msg is not None:
                await broadcast_log_file.write(msg)

            if sts == 200:
                success += 1
            else:
                failed += 1

            if sts == 400:
                await clinton.delete_user(user['id'])

            done += 1
            if broadcast_ids.get(broadcast_id) is None:
                break
            else:
                broadcast_ids[broadcast_id].update(
                    dict(
                        current=done,
                        failed=failed,
                        success=success
                    )
                )
    if broadcast_ids.get(broadcast_id):
        broadcast_ids.pop(broadcast_id)
    completed_in = datetime.timedelta(seconds=int(time.time()-start_time))

    await asyncio.sleep(3)

    await out.delete()

    if failed == 0:
        await m.reply_text(
            text=f"transmisión completada en `{completed_in}`\n\nTotal de usuarios {total_users}.\nTotal realizado {done}, {success} éxito y {failed} fallido.",
            quote=True
        )
    else:
        await m.reply_document(
            document='broadcast.txt',
            caption=f"transmisión completada en `{completed_in}`\n\nTotal de usuario {total_users}.\nTotal realizado {done}, {success} éxito y {failed} fallido.",
            quote=True
        )

    await aiofiles.os.remove('broadcast.txt')
