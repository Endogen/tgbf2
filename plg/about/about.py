from plugin import TGBFPlugin
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler


class About(TGBFPlugin):

    async def init(self):
        if not await self.table_exists('test'):
            sql = await self.get_resource("create_test.sql")
            await self.exec_sql(sql)

        await self.add_handler(CommandHandler(self.handle, self.init_callback))

    @TGBFPlugin.send_typing
    async def init_callback(self, update: Update, context: CallbackContext):
        await update.message.reply_text(text="WORKS")
