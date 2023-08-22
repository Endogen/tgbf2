# TGBF2 - Telegram Bot Framework V2

TGBF2 is a framework to build Telegram bots based on the Python module [`python-telegram-bot`](https://github.com/python-telegram-bot/python-telegram-bot). That module is already easy to use but once you built more than one bot you will find yourself doing things over and over again and instead of copying things over all the time, it makes more sens to use a framework like this one that can handle certain things for you so that you can focus on implementing the main logic for bot commands.    

The following concepts help TGBF2 to achieve this
- Plugin system
  - Everything you can do with the `python-telegram-bot` module you can do here too with a plugin (Python file) that will be loaded on startup. These Plugins can also be enabled / disabled while the bot is running. Read more about plugins [here](plg/README.md).
- FastAPI integration
  - Each plugin can set up endpoints that can be enabled / disabled on the fly
- JSON config files
  - A plugin can have one or more config files that 
- SQLite integration
  - ...
- Logging into file with file rotation
- Decorators to handle common tasks like
  - Typing notification on command execution
  - Commands only for private / public /owner use
  - Blacklists and Whitelists for command executions
- Global data that all plugins can access
- Existing plugins for
  - Error handling
  - Backups (whole bot or single plugins)
  - Bot restart
  - Bot shutdown
  - Admin command to enable / disable plugins
  - Tracking of posted user messages 

- Explain core concepts
  - Plugins - link to README in plg folder
- Remove DB plugin and instead create how-to where the details are mentioned
- If plugin 'debug' is not being used then no need to install 'psutil' module
- Default parse mode is HTML

## Enable webserver
- In global config file `cfg/globla.cfg`  set `webserver - enabled` to `true`
- In a plugin you can add following to enable a new route: `self.add_endpoint('/about', self.action)`
  - Will require method `action()` too

## .env file
- hidden file in main bot directory
- contains parameters that plugins don't need to access (also sensitive data)
- Parameters
  - `TG_TOKEN` = Telegram bot token (get it from https://t.me/BotFather)
  - `LOG_LEVEL` = DEBUG, INFO, WARNING, ERROR
  - `LOG_INTO_FILE` = `true` or `false`. Saved logs into `log` folder

## Plugin config file
- In folder `cfg`
- Accessible by plugins
- Possible settings
  - handle, dependency [], admins [], description, category, blacklist, blacklist_msg, whitelist, whitelist_msg

## Global config file
- In folder `cfg`
- Accessible by plugins
- It's a JSON file (despite the .cfg extension)
- Following parameters are possible
  - `admin_tg_id` = Telegram user ID of bot admin (check ID by sending message https://t.me/getidsbot)
  - `webserver - enabled` = Enable or disable webserver
  - `webserver - port` = Webserver port

## Download bot
- `git clone https://github.com/Endogen/tgbf2.git`

## Update bot
- Stop bot first with `pm2 stop [ID]`
- `git reset --hard origin/main`
- `git pull origin main`

## How to install `poetry`
TODO

## Run in background
- `screen -S tgbf2`
- start with `poetry run python main.py`
- go back to your screen with `screen -r tgbf2`

## Run with PM2 (ecosystem file)
- adjusting interpreter path
- pm2 start `pm2.config.json`

TODO: Check README content with AI and adjust texts