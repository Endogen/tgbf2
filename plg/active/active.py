from plugin import TGBFPlugin
from telegram import Update, Chat
from telegram.ext import CallbackContext, MessageHandler, filters


class Active(TGBFPlugin):

    async def init(self):
        if not await self.table_exists('active'):
            sql = await self.get_resource('create_active.sql')
            await self.exec_sql(sql)

        await self.add_handler(
            MessageHandler(
                filters.ALL,
                self.init_callback,
                block=False
            )
        )

        self.run_repeating(self.cleaner_callback, 86_400)

    async def init_callback(self, update: Update, context: CallbackContext):
        try:
            if update.message.chat.type == Chat.PRIVATE:
                return

            c = update.effective_chat
            u = update.effective_user
            m = update.effective_message

            if not u:
                return
            if u.is_bot:
                return

            await self.exec_sql(
                await self.get_resource('insert_active.sql'),
                c.id,
                c.title,
                c.link,
                u.id,
                '@' + u.username if u.username else u.first_name,
                m.id,
                len(m.text) if m.text else None,
                m.text if m.text else None
            )
        except Exception as e:
            self.log.error(f'Can not save activity: {e} - UPDATE: {update}')
            await self.notify(e)

    async def cleaner_callback(self, context: CallbackContext):
        sql = await self.get_resource('delete_active.sql')
        sql = sql.replace('?', self.cfg.get('remove_after_days'))
        await self.exec_sql(sql)
