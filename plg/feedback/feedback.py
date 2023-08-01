import emoji as emo

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from plugin import TGBFPlugin


class Feedback(TGBFPlugin):

    async def init(self):
        if not await self.table_exists("feedback"):
            sql = await self.get_resource("create_feedback.sql")
            await self.exec_sql(sql)

        await self.add_handler(CommandHandler(self.handle, self.init_callback, block=False))

    @TGBFPlugin.private
    @TGBFPlugin.send_typing
    async def init_callback(self, update: Update, context: CallbackContext):
        if not context.args:
            await update.message.reply_text(await self.get_info())
            return

        user = update.message.from_user
        name = f"@{user.username}" if user.username else user.first_name

        feedback = update.message.text.replace(f"/{self.handle} ", "")
        await self.notify(f"Feedback from {name}: {feedback}")

        sql = await self.get_resource("insert_feedback.sql")
        await self.exec_sql(sql, user.id, name, user.username, feedback)

        await update.message.reply_text(f"Thanks for letting us know {emo.HEART}")
