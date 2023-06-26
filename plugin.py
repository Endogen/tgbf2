import os
import hashlib
import sqlite3
import inspect

import asyncio
from functools import wraps

from enum import Enum
from telegram.constants import ChatAction

import constants as c
import emoji as emo
import utils as utl

from pathlib import Path
from loguru import logger
from typing import List, Tuple
from telegram import Chat, Update, Message
from telegram.ext import CallbackContext, CallbackQueryHandler, ConversationHandler, BaseHandler
from datetime import datetime, timedelta

from run import TelegramBot


class TGBFPlugin:

    def __init__(self, tgb: TelegramBot):
        self._tgb = tgb

        # Set class name as name of this plugin
        self._name = type(self).__name__.lower()

        # All bot handlers for this plugin
        self._handlers: List[BaseHandler] = list()

        # Access to global config
        #self._global_config = self._bot.config

        # Access to plugin config
        #self._config = self.get_cfg_manager()

        # All web endpoints for this plugin
        #self._endpoints: Dict[str, EndpointAction] = dict()

        # # Create global db table for wallets
        # if not self.global_table_exists("wallets"):
        #     sql = self.get_global_resource("create_wallets.sql")
        #     self.execute_global_sql(sql)

    async def __aenter__(self):
        """ This method gets executed after __init__() but before
        load(). Make sure to return 'self' if you override it """
        await self.init()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """ This method gets executed after __init__() and after load() """
        pass

    async def init(self):
        method = inspect.currentframe().f_code.co_name
        msg = f"Method '{method}' of plugin '{self.name}' not implemented"
        logger.warning(msg)

    def callback_cfg_change(self, value, *keys):
        """ Overwrite this method if you need some logic to be executed
         after the plugin configuration changed """
        pass

    # def get_cfg_manager(self, plugin: str = None, on_change: Callable = None, pass_args=True) -> ConfigManager:
    #     """ Returns a plugin configuration. If the config file
    #     doesn't exist then it will be created.
    #
    #     If you don't provide 'plugin' and 'on_change' then the
    #     default callback_cfg_change() will be used as callback
    #     method that will be triggered on changes in the file.
    #
    #     If 'pass_args' is True then the settings-change context
    #     (what has changed, key and value) will be passed to the
    #     callback method. If False then nothing will be passed. """
    #
    #     if plugin:
    #         cfg_file = plugin.lower() + ".json"
    #         cfg_fold = os.path.join(self.get_cfg_path(plugin=plugin))
    #     else:
    #         cfg_file = f"{self.name}.json"
    #         cfg_fold = os.path.join(self.get_cfg_path())
    #
    #         on_change = on_change if on_change else self.callback_cfg_change
    #
    #     cfg_path = os.path.join(cfg_fold, cfg_file)
    #
    #     # Create config directory if it doesn't exist
    #     os.makedirs(cfg_fold, exist_ok=True)
    #
    #     # Create config file if it doesn't exist
    #     if not os.path.isfile(cfg_path):
    #         with open(cfg_path, 'w') as file:
    #             # Make it a valid JSON file
    #             file.write("{}")
    #
    #     # Return plugin config
    #     return ConfigManager(
    #         cfg_path,
    #         callback=on_change,
    #         callback_pass_args=pass_args)

    @property
    def tgb(self) -> TelegramBot:
        return self._tgb

    @property
    def name(self) -> str:
        """ Return the name of the current plugin """
        return self._name

    @property
    def handle(self) -> str:
        """ Return the command string that triggers the plugin """
        handle = self.config.get("handle")
        return handle.lower() if handle else self.name

    @property
    def category(self) -> str:
        """ Return the category of the plugin for the 'help' command """
        return self.config.get("category")

    @property
    def description(self) -> str:
        """ Return the description of the plugin """
        return self.config.get("description")

    @property
    def plugins(self) -> List:
        """ Return a list of all active plugins """
        return self.tgb.plugins

    @property
    def jobs(self) -> Tuple:
        """ Return a tuple with all currently active jobs """
        return self.tgb.app.job_queue.jobs()

    # @property
    # def global_config(self) -> ConfigManager:
    #     """ Return the global configuration """
    #     return self._global_config

    # @property
    # def config(self) -> ConfigManager:
    #     """ Return the configuration for this plugin """
    #     return self._config

    @property
    def handlers(self) -> List[BaseHandler]:
        """ Return a list of bot handlers for this plugin """
        return self._handlers

    # @property
    # def endpoints(self) -> Dict[str, EndpointAction]:
    #     """ Return a dictionary with key = endpoint name and
    #     value = EndpointAction for this plugin """
    #     return self._endpoints

    async def add_handler(self, handler: BaseHandler, group: int = None):
        """ Will add bot handlers to this plugins list of handlers
         and also add them to the bot dispatcher """

        # TODO: Is this workaround still needed?
        if not group:
            """
            Make sure that all CallbackQueryHandlers are in their own
            group so that ALL CallbackQueryHandler callbacks get triggered.
            But that means that we need to make sure that only the right
            one gets executed! This is a workaround due to not knowing
            how to call only the 'right' callback function.
            """
            if isinstance(handler, (CallbackQueryHandler, ConversationHandler)):
                group = int(hashlib.md5(self.name.encode("utf-8")).hexdigest(), 16)
            else:
                group = 0

        self.tgb.app.add_handler(handler, group)
        self.handlers.append(handler)

        logger.info(f"Plugin '{self.name}': {type(handler).__name__} added")

    # def add_endpoint(self, name, endpoint: EndpointAction):
    #     """ Will add web endpoints (Flask) to this plugins list of
    #      endpoints and also add them to the Flask app """
    #
    #     name = name if name.startswith("/") else "/" + name
    #     self.bot.web.app.add_url_rule(name, name, endpoint)
    #     self.endpoints[name] = endpoint
    #
    #     logger.info(f"Plugin '{self.name}': Endpoint '{name}' added")

    def get_usage(self, replace: dict = None):
        """ Return how to use a command. Default resource '<plugin>.md'
         will be loaded from the resource folder and if you provide a
         dict with '<placeholder>,<value>' entries then placeholders in
         the resource will be replaced with the corresponding <value> """

        usage = self.get_resource(f"{self.name}.md")

        if usage:
            usage = usage.replace("{{handle}}", self.handle)

            if replace:
                for placeholder, value in replace.items():
                    usage = usage.replace(placeholder, str(value))

            return usage

        return None

    def get_global_resource(self, filename):
        """ Return the content of the given file
        from the global resource directory """

        path = os.path.join(os.getcwd(), c.DIR_RES, filename)
        return self._get_resource_content(path)

    def get_resource(self, filename, plugin=None):
        """ Return the content of the given file from
        the resource directory of the given plugin """

        path = os.path.join(self.get_res_path(plugin), filename)
        return self._get_resource_content(path)

    def _get_resource_content(self, path):
        """ Return the content of the file in the given path """

        try:
            with open(path, "r", encoding="utf8") as f:
                return f.read()
        except Exception as e:
            logger.error(e)
            self.notify(e)
            return None

    def get_jobs(self, name=None) -> Tuple['Job[CCT]', ...]:
        """ Return jobs with given name or all jobs if not name given """

        if name:
            # Get all jobs with given name
            return self.tgb.app.job_queue.get_jobs_by_name(name)
        else:
            # Return all jobs
            return self.tgb.app.job_queue.jobs()

    def run_repeating(self, callback, interval, first=0, last=None, data=None, name=None):
        """ Executes the provided callback function indefinitely.
        It will be executed every 'interval' (seconds) time. The
        created job will be returned by this method. If you want
        to stop the job, execute 'schedule_removal()' on it.

        The job will be added to the job queue and the default
        name of the job (if no 'name' provided) will be the name
        of the plugin plus some random data"""

        return self.tgb.app.job_queue.run_repeating(
            callback,
            interval,
            first=first,
            last=last,
            data=data,
            name=name if name else (self.name + "_" + utl.id()))

    def run_once(self, callback, when, data=None, name=None):
        """ Executes the provided callback function only one time.
        It will be executed at the provided 'when' time. The
        created job will be returned by this method. If you want
        to stop the job before it gets executed, execute
        'schedule_removal()' on it.

        The job will be added to the job queue and the default
        name of the job (if no 'name' provided) will be the name
        of the plugin """

        return self.tgb.app.job_queue.run_once(
            callback,
            when,
            data=data,
            name=name if name else (self.name + "_" + utl.id()))

    # def execute_global_sql(self, sql, *args, db_name=""):
    #     """ Execute raw SQL statement on the global
    #     database and return the result
    #
    #     param: sql = the SQL query
    #     param: *args = arguments for the SQL query
    #     param: db_name = name of the database file
    #
    #     Following data will be returned
    #     If error happens:
    #     {"success": False, "data": None}
    #
    #     If no data available:
    #     {"success": True, "data": None}
    #
    #     If database disabled:
    #     {"success": False, "data": "Database disabled"} """
    #
    #     if db_name:
    #         if not db_name.lower().endswith(".db"):
    #             db_name += ".db"
    #     else:
    #         db_name = c.FILE_DAT
    #
    #     db_path = os.path.join(os.getcwd(), c.DIR_DAT, db_name)
    #     return self._get_database_content(db_path, sql, *args)

    # def execute_sql(self, sql, *args, plugin="", db_name=""):
    #     """ Execute raw SQL statement on database for given
    #     plugin and return the result.
    #
    #     param: sql = the SQL query
    #     param: *args = arguments for the SQL query
    #     param: plugin = name of plugin that DB belongs too
    #     param: db_name = name of DB in case it's not the
    #     default (the name of the plugin)
    #
    #     Following data will be returned
    #     If error happens:
    #     {"success": False, "data": None}
    #
    #     If no data available:
    #     {"success": True, "data": None}
    #
    #     If database disabled:
    #     {"success": False, "data": "Database disabled"} """
    #
    #     if db_name:
    #         if not db_name.lower().endswith(".db"):
    #             db_name += ".db"
    #     else:
    #         if plugin:
    #             db_name = plugin + ".db"
    #         else:
    #             db_name = self.name + ".db"
    #
    #     if plugin:
    #         plugin = plugin.lower()
    #         data_path = self.get_dat_path(plugin=plugin)
    #         db_path = os.path.join(data_path, db_name)
    #     else:
    #         db_path = os.path.join(self.get_dat_path(), db_name)
    #
    #     return self._get_database_content(db_path, sql, *args)

    # TODO: Weird name since it's not always only getting but also setting values
    # def _get_database_content(self, db_path, sql, *args):
    #     """ Open database connection and execute SQL statement """
    #
    #     res = {"success": None, "data": None}
    #
    #     # Check if database usage is enabled
    #     if not self.global_config.get("database", "use_db"):
    #         res["data"] = "Database disabled"
    #         res["success"] = False
    #         return res
    #
    #     timeout = self.global_config.get("database", "timeout")
    #     db_timeout = timeout if timeout else 5
    #
    #     try:
    #         # Create directory if it doesn't exist
    #         directory = os.path.dirname(db_path)
    #         os.makedirs(directory, exist_ok=True)
    #     except Exception as e:
    #         res["data"] = str(e)
    #         res["success"] = False
    #         logger.error(e)
    #         self.notify(e)
    #
    #     with sqlite3.connect(db_path, timeout=db_timeout) as con:
    #         try:
    #             cur = con.cursor()
    #             cur.execute(sql, args)
    #             con.commit()
    #
    #             res["data"] = cur.fetchall()
    #             res["success"] = True
    #
    #         except Exception as e:
    #             res["data"] = str(e)
    #             res["success"] = False
    #             logger.error(e)
    #             self.notify(e)
    #
    #         return res

    # def global_table_exists(self, table_name, db_name=""):
    #     """ Return TRUE if given table exists in global database, otherwise FALSE """
    #
    #     if db_name:
    #         if not db_name.lower().endswith(".db"):
    #             db_name += ".db"
    #     else:
    #         db_name = c.FILE_DAT
    #
    #     db_path = os.path.join(os.getcwd(), c.DIR_DAT, db_name)
    #     return self._database_table_exists(db_path, table_name)

    # def table_exists(self, table_name, plugin=None, db_name=None):
    #     """ Return TRUE if given table existsin given plugin, otherwise FALSE """
    #
    #     if db_name:
    #         if not db_name.lower().endswith(".db"):
    #             db_name += ".db"
    #     else:
    #         if plugin:
    #             db_name = plugin + ".db"
    #         else:
    #             db_name = self.name + ".db"
    #
    #     if plugin:
    #         db_path = os.path.join(self.get_dat_path(plugin=plugin), db_name)
    #     else:
    #         db_path = os.path.join(self.get_dat_path(), db_name)
    #
    #     return self._database_table_exists(db_path, table_name)

    # def _database_table_exists(self, db_path, table_name):
    #     """ Open connection to database and check if given table exists """
    #
    #     if not Path(db_path).is_file():
    #         return False
    #
    #     con = sqlite3.connect(db_path)
    #     cur = con.cursor()
    #     exists = False
    #
    #     statement = self.get_global_resource("table_exists.sql")
    #
    #     try:
    #         if cur.execute(statement, [table_name]).fetchone():
    #             exists = True
    #     except Exception as e:
    #         logger.error(e)
    #         self.notify(e)
    #
    #     con.close()
    #     return exists

    def get_res_path(self, plugin=None):
        """ Return path of resource directory for this plugin """
        if not plugin:
            plugin = self.name
        return os.path.join(c.DIR_PLG, plugin, c.DIR_RES)

    def get_cfg_path(self, plugin=None):
        """ Return path of configuration directory for this plugin """
        if not plugin:
            plugin = self.name
        return os.path.join(c.DIR_PLG, plugin, c.DIR_CFG)

    def get_dat_path(self, plugin=None):
        """ Return path of data directory for this plugin """
        if not plugin:
            plugin = self.name
        return os.path.join(c.DIR_PLG, plugin, c.DIR_DAT)

    def get_plg_path(self, plugin=None):
        """ Return path of current plugin directory """
        if not plugin:
            plugin = self.name
        return os.path.join(c.DIR_PLG, plugin)

    def get_plugin(self, name):
        for plugin in self.plugins:
            if plugin.name == name:
                return plugin

    def is_enabled(self, plugin_name):
        """ Return TRUE if the given plugin is enabled or FALSE otherwise """
        for plugin in self.plugins:
            if plugin.name == plugin_name.lower():
                return True
        return False

    def is_private(self, message: Message):
        """ Check if message was sent in a private chat or not """
        return self.tgb.app.updater.bot.get_chat(message.chat_id).type == Chat.PRIVATE

    async def remove_msg_after(self, message: Message, after_secs):
        """ Remove a Telegram message after a given time """

        async def remove_msg_job(context: CallbackContext):
            param_lst = str(context.job.data).split("_")
            chat_id = param_lst[0]
            msg_id = int(param_lst[1])

            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception as e:
                logger.error(f"Not possible to remove message: {e}")

        self.run_once(
            remove_msg_job,
            datetime.utcnow() + timedelta(seconds=after_secs),
            data=f"{message.chat_id}_{message.message_id}")

    # TODO: Set correct admin ID
    async def notify(self, some_input):
        """ All admins in global config will get a message with the given text.
         Primarily used for exceptions but can be used with other inputs too. """

        if isinstance(some_input, Exception):
            some_input = repr(some_input)

        try:
            await self.tgb.app.updater.bot.send_message(134166731, f"{emo.ALERT} {some_input}")
        except Exception as e:
            error = f"Not possible to notify admin id '{134166731}'"
            logger.error(f"{error}: {e}")
            return False

        return True

    @classmethod
    def private(cls, func):
        """ Decorator for methods that need to be run in a private chat with the bot """

        def _private(self, update: Update, context: CallbackContext, **kwargs):
            if self.config.get("private") == False:
                return func(self, update, context, **kwargs)
            if context.bot.get_chat(update.effective_chat.id).type == Chat.PRIVATE:
                return func(self, update, context, **kwargs)

            if update.message:
                name = context.bot.username if context.bot.username else context.bot.name
                msg = f"{emo.ERROR} DM the bot @{name} to use this command"
                update.message.reply_text(msg)

        return _private

    @classmethod
    def public(cls, func):
        """ Decorator for methods that need to be run in a public group """

        def _public(self, update: Update, context: CallbackContext, **kwargs):
            if self.config.get("public") == False:
                return func(self, update, context, **kwargs)
            if context.bot.get_chat(update.effective_chat.id).type != Chat.PRIVATE:
                return func(self, update, context, **kwargs)

            if update.message:
                msg = f"{emo.ERROR} Can only be used in a public chat"
                update.message.reply_text(msg)

        return _public

    @classmethod
    def owner(cls, func):
        """
        Decorator that executes the method only if the user is an bot admin.

        The user ID that triggered the command has to be in the ["admin"]["ids"]
        list of the global config file 'config.json' or in the ["admins"] list
        of the currently used plugin config file.
        """

        def _owner(self, update: Update, context: CallbackContext, **kwargs):
            if self.config.get("owner") == False:
                return func(self, update, context, **kwargs)

            user_id = update.effective_user.id

            admins_global = self.global_config.get("admin", "ids")
            if admins_global and isinstance(admins_global, list):
                if user_id in admins_global:
                    return func(self, update, context, **kwargs)

            admins_plugin = self.config.get("admins")
            if admins_plugin and isinstance(admins_plugin, list):
                if user_id in admins_plugin:
                    return func(self, update, context, **kwargs)

        return _owner

    @classmethod
    def dependency(cls, func):
        """ Decorator that executes a method only if the mentioned
        plugins in the config file of the current plugin are enabled """

        def _dependency(self, update: Update, context: CallbackContext, **kwargs):
            dependencies = self.config.get("dependency")

            if dependencies and isinstance(dependencies, list):
                plugin_names = [p.name for p in self.plugins]

                for dependency in dependencies:
                    if dependency.lower() not in plugin_names:
                        msg = f"{emo.ERROR} Plugin '{self.name}' is missing dependency '{dependency}'"
                        update.message.reply_text(msg)
                        return
            else:
                logger.error(f"Dependencies for plugin '{self.name}' not defined as list")

            return func(self, update, context, **kwargs)
        return _dependency

    @classmethod
    def send_typing(cls, func):
        """ Decorator for sending typing notification in the Telegram chat """

        @wraps(func)
        async def _send_typing(self, update, context, **kwargs):
            # Make sure that edited messages will not trigger any functionality
            if update.edited_message:
                return

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
        def _blacklist(self, update: Update, context: CallbackContext, **kwargs):
            blacklist_chats = self.config.get("blacklist")

            try:
                if blacklist_chats and (update.effective_chat.id in blacklist_chats):
                    name = context.bot.username if context.bot.username else context.bot.name
                    msg = self.config.get("blacklist_msg").replace("{{name}}", name)  # TODO: Rework
                    await update.message.reply_text(msg, disable_web_page_preview=True)
            except:
                pass

            if asyncio.iscoroutinefunction(func):
                return await func(self, update, context, **kwargs)
            else:
                return func(self, update, context, **kwargs)

        return _blacklist

    @classmethod
    def whitelist(cls, func):
        """ Decorator to check whether a command can be executed in the given
         chat or not. If the current chat ID is part of the 'whitelist' list
         in the plugins config file then the command will be executed. """

        @wraps(func)
        def _whitelist(self, update: Update, context: CallbackContext, **kwargs):
            whitelist_chats = self.config.get("whitelist")

            try:
                if whitelist_chats and (update.effective_chat.id in whitelist_chats):
                    return func(self, update, context, **kwargs)
                else:
                    name = context.bot.username if context.bot.username else context.bot.name
                    msg = self.config.get("whitelist_msg").replace("{{name}}", name)  # TODO: Rework
                    await update.message.reply_text(msg, disable_web_page_preview=True)
            except:
                pass

            if asyncio.iscoroutinefunction(func):
                return await func(self, update, context, **kwargs)
            else:
                return func(self, update, context, **kwargs)

        return _whitelist
