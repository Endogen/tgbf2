import asyncio
import sys
import os
import json
import shutil
import importlib
import traceback
import nest_asyncio
import emoji as emo
import utils as utl
import constants as con

from loguru import logger
from dotenv import load_dotenv
from zipfile import ZipFile
from importlib import reload
from telegram import Chat, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, Application, Defaults, CommandHandler


class TelegramBot:

    def __init__(self):
        self.app = None
        self.plugins = list()

    async def run(self):
        self.app = (
            Application.builder()
            .token(os.getenv('TG_TOKEN'))
            .defaults(Defaults(parse_mode=ParseMode.HTML))
            .build()
        )

        await self.load_plugins()
        self.app.run_polling()

    async def load_plugins(self):
        """ Load all plugins from the 'plugins' folder """
        try:
            for _, folders, _ in os.walk(con.DIR_PLG):
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
            module_path = f"{con.DIR_PLG}.{module_name}.{module_name}"
            module = importlib.import_module(module_path)

            #reload(module)

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
