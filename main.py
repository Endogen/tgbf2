import os
import sys
import asyncio
import importlib
import nest_asyncio
import constants as con

from pathlib import Path
from loguru import logger
from dotenv import load_dotenv
from telegram.error import InvalidToken
from telegram.constants import ParseMode
from telegram.ext import Application, Defaults
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
        self.web = WebAppWrapper(
            res_path=con.DIR_RES,
            port=self.cfg.get('webserver', 'port')
        )

        # Load all plugins
        await self.load_plugins()

        try:
            # Notify admin about bot start
            await self.bot.updater.bot.send_message(
                chat_id=self.cfg.get('admin_tg_id'),
                text=f'{con.ROBOT} Bot is up and running!'
            )
        except InvalidToken:
            logger.error('Invalid Telegram bot token')
            return

        # Start webserver
        if self.cfg.get('webserver', 'enabled'):
            logger.info("Setting up webserver...")
            self.web.start()

        # Start polling for updates
        logger.info("Setting up polling for updates...")
        self.bot.run_polling(drop_pending_updates=True)

    async def load_plugins(self):
        """ Load all plugins from the 'plg' folder """

        try:
            for _, folders, _ in os.walk(con.DIR_PLG):
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
            module_path = f"{con.DIR_PLG}.{name}.{name}"
            module = importlib.import_module(module_path)

            importlib.reload(module)

            async with getattr(module, name.capitalize())(self) as plugin:
                self.plugins[name] = plugin
                msg = f"Plugin '{name}' enabled"
                logger.info(msg)
                return True, msg

        except Exception as e:
            msg = f"Plugin '{name}' can not be enabled: {e}"
            logger.error(msg)
            return False, str(e)

    async def disable_plugin(self, name):
        """ Remove a plugin from the plugin list and also
         remove all its handlers and endpoints """

        if name in self.plugins:
            plugin = self.plugins[name]

            # Run plugin's own cleanup method
            await plugin.cleanup()

            # Remove plugin handlers
            for group, handler in plugin.handlers.items():
                self.bot.remove_handler(handler, group)
            plugin.handlers.clear()

            # Remove plugin endpoints
            for endpoint in plugin.endpoints:
                self.web.remove_endpoint(endpoint)
            plugin.endpoints.clear()

            # Remove all plugin references
            del sys.modules[f"{con.DIR_PLG}.{name}.{name}"]
            del sys.modules[f"{con.DIR_PLG}.{name}"]
            del self.plugins[name]
            del plugin

            msg = f"Plugin '{name}' disabled"
            logger.info(msg)
            return True, msg


if __name__ == "__main__":
    # Load data from .env file
    load_dotenv()

    # Read parameters from .env file
    log_level = os.getenv('LOG_LEVEL') if os.getenv('LOG_LEVEL') else 'INFO'
    log_into_file = os.getenv('LOG_INTO_FILE') if os.getenv('LOG_INTO_FILE') else True

    # Remove standard logger
    logger.remove()

    # Add new loguru logger
    logger.add(
        sys.stderr,
        level=log_level)

    # Save log in file
    if log_into_file:
        logger.add(
            Path(Path('log') / Path('{time}.log')),
            format="{time} {name} {message}",
            level=log_level,
            rotation="5 MB"
        )

    nest_asyncio.apply()

    asyncio.run(TelegramBot().run(
        ConfigManager(con.DIR_CFG / con.FILE_CFG),
        os.getenv('TG_TOKEN'))
    )
