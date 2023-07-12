import asyncio
import html
import os
import sys
import json
import shutil
import importlib
import traceback
from pathlib import Path

import nest_asyncio
import emoji as emo
import utils as utl
import constants as c

from loguru import logger
from dotenv import load_dotenv
from zipfile import ZipFile
from importlib import reload
from telegram import Chat, Update
from telegram.constants import ParseMode
from telegram.ext import Application, Defaults, MessageHandler, ContextTypes, filters, CallbackContext
from config import ConfigManager


class TelegramBot:

    def __init__(self):
        self.app = None
        self.plugins = list()
        self.cfg = ConfigManager(c.DIR_CFG / c.FILE_CFG)

    async def run(self):
        self.app = (
            Application.builder()
            .token(os.getenv('TG_TOKEN'))
            .defaults(Defaults(parse_mode=ParseMode.HTML))
            .build()
        )

        # Notify admin about bot start
        await self.app.updater.bot.send_message(
            chat_id=self.cfg.get('admin_tg_id'),
            text=f'{emo.ROBOT} Bot is up and running!'
        )

        # Load all plugins
        await self.load_plugins()

        # Add handler for file downloads (plugin updates)
        logger.info("Setting up plugin updates...")
        mh = MessageHandler(filters.ATTACHMENT, self._update_handler)
        self.app.add_handler(mh)

        # Handle all Telegram related errors
        logger.info("Setting up error handling...")
        self.app.add_error_handler(self._error_handler)

        # Start polling updates
        self.app.run_polling()

    async def load_plugins(self):
        """ Load all plugins from the 'plugins' folder """
        try:
            for _, folders, _ in os.walk(c.DIR_PLG):
                for folder in folders:
                    if folder.startswith("_"):
                        continue
                    logger.info(f"Plugin '{folder}' loading...")
                    await self.load_plugin(f"{folder}.py")
                break
        except Exception as e:
            logger.error(e)

    async def load_plugin(self, name):
        """ Load a single plugin """
        try:
            module_name, _ = os.path.splitext(name)
            module_path = f"{c.DIR_PLG}.{module_name}.{module_name}"
            module = importlib.import_module(module_path)

            # reload(module)  # TODO: Activate again

            async with getattr(module, module_name.capitalize())(self) as plugin:
                try:
                    self.plugins.append(plugin)
                    msg = f"Plugin '{plugin.name}' enabled"
                    logger.info(msg)
                    return True, msg
                except Exception as e:
                    msg = f"ERROR: Plugin '{plugin.name}' initialization failed: {e}"
                    logger.error(msg)
                    return False, str(e)
        except Exception as e:
            msg = f"ERROR: Plugin '{name}' can not be enabled: {e}"
            logger.error(msg)
            return False, str(e)

    async def _update_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Update a plugin by uploading a file to the bot.

        If you provide a .ZIP file then the content will be extracted into
        the plugin with the same name as the file. For example the file
        'about.zip' will be extracted into the 'about' plugin folder.

        It's also possible to provide a .PY file. In this case the file will
        replace the plugin implementation with the same name. For example the
        file 'about.py' will replace the same file in the 'about' plugin.

        All of this will only work in a private chat with the bot.
        """

        if not isinstance(update, Update):
            return
        if not update.message:
            return
        if context.bot.get_chat(update.message.chat_id).type != Chat.PRIVATE:
            return
        if update.effective_user.id is not self.cfg.get('admin_tg_id'):
            return

        name = update.message.effective_attachment.file_name.lower()
        zipped = False

        try:
            if name.endswith(".py"):
                plugin_name = name.replace(".py", "")
            elif name.endswith(".zip"):
                if len(name) == 18:
                    msg = f"{emo.ERROR} Only backups of plugins are supported"
                    await update.message.reply_text(text=msg)
                    return
                zipped = True
                if utl.is_numeric(name[:13]):
                    plugin_name = name[14:].replace(".zip", "")
                else:
                    plugin_name = name.replace(".zip", "")
            else:
                msg = f"{emo.ERROR} Wrong file format"
                await update.message.reply_text(msg)
                return

            file = context.bot.getFile(update.message.document.file_id)

            if zipped:
                os.makedirs(c.DIR_TMP, exist_ok=True)
                zip_path = os.path.join(c.DIR_TMP, name)
                file.download(zip_path)

                with ZipFile(zip_path, 'r') as zip_file:
                    plugin_path = os.path.join(c.DIR_PLG, plugin_name)
                    zip_file.extractall(plugin_path)
            else:
                file.download(os.path.join(c.DIR_PLG, plugin_name, name))

            self.disable_plugin(plugin_name)
            self.enable_plugin(plugin_name)

            shutil.rmtree(c.DIR_TMP, ignore_errors=True)

            await update.message.reply_text(f"{emo.DONE} Plugin successfully loaded")
        except Exception as e:
            logger.error(e)
            await update.message.reply_text(f"{emo.ERROR} {e}")

    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log the error and send a telegram message to notify the developer."""
        # Log the error before we do anything else, so we can see it even if something breaks.
        logger.error("Exception while handling an update:", exc_info=context.error)

        # traceback.format_exception returns the usual python message about an exception, but as a
        # list of strings rather than a single string, so we have to join them together.
        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = "".join(tb_list)

        # Build the message with some markup and additional information about what happened.
        # You might need to add some logic to deal with messages longer than the 4096 character limit.
        update_str = update.to_dict() if isinstance(update, Update) else str(update)
        message = (
            f"An exception was raised while handling an update\n"
            f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
            "</pre>\n\n"
            f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
            f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
            f"<pre>{html.escape(tb_string)}</pre>"
        )

        # Finally, send the message
        await context.bot.send_message(
            chat_id=self.cfg.get('admin_tg_id'), text=message, parse_mode=ParseMode.HTML
        )


if __name__ == "__main__":
    load_dotenv()

    logger.remove()

    logger.add(
        sys.stderr,
        level=os.getenv('LOG_LEVEL'))

    logger.add(
        os.path.join("log", "{time}.log"),
        format="{time} {name} {message}",
        level=os.getenv('LOG_LEVEL'),
        rotation="5 MB"
    )

    nest_asyncio.apply()
    asyncio.run(TelegramBot().run())
