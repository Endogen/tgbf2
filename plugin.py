import os
import sqlite3
import inspect
import asyncio

import constants as c
import utils as utl

from pathlib import Path
from loguru import logger
from functools import wraps
from loguru._logger import Logger
from typing import Tuple, Dict, Callable
from telegram.constants import ChatAction
from telegram import Chat, Update, Message
from telegram.ext import CallbackContext, BaseHandler, Job
from datetime import datetime, timedelta
from config import ConfigManager
from main import TelegramBot


class TGBFPlugin:

    def __init__(self, tgb: TelegramBot):
        # Parent that instantiated this plugin
        self._tgb = tgb

        # Set default logger
        self._log = logger

        # Set class name as name of this plugin
        self._name = type(self).__name__.lower()

        # All bot handlers for this plugin
        self._handlers: Dict[int, BaseHandler] = dict()

        # All endpoints of this plugin
        self._endpoints: Dict[str, Callable] = dict()

        # Access to global config
        self._cfg_global = self._tgb.cfg

        # Access to plugin config
        self._cfg = ConfigManager(self.get_cfg_path() / self.get_cfg_name())

    async def __aenter__(self):
        """ Executes init() method. Make sure to return 'self' if you override it """
        await self.init()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """ This method gets executed after the plugin is loaded """
        pass

    async def init(self):
        method = inspect.currentframe().f_code.co_name
        raise NotImplementedError(f"Method '{method}' not implemented")

    async def cleanup(self):
        """ Overwrite this method if you want to clean something up
         before the plugin will be disabled """
        pass

    @property
    def tgb(self) -> TelegramBot:
        return self._tgb

    @property
    def log(self) -> Logger:
        return self._log

    @property
    def name(self) -> str:
        """ Return the name of the current plugin """
        return self._name

    @property
    def handle(self) -> str:
        """ Return the command string that triggers the plugin """
        handle = self.cfg.get("handle")
        return handle.lower() if handle else self.name

    @property
    def category(self) -> str:
        """ Return the category of the plugin for the 'help' command """
        return self.cfg.get("category")

    @property
    def description(self) -> str:
        """ Return the description of the plugin """
        return self.cfg.get("description")

    @property
    def plugins(self) -> Dict:
        """ Return a list of all active plugins """
        return self.tgb.plugins

    @property
    def jobs(self) -> Tuple[Job, ...]:
        """ Return a tuple with all currently active jobs """
        return self.tgb.bot.job_queue.jobs()

    @property
    def cfg_global(self) -> ConfigManager:
        """ Return the global configuration """
        return self._cfg_global

    @property
    def cfg(self) -> ConfigManager:
        """ Return the configuration for this plugin """
        return self._cfg

    @property
    def handlers(self) -> Dict[int, BaseHandler]:
        """ Return a list of bot handlers for this plugin """
        return self._handlers

    @property
    def endpoints(self) -> Dict[str, Callable]:
        """ Return a list of bot endpoints for this plugin """
        return self._endpoints

    async def add_handler(self, handler: BaseHandler, group: int = None):
        """ Will add bot handlers to this plugins list of handlers
         and also add them to the bot dispatcher """

        group = group if group else utl.md5(self.name, to_int=True)

        self.tgb.bot.add_handler(handler, group)
        self.handlers[group] = handler

        self.log.info(f"Plugin '{self.name}': {type(handler).__name__} added")

    async def remove_handler(self, handler: BaseHandler):
        """ Removed the given handler from the bot """

        for g, h in self.handlers.items():
            if h == handler:
                self.tgb.bot.remove_handler(h, g)
                del self.handlers[g]
                break

        self.log.info(f"Plugin '{self.name}': {type(handler).__name__} removed")

    async def add_endpoint(self, name: str, action):
        """ Adds a webserver endpoint """

        self.tgb.web.add_endpoint(name, action)
        self.endpoints[name] = action

        self.log.info(f"Plugin '{self.name}': Endpoint '{name}' added")

    async def remove_endpoint(self, name: str):
        """ Remove an existing endpoint from webserver """

        self.tgb.web.remove_endpoint(name)
        del self.endpoints[name]

        self.log.info(f"Plugin '{self.name}': Endpoint '{name}' removed")

    async def get_info(self, replace: dict = None):
        """
        Return info about the command. Default resource '<plugin>.txt'
        will be loaded from the resource folder and if you provide a
        dict with '<placeholder>,<value>' entries then placeholders in
        the resource will be replaced with the corresponding <value>.

        The placeholders need to be wrapped in double curly brackets
        """

        usage = await self.get_resource(f"{self.name}.txt")

        if usage:
            usage = usage.replace("{{handle}}", self.handle)

            if replace:
                for placeholder, value in replace.items():
                    usage = usage.replace(placeholder, str(value))

            return usage

        await self.notify(f'No usage info for plugin <b>{self.name}</b>')
        return f'{c.ERROR} Could not retrieve usage info'

    async def get_resource_global(self, filename):
        """ Return the content of the given file
        from the global resource directory """

        path = Path(Path.cwd() / c.DIR_RES / filename)
        return await self._get_resource_content(path)

    async def get_resource(self, filename, plugin=None):
        """ Return the content of the given file from
        the resource directory of the given plugin """

        path = os.path.join(self.get_res_path(plugin), filename)
        return await self._get_resource_content(path)

    async def _get_resource_content(self, path):
        """ Return the content of the file in the given path """

        try:
            with open(path, "r", encoding="utf8") as f:
                return f.read()
        except Exception as e:
            self.log.error(e)
            await self.notify(e)

    async def get_jobs(self, name=None) -> Tuple[Job, ...]:
        """ Return jobs with given name or all jobs if not name given """

        if name:
            # Get all jobs with given name
            return await self.tgb.bot.job_queue.get_jobs_by_name(name)
        else:
            # Return all jobs
            return await self.tgb.bot.job_queue.jobs()

    def run_repeating(self, callback, interval, first=0, last=None, data=None, name=None):
        """ Executes the provided callback function indefinitely.
        It will be executed every 'interval' (seconds) time. The
        created job will be returned by this method. If you want
        to stop the job, execute 'schedule_removal()' on it.

        The job will be added to the job queue and the default
        name of the job (if no 'name' provided) will be the name
        of the plugin plus some random data"""

        name = name if name else (self.name + "_" + utl.random_id())

        return self.tgb.bot.job_queue.run_repeating(
            callback,
            interval,
            first=first,
            last=last,
            data=data,
            name=name)

    def run_once(self, callback, when, data=None, name=None):
        """ Executes the provided callback function only one time.
        It will be executed at the provided 'when' time. The
        created job will be returned by this method. If you want
        to stop the job before it gets executed, execute
        'schedule_removal()' on it.

        The job will be added to the job queue and the default
        name of the job (if no 'name' provided) will be the name
        of the plugin """

        return self.tgb.bot.job_queue.run_once(
            callback,
            when,
            data=data,
            name=name if name else (self.name + "_" + utl.random_id()))

    async def exec_sql_global(self, sql, *args, db_name=""):
        """ Execute raw SQL statement on the global
        database and return the result

        param: sql = the SQL query
        param: *args = arguments for the SQL query
        param: db_name = name of the database file

        Following data will be returned
        If error happens:
        {"success": False, "data": None}

        If no data available:
        {"success": True, "data": None}

        If database disabled:
        {"success": False, "data": "Database disabled"} """

        if db_name:
            if not db_name.lower().endswith(".db"):
                db_name += ".db"
        else:
            db_name = c.FILE_DAT

        db_path = Path.cwd() / c.DIR_DAT / db_name
        return await self._exec_on_db(db_path, sql, *args)

    async def exec_sql(self, sql, *args, plugin="", db_name=""):
        """ Execute raw SQL statement on database for given
        plugin and return the result.

        param: sql = the SQL query
        param: *args = arguments for the SQL query
        param: plugin = name of plugin that DB belongs too
        param: db_name = name of DB in case it's not the
        default (the name of the plugin)

        Following data will be returned
        If error happens:
        {"success": False, "data": None}

        If no data available:
        {"success": True, "data": None}

        If database disabled:
        {"success": False, "data": "Database disabled"} """

        if db_name:
            if not db_name.lower().endswith(".db"):
                db_name += ".db"
        else:
            if plugin:
                db_name = plugin + ".db"
            else:
                db_name = self.name + ".db"

        plugin = plugin if plugin else self.name
        db_path = Path(self.get_dat_path(plugin=plugin) / db_name)

        return await self._exec_on_db(db_path, sql, *args)

    async def _exec_on_db(self, db_path, sql, *args):
        """ Open database connection and execute SQL statement """

        res = {"data": None, "success": None}

        try:
            # Create directory if it doesn't exist
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            res["data"] = str(e)
            res["success"] = False
            self.log.error(e)
            await self.notify(e)

        with sqlite3.connect(db_path, timeout=5) as con:
            try:
                cur = con.cursor()
                cur.execute(sql, args)
                con.commit()

                res["data"] = cur.fetchall()
                res["success"] = True

            except Exception as e:
                res["data"] = str(e)
                res["success"] = False
                self.log.error(e)
                await self.notify(e)

            return res

    async def table_exists_global(self, table_name, db_name="") -> bool:
        """ Return TRUE if given table exists in global database, otherwise FALSE """

        if db_name:
            if not db_name.lower().endswith(".db"):
                db_name += ".db"
        else:
            db_name = c.FILE_DAT

        db_path = Path(Path.cwd() / c.DIR_DAT / db_name)
        return await self._db_table_exists(db_path, table_name)

    async def table_exists(self, table_name, plugin=None, db_name=None) -> bool:
        """ Return TRUE if given table exists in given plugin, otherwise FALSE """

        if db_name:
            if not db_name.lower().endswith(".db"):
                db_name += ".db"
        else:
            if plugin:
                db_name = plugin + ".db"
            else:
                db_name = self.name + ".db"

        plugin = plugin if plugin else self.name
        db_path = Path(self.get_dat_path(plugin=plugin) / db_name)

        return await self._db_table_exists(db_path, table_name)

    async def _db_table_exists(self, db_path, table_name) -> bool:
        """ Open connection to database and check if given table exists """

        if not db_path.is_file():
            return False

        con = sqlite3.connect(db_path)
        cur = con.cursor()
        exists = False

        statement = await self.get_resource_global("table_exists.sql")

        try:
            if cur.execute(statement, [table_name]).fetchone():
                exists = True
        except Exception as e:
            self.log.error(e)
            await self.notify(e)

        con.close()
        return exists

    def get_res_path(self, plugin=None) -> Path:
        """ Return path of resource directory for given plugin """
        plugin = plugin if plugin else self.name
        return Path(c.DIR_PLG, plugin, c.DIR_RES)

    def get_cfg_path(self, plugin=None) -> Path:
        """ Return path of configuration directory for the given plugin """
        plugin = plugin if plugin else self.name
        return Path(c.DIR_PLG / plugin / c.DIR_CFG)

    def get_cfg_name(self, plugin=None) -> Path:
        """ Return name of configuration file for given plugin """
        plugin = plugin if plugin else self.name
        return Path(plugin).with_suffix(c.CFG_EXT)

    def get_dat_path(self, plugin=None) -> Path:
        """ Return path of data directory for given plugin """
        plugin = plugin if plugin else self.name
        return Path(c.DIR_PLG, plugin, c.DIR_DAT)

    def get_plg_path(self, plugin=None) -> Path:
        """ Return path of given plugin directory """
        plugin = plugin if plugin else self.name
        return Path(c.DIR_PLG, plugin)

    def get_plugin(self, plugin_name):
        """ Return the plugin with the given name """
        if plugin_name in self.plugins:
            return self.plugins[plugin_name]

    def is_enabled(self, plugin_name) -> bool:
        """ Return TRUE if the given plugin is enabled or FALSE otherwise """
        return plugin_name in self.plugins

    def is_private(self, message: Message) -> bool:
        """ Check if message was sent in a private chat or not """
        return message.chat.type == Chat.PRIVATE

    def remove_msg_after(self, *messages: Message, after_secs):
        """ Remove a Telegram message after a given time """

        async def remove_msg_job(context: CallbackContext):
            param_lst = str(context.job.data).split("_")
            chat_id = param_lst[0]
            msg_id = int(param_lst[1])

            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception as e:
                self.log.error(f"Not possible to remove message: {e}")

        for message in messages:
            self.run_once(
                remove_msg_job,
                datetime.utcnow() + timedelta(seconds=after_secs),
                data=f"{message.chat_id}_{message.message_id}")

    async def notify(self, msg: str | Exception) -> bool:
        """ Admin in global config will get a message with the given text.
         Primarily used for exceptions but can be used with other inputs too. """

        msg = repr(msg) if isinstance(msg, Exception) else msg

        admin = self.cfg_global.get('admin_tg_id')

        try:
            await self.tgb.bot.updater.bot.send_message(admin, f"{c.ALERT} {msg}")
        except Exception as e:
            error = f"Not possible to notify admin id '{admin}'"
            self.log.error(f"{error}: {e}")
            return False

        return True

    @classmethod
    def private(cls, func):
        """ Decorator for methods that need to be run in a private chat with the bot """

        @wraps(func)
        async def _private(self, update: Update, context: CallbackContext, **kwargs):
            if (await context.bot.get_chat(update.effective_chat.id)).type == Chat.PRIVATE:
                if asyncio.iscoroutinefunction(func):
                    return await func(self, update, context, **kwargs)
                else:
                    return func(self, update, context, **kwargs)

            if update.message:
                name = context.bot.username if context.bot.username else context.bot.name
                msg = f"{c.ERROR} Use this command in a chat with the bot @{name}"
                await update.message.reply_text(msg)

        return _private

    @classmethod
    def public(cls, func):
        """ Decorator for methods that need to be run in a public group """

        @wraps(func)
        async def _public(self, update: Update, context: CallbackContext, **kwargs):
            if (await context.bot.get_chat(update.effective_chat.id)).type != Chat.PRIVATE:
                if asyncio.iscoroutinefunction(func):
                    return await func(self, update, context, **kwargs)
                else:
                    return func(self, update, context, **kwargs)

            if update.message:
                msg = f"{c.ERROR} Can only be used in a public chat"
                await update.message.reply_text(msg)

        return _public

    @classmethod
    def owner(cls, func):
        """
        Decorator that executes the method only if the user is a bot admin.

        The user ID that triggered the command has to be in the ["admin"]["ids"]
        list of the global config file 'global.cfg' or in the ["admins"] list
        of the currently used plugin config file.
        """

        @wraps(func)
        async def _owner(self, update: Update, context: CallbackContext, **kwargs):
            user_id = update.effective_user.id

            plg_admins = self.cfg.get("admins")
            plg_admins = plg_admins if isinstance(plg_admins, list) else []

            global_admin = self.cfg_global.get("admin_tg_id")

            if user_id in plg_admins or user_id == global_admin:
                if asyncio.iscoroutinefunction(func):
                    return await func(self, update, context, **kwargs)
                else:
                    return func(self, update, context, **kwargs)

        return _owner

    @classmethod
    def dependency(cls, func):
        """ Decorator that executes a method only if the mentioned
        plugins in the config file of the current plugin are enabled """

        @wraps(func)
        async def _dependency(self, update: Update, context: CallbackContext, **kwargs):
            dependencies = self.cfg.get("dependency")
            dependencies = dependencies if isinstance(dependencies, list) else []

            for dependency in dependencies:
                if dependency.lower() not in self.plugins:
                    msg = f"{c.ERROR} Plugin '{self.name}' is missing dependency '{dependency}'"
                    await update.message.reply_text(msg)
                    return

            if asyncio.iscoroutinefunction(func):
                return await func(self, update, context, **kwargs)
            else:
                return func(self, update, context, **kwargs)

        return _dependency

    @classmethod
    def send_typing(cls, func):
        """ Decorator for sending typing notification in the Telegram chat """

        @wraps(func)
        async def _send_typing(self, update, context, **kwargs):
            # Make sure that edited messages will not trigger any functionality
            if not update.edited_message:
                try:
                    await context.bot.send_chat_action(
                        chat_id=update.effective_chat.id,
                        action=ChatAction.TYPING)
                except:
                    pass

            if asyncio.iscoroutinefunction(func):
                return await func(self, update, context, **kwargs)
            else:
                return func(self, update, context, **kwargs)

        return _send_typing

    @classmethod
    def blacklist(cls, func):
        """ Decorator to check whether a command can be executed in the given
         chat or not. If the current chat ID is part of the 'blacklist' list
         in the plugins config file then the command will not be executed. """

        @wraps(func)
        async def _blacklist(self, update: Update, context: CallbackContext, **kwargs):
            blacklist_chats = self.cfg.get("blacklist")

            try:
                if blacklist_chats and (update.effective_chat.id not in blacklist_chats):
                    if asyncio.iscoroutinefunction(func):
                        return await func(self, update, context, **kwargs)
                    else:
                        return func(self, update, context, **kwargs)
            except:
                pass

            name = context.bot.username if context.bot.username else context.bot.name
            msg = self.cfg.get("blacklist_msg").replace("{{name}}", name)
            await update.message.reply_text(msg, disable_web_page_preview=True)

        return _blacklist

    @classmethod
    def whitelist(cls, func):
        """ Decorator to check whether a command can be executed in the given
         chat or not. If the current chat ID is part of the 'whitelist' list
         in the plugins config file then the command will be executed. """

        @wraps(func)
        async def _whitelist(self, update: Update, context: CallbackContext, **kwargs):
            whitelist_chats = self.cfg.get("whitelist")

            try:
                if whitelist_chats and (update.effective_chat.id in whitelist_chats):
                    if asyncio.iscoroutinefunction(func):
                        return await func(self, update, context, **kwargs)
                    else:
                        return func(self, update, context, **kwargs)
            except:
                pass

            name = context.bot.username if context.bot.username else context.bot.name
            msg = self.cfg.get("whitelist_msg").replace("{{name}}", name)
            await update.message.reply_text(msg, disable_web_page_preview=True)

        return _whitelist
