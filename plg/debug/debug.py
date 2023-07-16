import os
import sys
import psutil
import logging
import platform
import utils as utl

from plugin import TGBFPlugin
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler


class Debug(TGBFPlugin):

    async def init(self):
        await self.add_handler(CommandHandler(self.handle, self.init_callback, block=False))

    @TGBFPlugin.owner
    @TGBFPlugin.send_typing
    async def init_callback(self, update: Update, context: CallbackContext):
        try:
            await update.message.delete()
        except:
            pass

        vi = sys.version_info
        v = f"{vi.major}.{vi.minor}.{vi.micro}"

        msg = f"PID: {os.getpid()}\n" \
              f"Python: {v}\n" \
              f"Open files: {len(psutil.Process().open_files())}\n" \
              f"IP: {utl.get_external_ip()}\n" \
              f"Network: {platform.node()}\n" \
              f"Machine: {platform.machine()}\n" \
              f"Processor: {platform.processor()}\n" \
              f"Platform: {platform.platform()}\n" \
              f"OS: {platform.system()}\n" \
              f"OS Release: {platform.release()}\n" \
              f"OS Version: {platform.version()}\n" \
              f"CPU Physical Cores: {psutil.cpu_count(logical=False)}\n" \
              f"CPU Logical Cores: {psutil.cpu_count(logical=True)}\n" \
              f"Current CPU Frequency: {psutil.cpu_freq().current}\n" \
              f"Min CPU Frequency: {psutil.cpu_freq().min}\n" \
              f"Max CPU Frequency: {psutil.cpu_freq().max}\n" \
              f"CPU Utilization: {psutil.cpu_percent(interval=1)}\n" \
              f"Per-CPU Utilization: {psutil.cpu_percent(interval=1, percpu=True)}\n" \
              f"Total RAM: {round(psutil.virtual_memory().total/1000000000, 2)} GB\n" \
              f"Available RAM: {round(psutil.virtual_memory().available/1000000000, 2)} GB\n" \
              f"Used RAM: {round(psutil.virtual_memory().used/1000000000, 2)} GB\n" \
              f"RAM Usage: {psutil.virtual_memory().percent}%"

        if self.is_private(update.message):
            await update.message.reply_text(msg)
        else:
            try:
                await self.tgb.app.bot.updater.bot.send_message(
                    update.effective_user.id,
                    f"{msg}\n\n{update.effective_chat}")
            except Exception as e:
                logging.error(f"Could not send debug info: {e}")
