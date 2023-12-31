import constants as con

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from plugin import TGBFPlugin


class Restart(TGBFPlugin):

    async def init(self):
        await self.add_handler(CommandHandler(self.handle, self.init_callback, block=False))

        chat_id = self.cfg.get("chat_id")
        mess_id = self.cfg.get("message_id")

        # If no data saved, don't do anything
        if not mess_id or not chat_id:
            return

        try:
            await self.tgb.bot.bot.edit_message_text(
                chat_id=chat_id,
                message_id=mess_id,
                text=f"{con.DONE} Restarting bot..."
            )
        except Exception as e:
            self.log.error(str(e))
        finally:
            self.cfg.remove("chat_id")
            self.cfg.remove("message_id")

    @TGBFPlugin.owner
    @TGBFPlugin.private
    @TGBFPlugin.send_typing
    async def init_callback(self, update: Update, context: CallbackContext):
        msg = await update.message.reply_text(f"{con.WAIT} Restarting bot...")

        chat_id = msg.chat_id
        mess_id = msg.message_id

        context.bot_data["restart"] = True

        self.cfg.set(chat_id, "chat_id")
        self.cfg.set(mess_id, "message_id")

        # FIXME: Doesn't work
        self.tgb.bot.stop_running()
