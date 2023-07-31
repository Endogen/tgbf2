- Explain core concepts
- Remove DB plugin and instead create how-to where the details are mentioned
- If plugin 'debug' is not being used then no need to install 'psutil' module


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
- start with `poetry run python run.py`
- go back to your screen with `screen -r tgbf2`

## Run with PM2 (ecosystem file)
- adjusting interpreter path
- pm2 start `pm2.config.json`