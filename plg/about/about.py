from plugin import TGBFPlugin
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler


class About(TGBFPlugin):

    async def init(self):
        await self.add_handler(CommandHandler(self.handle, self.init_callback, block=False))
        await self.add_endpoint('test', self.action)  # TODO: Remove

    @TGBFPlugin.send_typing
    async def init_callback(self, update: Update, context: CallbackContext):
        msg = await update.message.reply_text(
            await self.get_plg_info(),
            disable_web_page_preview=True
        )

        if not self.is_private(update.message):
            self.remove_msg_after(update.message, msg, after_secs=20)

        # TODO: Remove
        await self.remove_handler(self.handlers[0])
        print('works')

    # TODO: Remove
    async def action(self):
        return 'WORKS'
