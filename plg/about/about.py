from plugin import TGBFPlugin
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler


class About(TGBFPlugin):

    async def init(self):
        await self.add_handler(CommandHandler(self.handle, self.init_callback, block=False))

    @TGBFPlugin.send_typing
    async def init_callback(self, update: Update, context: CallbackContext):
        msg = await update.message.reply_text(
            await self.get_plg_info(),
            disable_web_page_preview=True
        )

        if not self.is_private(update.message):
            self.remove_msg_after(update.message, msg, after_secs=20)

        import utils as utl
        print('External IP:', utl.get_external_ip())
