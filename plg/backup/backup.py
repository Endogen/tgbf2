import os
import os.path
import zipfile
import time
import constants as con

from pathlib import Path
from plugin import TGBFPlugin
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler


class Backup(TGBFPlugin):

    async def init(self):
        await self.add_handler(CommandHandler(self.handle, self.init_callback, block=False))

    @TGBFPlugin.owner
    @TGBFPlugin.private
    @TGBFPlugin.send_typing
    async def init_callback(self, update: Update, context: CallbackContext):
        command = ""

        if len(context.args) == 1:
            command = context.args[0].lower().strip()

            if not self.is_enabled(command):
                msg = f"{con.ERROR} Plugin '{command}' not available"
                await update.message.reply_text(msg)
                return

        # List of folders to exclude from backup
        exclude = [con.DIR_LOG, con.DIR_TMP, con.DIR_BCK, "__pycache__"]

        Path.mkdir(con.DIR_BCK, exist_ok=True)

        filename = os.path.join(con.DIR_BCK, f"{time.strftime('%Y%m%d%H%M%S')}{command}.zip")
        with zipfile.ZipFile(filename, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            if command:
                base_dir = os.path.join(os.getcwd(), con.DIR_PLG, command)
            else:
                base_dir = os.getcwd()

            for root, dirs, files in os.walk(base_dir, topdown=True):
                dirs[:] = [d for d in dirs if d not in exclude and not d.startswith(".")]
                for name in dirs:
                    path = os.path.normpath(os.path.join(root, name))
                    write_path = os.path.relpath(path, base_dir)
                    zf.write(path, write_path)
                files[:] = [f for f in files if not f.startswith(".")]
                for name in files:
                    path = os.path.normpath(os.path.join(root, name))
                    write_path = os.path.relpath(path, base_dir)
                    zf.write(path, write_path)

        filepath = Path(Path.cwd(), filename)

        try:
            await context.bot.send_document(
                chat_id=update.effective_user.id,
                caption=f"{con.DONE} Backup created",
                document=open(filepath, 'rb'))
        except Exception as e:
            self.log.error(e)
            await update.message.reply_text(f"{con.ERROR} {e}")
