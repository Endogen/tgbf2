import emoji as emo

from plugin import TGBFPlugin
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler


class Database(TGBFPlugin):

    async def init(self):
        if not await self.table_exists('test'):
            sql = await self.get_resource("create_test.sql")
            await self.exec_sql(sql)

        await self.add_handler(CommandHandler(self.handle, self.init_callback))

    @TGBFPlugin.send_typing
    async def init_callback(self, update: Update, context: CallbackContext):
        if len(context.args) < 2:
            await update.message.reply_text(await self.get_usage())
            return

        sub_command = context.args[0].lower()
        data = context.args[1].lower()

        if sub_command == 'insert':
            insert_sql = await self.get_resource('insert_test.sql')
            await self.exec_sql(insert_sql, data)
            await update.message.reply_text(f'{emo.DONE} Inserted <b>{data}</b>')

        elif sub_command == 'select':
            if not data.isdigit():
                await update.message.reply_text(f'{emo.ERROR} Second argument needs to be an Integer')
                return

            select_sql = await self.get_resource('select_test.sql')
            sql_data = await self.exec_sql(select_sql, int(data))

            data_string = str()
            if sql_data['success']:
                for entry in sql_data['data']:
                    data_string += (entry[0] + '\n')

                await update.message.reply_text(
                    f'{emo.DONE} Last {data} entries:\n{data_string}')
            else:
                await update.message.reply_text(f'{emo.ERROR} Something bad happened')

        else:
            await update.message.reply_text(f'{emo.ERROR} Unknown argument(s)')
