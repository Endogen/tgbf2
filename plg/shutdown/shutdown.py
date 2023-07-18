import logging
import asyncio
import threading
import emoji as emo

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from plugin import TGBFPlugin


class Shutdown(TGBFPlugin):

    async def init(self):
        await self.add_handler(CommandHandler(self.handle, self.init_callback, block=False))

    @TGBFPlugin.owner
    @TGBFPlugin.private
    @TGBFPlugin.send_typing
    async def init_callback(self, update: Update, context: CallbackContext):
        msg = f"{emo.GOODBYE} Shutting down..."
        await update.message.reply_text(msg)
        logging.info(msg)

        threading.Thread(target=asyncio.run, args=(self.shutdown_callback(),)).start()

    async def shutdown_callback(self):
        await self.tgb.app.updater.stop()
        self.tgb.app.updater.is_idle = False