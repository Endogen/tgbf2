from plugin import TGBFPlugin
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler


class Start(TGBFPlugin):

    async def init(self):
        await self.add_handler(CommandHandler(self.handle, self.init_callback, block=False))

    @TGBFPlugin.send_typing
    async def init_callback(self, update: Update, context: CallbackContext):
        await update.message.reply_text(
            await self.get_plg_info(),
            disable_web_page_preview=True
        )
