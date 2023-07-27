import os
import sys
import asyncio
import emoji as emo

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from plugin import TGBFPlugin


class Restart(TGBFPlugin):

    async def init(self):
        await self.add_handler(CommandHandler(self.handle, self.init_callback, block=False))

        chat_id = self.cfg.get("chat_id")
        mess_id = self.cfg.get("message_id")

        # If no data saved, don't do anything
        if not mess_id or not chat_id:
            return

        try:
            await self.tgb.app.bot.edit_message_text(
                chat_id=chat_id,
                message_id=mess_id,
                text=f"{emo.DONE} Restarting bot..."
            )
        except Exception as e:
            self.log.error(str(e))
        finally:
            self.cfg.remove("chat_id")
            self.cfg.remove("message_id")

    @TGBFPlugin.owner
    @TGBFPlugin.private
    @TGBFPlugin.send_typing
    async def init_callback(self, update: Update, context: CallbackContext):
        msg = await update.message.reply_text(f"{emo.HOURGLASS} Restarting bot...")

        chat_id = msg.chat_id
        mess_id = msg.message_id

        self.cfg.set(chat_id, "chat_id")
        self.cfg.set(mess_id, "message_id")

        m_name = __spec__.name
        m_name = m_name[:m_name.index(".")]

        await asyncio.sleep(1)
        os.execl(sys.executable, sys.executable, '-m', m_name, *sys.argv[1:])
