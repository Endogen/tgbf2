import constants as con

from pathlib import Path
from telegram import Update
from plugin import TGBFPlugin
from telegram.ext import CallbackContext, CommandHandler


class Logfile(TGBFPlugin):

    async def init(self):
        await self.add_handler(CommandHandler(self.handle, self.init_callback, block=False))
        await self.add_handler(CommandHandler('log', self.init_callback, block=False))

    @TGBFPlugin.owner
    @TGBFPlugin.private
    @TGBFPlugin.send_typing
    async def init_callback(self, update: Update, context: CallbackContext):
        log_file = max(con.DIR_LOG.glob('*.log'), key=lambda item: item.stat().st_ctime)

        if Path.is_file(Path(log_file)):
            try:
                file = open(log_file, 'rb')
            except Exception as e:
                file = None
                self.log.error(e)
                await self.notify(e)
        else:
            file = None

        if file:
            await update.message.reply_document(document=file)
        else:
            await update.message.reply_text(f"{con.WARNING} No logfile found")
