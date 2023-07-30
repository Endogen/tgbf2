import asyncio
import html
import os
import sys
import json
import shutil
import importlib
import traceback
import nest_asyncio
from starlette.responses import FileResponse

import emoji as emo
import utils as utl
import constants as c

from pathlib import Path
from loguru import logger
from zipfile import ZipFile
from dotenv import load_dotenv
from telegram import Chat, Update
from telegram.error import InvalidToken
from telegram.constants import ParseMode
from telegram.ext import Application, Defaults, MessageHandler, ContextTypes, filters, CallbackContext
from config import ConfigManager
from web import WebAppWrapper


class TelegramBot:

    def __init__(self):
        self.bot = None
        self.cfg = None
        self.web = None
        self.plugins = dict()

    async def run(self, config: ConfigManager, token: str):
        self.cfg = config

        # Init bot
        self.bot = (
            Application.builder()
            .defaults(Defaults(parse_mode=ParseMode.HTML))
            .token(token)
            .build()
        )

        # Init webserver
        port = self.cfg.get('webserver', 'port')
        self.web = WebAppWrapper(port=port)

        # TODO: Add favicon
        # Add default root route
        self.web.add_endpoint('/', lambda: FileResponse(c.DIR_RES / 'root.html'))

        # Load all plugins
        await self.load_plugins()

        # Add handler for file downloads (plugin updates)
        logger.info("Setting up plugin updates...")
        self.bot.add_handler(
            MessageHandler(
                filters.Document.ZIP | filters.Document.FileExtension('py'),
                self._update_handler)
        )

        # Handle all Telegram related errors
        logger.info("Setting up error handling...")
        self.bot.add_error_handler(self._error_handler)

        try:
            # Notify admin about bot start
            await self.bot.updater.bot.send_message(
                chat_id=self.cfg.get('admin_tg_id'),
                text=f'{emo.ROBOT} Bot is up and running!'
            )
        except InvalidToken:
            logger.error('Invalid Telegram bot token')
            return

        # Start webserver
        if self.cfg.get('webserver', 'enabled'):
            logger.info("Setting up webserver...")
            self.web.start()

        # Start polling for updates
        self.bot.run_polling(drop_pending_updates=True)

    async def load_plugins(self):
        """ Load all plugins from the 'plugins' folder """

        try:
            for _, folders, _ in os.walk(c.DIR_PLG):
                for folder in folders:
                    if folder.startswith("_"):
                        continue
                    logger.info(f"Plugin '{folder}' loading...")
                    await self.enable_plugin(folder)
                break
        except Exception as e:
            logger.error(e)

    async def enable_plugin(self, name):
        """ Load a single plugin """

        # If already enabled, disable first
        await self.disable_plugin(name)

        try:
            module_path = f"{c.DIR_PLG}.{name}.{name}"
            module = importlib.import_module(module_path)

            async with getattr(module, name.capitalize())(self) as plugin:
                try:
                    self.plugins[name] = plugin
                    msg = f"Plugin '{name}' enabled"
                    logger.info(msg)
                    return True, msg
                except Exception as e:
                    msg = f"Plugin '{name}' initialization failed: {e}"
                    logger.error(msg)
                    return False, str(e)

        except Exception as e:
            msg = f"Plugin '{name}' can not be enabled: {e}"
            logger.error(msg)
            return False, str(e)

    async def disable_plugin(self, name):
        """ Remove a plugin from the plugin list and also
         remove all its handlers from the dispatcher """

        if name in self.plugins:
            plugin = self.plugins[name]

            try:
                # Run plugins own cleanup method
                await plugin.cleanup()
            except Exception as e:
                msg = f"Plugin '{plugin.name}' cleanup failed: {e}"
                logger.error(msg)
                return False, str(e)

            # Remove plugin handlers
            for handler in plugin.handlers:
                self.bot.remove_handler(handler)

            # Remove plugin endpoints
            for endpoint in plugin.endpoints:
                self.web.remove_endpoint(endpoint)

            # Remove plugin
            del plugin
            del self.plugins[name]

            msg = f"Plugin '{name}' disabled"
            logger.info(msg)
            return True, msg

    # FIXME: How to correctly replace already loaded plugin?
    async def _update_handler(self, update: Update, context: CallbackContext) -> None:
        """
        Update a plugin by uploading a file to the bot.

        If you provide a .ZIP file then the content will be extracted into
        the plugin with the same name as the file. For example the file
        'about.zip' will be extracted into the 'about' plugin folder.

        It's also possible to provide a .PY file. In this case the file will
        replace the plugin implementation with the same name. For example the
        file 'about.py' will replace the same file in the 'about' plugin.

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
                logger.warning(f"{emo.ERROR} Wrong file format for update")
                return

            file = await update.message.effective_attachment.get_file()

            if zipped:
                Path.mkdir(c.DIR_TMP, parents=True, exist_ok=True)
                zip_path = c.DIR_TMP / name

                await file.download_to_drive(zip_path)

                with ZipFile(zip_path, 'r') as zip_file:
                    the_path = Path(c.DIR_PLG / plugin_name)
                    zip_file.extractall(the_path)
            else:
                the_path = Path(c.DIR_PLG / plugin_name / name)
                await file.download_to_drive(the_path)

            await self.disable_plugin(plugin_name)
            await self.enable_plugin(plugin_name)

            shutil.rmtree(c.DIR_TMP, ignore_errors=True)

            await update.message.reply_text(f"{emo.DONE} Plugin successfully loaded")
        except Exception as e:
            logger.error(e)
            await update.message.reply_text(f"{emo.ERROR} {e}")

    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log the error and send a telegram message to notify the developer."""

        # Log the error before we do anything else, so we can see it even if something breaks.
        logger.error(f"Exception while handling an update: {context.error}")

        # traceback.format_exception returns the usual python message about an exception, but as a
        # list of strings rather than a single string, so we have to join them together.
        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = "".join(tb_list)

        logger.error(tb_string)

        # Build the message with some markup and additional information about what happened.
        # You might need to add some logic to deal with messages longer than the 4096-character limit.
        update_str = update.to_dict() if isinstance(update, Update) else str(update)
        message = (
            f"{emo.ALERT} An exception was raised while handling an update\n\n"
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
    # Load data from .env file
    load_dotenv()

    log_level = os.getenv('LOG_LEVEL') if os.getenv('LOG_LEVEL') else 'INFO'
    log_into_file = os.getenv('LOG_INTO_FILE') if os.getenv('LOG_INTO_FILE') else True

    logger.remove()

    logger.add(
        sys.stderr,
        level=log_level)

    if log_into_file:
        logger.add(
            Path(Path('log') / Path('{time}.log')),
            format="{time} {name} {message}",
            level=log_level,
            rotation="5 MB"
        )

    nest_asyncio.apply()  # FIXME: How to get rid of that?

    asyncio.run(TelegramBot().run(
        ConfigManager(c.DIR_CFG / c.FILE_CFG),
        os.getenv('TG_TOKEN'))
    )
