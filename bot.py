import asyncio
import os
import re
import uuid
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command
from yt_dlp import YoutubeDL
from shazamio import Shazam
from pydub import AudioSegment

TOKEN = "7896639551:AAGkVQ6MvSd15bzAz-RHPZEAheJK4BxOmfo"
OWNER_USERNAME = "@Alavkhanovvv"

bot = Bot(token=TOKEN)
dp = Dispatcher()
shazam = Shazam()


def get_music_buttons(video_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎵 Скачать музыку из видео", callback_data=f"download_music:{video_id}")],
        [InlineKeyboardButton(text="🔍 Найти полную версию", callback_data=f"find_full_track:{video_id}")]
    ])
    return keyboard


@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}! Отправь ссылку на видео из TikTok, Instagram или YouTube.")


@dp.message(F.text)
async def download_video(message: Message):
    url = message.text.strip()
    if not re.match(r"https?://(www\.)?(youtube\.com|youtu\.be|tiktok\.com|instagram\.com)", url):
        await message.answer("⚠️ Отправь ссылку на видео из YouTube, TikTok или Instagram.")
        return

    await message.answer("⏳ Обрабатываю видео...")
    video_id = str(uuid.uuid4())
    video_path = f"downloads/{video_id}.mp4"

    ydl_opts = {
        "format": "best",
        "quiet": True,
        "noplaylist": True,
        "outtmpl": video_path
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        file = FSInputFile(video_path)
        await message.answer_video(file, caption=f"🎬 Видео скачано!", reply_markup=get_music_buttons(video_id))
    except Exception as e:
        await message.answer(f"❌ Ошибка при скачивании: {e}")


@dp.callback_query(F.data.startswith("download_music"))
async def download_music(callback: CallbackQuery):
    video_id = callback.data.split(":")[1]
    video_path = f"downloads/{video_id}.mp4"
    audio_path = f"downloads/{video_id}.mp3"

    if not os.path.exists(video_path):
        await callback.message.answer("⚠ Музыка еще не загружена. Скачайте видео сначала.")
        return

    await callback.message.answer("🎵 Извлекаю музыку...")
    try:
        audio = AudioSegment.from_file(video_path, format="mp4")
        audio.export(audio_path, format="mp3", bitrate="192k")
        file = FSInputFile(audio_path)
        await callback.message.answer_audio(file, caption="🎶 Музыка из видео загружена!")
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при извлечении музыки: {e}")


@dp.callback_query(F.data.startswith("find_full_track"))
async def find_full_track(callback: CallbackQuery):
    video_id = callback.data.split(":")[1]
    video_path = f"downloads/{video_id}.mp4"

    if not os.path.exists(video_path):
        await callback.message.answer("⚠ Видео еще не загружено. Скачайте его сначала.")
        return

    await callback.message.answer("🔍 Определяю трек...")
    try:
        song_data = await shazam.recognize_song(video_path)
        if song_data and "track" in song_data:
            track = song_data["track"]
            track_name = track.get("title", "Неизвестно")
            artist = track.get("subtitle", "Неизвестен")
            search_query = f"{artist} {track_name} audio"

            await callback.message.answer(f"🎶 Трек найден: {track_name} – {artist}\n🔍 Ищу полную версию...")

            music_path = f"downloads/{track_name}.mp3"
            ydl_opts = {
                "format": "bestaudio/best",
                "quiet": True,
                "noplaylist": True,
                "outtmpl": music_path
            }

            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"ytsearch:{search_query}"])

            file = FSInputFile(music_path)
            await callback.message.answer_audio(file, caption=f"🎶 Полная версия: {track_name} – {artist}")
        else:
            await callback.message.answer("❌ Не удалось определить трек.")
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при поиске полной версии: {e}")


async def main():
    await dp.start_polling(bot)


print("Бот запущен!")

if __name__ == "__main__":
    asyncio.run(main())