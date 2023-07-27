import os
import sys
import psutil
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

            vi = sys.version_info
            v = f"{vi.major}.{vi.minor}.{vi.micro}"

            msg = f"PID: <code>{os.getpid()}</code>\n" \
                  f"Python: <code>{v}</code>\n" \
                  f"Open files: <code>{len(psutil.Process().open_files())}</code>\n" \
                  f"IP: <code>{utl.get_external_ip()}</code>\n" \
                  f"Network: <code>{platform.node()}</code>\n" \
                  f"Machine: <code>{platform.machine()}</code>\n" \
                  f"Processor: <code>{platform.processor()}</code>\n" \
                  f"Platform: <code>{platform.platform()}</code>\n" \
                  f"OS: <code>{platform.system()}</code>\n" \
                  f"OS Release: <code>{platform.release()}</code>\n" \
                  f"OS Version: <code>{platform.version()}</code>\n" \
                  f"CPU Physical Cores: <code>{psutil.cpu_count(logical=False)}</code>\n" \
                  f"CPU Logical Cores: <code>{psutil.cpu_count(logical=True)}</code>\n" \
                  f"Current CPU Frequency: <code>{psutil.cpu_freq().current}</code>\n" \
                  f"Min CPU Frequency: <code>{psutil.cpu_freq().min}</code>\n" \
                  f"Max CPU Frequency: <code>{psutil.cpu_freq().max}</code>\n" \
                  f"CPU Utilization: <code>{psutil.cpu_percent(interval=1)}</code>\n" \
                  f"Per-CPU Utilization: <code>{psutil.cpu_percent(interval=1, percpu=True)}</code>\n" \
                  f"Total RAM: <code>{round(psutil.virtual_memory().total/1000000000, 2)} GB</code>\n" \
                  f"Available RAM: <code>{round(psutil.virtual_memory().available/1000000000, 2)} GB</code>\n" \
                  f"Used RAM: <code>{round(psutil.virtual_memory().used/1000000000, 2)} GB</code>\n" \
                  f"RAM Usage: <code>{psutil.virtual_memory().percent}%</code>"

            if self.is_private(update.message):
                await update.message.reply_text(msg)
            else:
                await self.tgb.app.bot.send_message(
                    update.effective_user.id,
                    f"{msg}\n\nChat details: <code>{update.effective_chat.to_json()}</code>")
        except Exception as e:
            self.log.error(f"Could not send debug info: {e}")
            await self.notify(e)
