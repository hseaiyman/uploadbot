import os
import asyncio
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

import nest_asyncio
nest_asyncio.apply()

TOKEN = '7743531642:AAHvLUDpx1stBvEmqH6sOLXTzZBIb9ztR8w'
MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2000 MB (2 GB)

async def start(update: Update, context):
    await update.message.reply_text('Welcome! Send me a file link, and I will upload it to Telegram. Maximum file size: 2 GB.')

async def download_file(url, file_name, update):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                await update.message.reply_text('Failed to download the file. Please check the link and try again.')
                return None

            total_size = int(response.headers.get('content-length', 0))
            if total_size > MAX_FILE_SIZE:
                await update.message.reply_text(f'The file is too large. Maximum allowed size is {MAX_FILE_SIZE / (1024 * 1024):.2f} MB.')
                return None

            progress_message = await update.message.reply_text('Downloading: 0%')
            with open(file_name, 'wb') as file:
                downloaded = 0
                async for chunk in response.content.iter_chunked(8192):
                    file.write(chunk)
                    downloaded += len(chunk)
                    progress = (downloaded / total_size) * 100
                    if downloaded % (5 * 1024 * 1024) == 0:  # Update progress every 5 MB
                        await progress_message.edit_text(f'Downloading: {progress:.2f}%')

            await progress_message.delete()
            return file_name

async def handle_link(update: Update, context):
    link = update.message.text
    try:
        file_name = os.path.basename(link) or 'downloaded_file'
        await update.message.reply_text('Starting download...')
        
        downloaded_file = await download_file(link, file_name, update)
        if downloaded_file:
            await update.message.reply_text('Upload to Telegram starting...')
            with open(downloaded_file, 'rb') as file:
                await update.message.reply_document(document=file, filename=file_name)
            os.remove(downloaded_file)
            await update.message.reply_text('File uploaded successfully!')
    except Exception as e:
        await update.message.reply_text(f'An error occurred: {str(e)}')

async def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    print("Bot is running...")
    
    while True:
        await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(main())
