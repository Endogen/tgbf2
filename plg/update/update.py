import shutil

import utils as utl
import emoji as emo
import constants as con

from pathlib import Path
from zipfile import ZipFile
from plugin import TGBFPlugin
from telegram import Update, Chat
from telegram.ext import CallbackContext, MessageHandler, filters


class Update(TGBFPlugin):

    async def init(self):
        await self.add_handler(
            MessageHandler(
                filters.Document.ZIP | filters.Document.FileExtension('py'), 
                self.init_callback,
                block=False
            )
        )
        
    @TGBFPlugin.send_typing
    async def init_callback(self, update: Update, context: CallbackContext):
        """
        Update a plugin by uploading a file to the bot.

        If you provide a .ZIP file then the content will be extracted into
        the plugin with the same name as the file. For example the file
        'about.zip' will be extracted into the 'about' plugin folder.

        It's also possible to provide a .PY file. In this case the file will
        replace the plugin implementation with the same name. For example the
        file 'about.py' will replace the same file in the 'about' plugin.

        It is also possible to upload a previously created backup of a plugin
        that was created with the /backup command.

        Will only work in a private chat and only if user is bot admin.
        """

        if not isinstance(update, Update):
            return
        if not update.message:
            return
        if update.effective_user.id != int(self.cfg.get('admin_tg_id')):
            return
        if (await context.bot.get_chat(update.message.chat_id)).type != Chat.PRIVATE:
            return

        name = update.message.document.file_name
        zipped = False

        try:
            if name.endswith(".py"):
                plugin_name = name.replace(".py", "")
            elif name.endswith(".zip"):
                zipped = True
                if utl.is_numeric(name[:13]):
                    plugin_name = name[14:].replace(".zip", "")
                else:
                    plugin_name = name.replace(".zip", "")
            else:
                self.log.warning(f"{emo.ERROR} Wrong file format for update")
                return

            file = await update.message.effective_attachment.get_file()

            if zipped:
                Path.mkdir(con.DIR_TMP, parents=True, exist_ok=True)
                zip_path = con.DIR_TMP / name

                await file.download_to_drive(zip_path)

                with ZipFile(zip_path, 'r') as zip_file:
                    the_path = Path(con.DIR_PLG / plugin_name)
                    zip_file.extractall(the_path)
            else:
                the_path = Path(con.DIR_PLG / plugin_name / name)
                await file.download_to_drive(the_path)

            await self.tgb.enable_plugin(plugin_name)

            shutil.rmtree(con.DIR_TMP, ignore_errors=True)

            await update.message.reply_text(f"{emo.DONE} Plugin successfully loaded")
        except Exception as e:
            self.log.error(e)
            await update.message.reply_text(f"{emo.ERROR} {e}")
