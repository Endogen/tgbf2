import emoji as emo

from plugin import TGBFPlugin
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler


class Admin(TGBFPlugin):

    async def init(self):
        await self.add_handler(CommandHandler(self.handle, self.init_callback, block=False))

    @TGBFPlugin.owner
    @TGBFPlugin.send_typing
    async def init_callback(self, update: Update, context: CallbackContext):
        if len(context.args) < 2:
            await update.message.reply_text(await self.get_plg_info())
            return

        sub_command = context.args[0].lower()
        plg_name = context.args[1].lower()

        if sub_command == 'disable':
            if plg_name in list(self.plugins.keys()):
                await self.tgb.disable_plugin(plg_name)
                await update.message.reply_text(f"{emo.DONE} Plugin '{plg_name}' disabled")
            else:
                await update.message.reply_text(f"{emo.WARNING} Plugin '{plg_name}' not available")

        elif sub_command == 'enable':
            worked, msg = await self.tgb.enable_plugin(plg_name)

            if worked:
                await update.message.reply_text(f"{emo.DONE} Plugin '{plg_name}' enabled")
            else:
                await update.message.reply_text(f"{emo.WARNING} Plugin '{plg_name}' not available")

        else:
            await update.message.reply_text(f'{emo.WARNING} Unknown argument(s)')
