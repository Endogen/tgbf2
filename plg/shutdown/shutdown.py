import asyncio
import threading
import constants as con

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
        msg = f"{con.BYE} Shutting down..."
        await update.message.reply_text(msg)
        self.log.info(msg)

        threading.Thread(target=asyncio.run, args=(self.shutdown_callback(),)).start()

    async def shutdown_callback(self):
        await self.tgb.bot.updater.stop()
        self.tgb.bot.updater.is_idle = False
