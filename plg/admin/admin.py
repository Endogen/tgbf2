import emoji as emo

from plugin import TGBFPlugin
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler


class Admin(TGBFPlugin):

    async def init(self):
        await self.add_handler(CommandHandler(self.handle, self.init_callback))

    @TGBFPlugin.send_typing
    async def init_callback(self, update: Update, context: CallbackContext):
        if len(context.args) < 2:
            await update.message.reply_text(await self.get_usage())
            return

        sub_command = context.args[0].lower()
        plg_name = context.args[1].lower()

        if sub_command == 'disable':
            await self.tgb.disable_plugin(plg_name)
            await update.message.reply_text(f'{emo.DONE} Disabled plugin {plg_name}')
        elif sub_command == 'enable':
            await self.tgb.enable_plugin(plg_name)
            await update.message.reply_text(f'{emo.DONE} Enabled plugin {plg_name}')
        else:
            await update.message.reply_text(f'{emo.WARNING} Unknown argument(s)')
