from plugin import TGBFPlugin
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler


class About(TGBFPlugin):

    async def init(self):
        await self.add_handler(CommandHandler("about", self.about_callback))

    @TGBFPlugin.send_typing
    async def about_callback(self, update: Update, context: CallbackContext):
        msg = await update.message.reply_text(text="WORKS")
