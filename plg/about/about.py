from plugin import TGBFPlugin
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler


class About(TGBFPlugin):

    async def init(self):
        await self.add_handler(CommandHandler(self.handle, self.init_callback))

    @TGBFPlugin.send_typing
    async def init_callback(self, update: Update, context: CallbackContext):
        msg = await update.message.reply_text(
            text="Created by ⒺⓃⒹⓄⒼⒺⓃ\n"
                 "This message will be removed in 5 seconds"
        )

        self.remove_msg_after(msg, 5)
