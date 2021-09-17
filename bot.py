#!/usr/local/bin/python3.9
# nohup ~/bot.py &

import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
from discord.ext.commands.errors import ClientException
from youtube_dl import YoutubeDL as yt
from discord.utils import get
from urllib.request import urlopen
import re
import time
import asyncio

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='~')
client = discord.Client()

queue = {}
duration = {}


def next_song(ctx):
    voice = get(ctx.bot.voice_clients, guild=ctx.guild)
    voice.play(queue[ctx.message.guild.id][0], after=lambda e: next_song(ctx))
    try:
        del queue[ctx.message.guild.id][0]
        time.sleep(duration[ctx.message.guild.id][0])
        del duration[ctx.message.guild.id][0]
    except IndexError:
        pass
    if not voice.is_playing():
        asyncio.run_coroutine_threadsafe(voice.disconnect(), bot.loop)


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')


@bot.command()
async def gay(message):
    await message.channel.send('dylans gay')


@bot.command()
async def play(ctx, url):
    voice = get(ctx.bot.voice_clients, guild=ctx.guild)
    if voice is None or not voice.is_playing():
        await player(ctx, url)


@bot.command()
async def pause(ctx):
    voice = get(ctx.bot.voice_clients, guild=ctx.guild)
    if voice.is_playing() and voice.is_connected():
        ctx.voice_client.pause()
    else:
        await ctx.channel.send('No song playing.')


@bot.command()
async def resume(ctx):
    voice = get(ctx.bot.voice_clients, guild=ctx.guild)
    if not voice.is_playing() and voice.is_connected():
        ctx.voice_client.resume()
    else:
        await ctx.channel.send('Song playing.')


@bot.command()
async def stop(ctx):
    voice = get(ctx.bot.voice_clients, guild=ctx.guild)
    if not voice.is_playing() or voice.is_playing() and voice.is_connected():
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
    else:
        await ctx.channel.send("Can't stop won't stop.")


@bot.command()
async def disconnect(ctx):
    try:
        await ctx.voice_client.disconnect()
    except AttributeError:
        await ctx.channel.send("I'm not in a channel.")


async def player(ctx, song_link):
    voice = get(ctx.bot.voice_clients, guild=ctx.guild)
    try:
        user_channel = ctx.author.voice.channel
    except AttributeError:
        user_channel = None
    if user_channel is None:
        await ctx.channel.send('Please join a voice channel')
    else:
        try:
            voice = await user_channel.connect()
        except ClientException:
            pass
    ydl_options = {'format': 'bestaudio', 'noplaylist': 'True',
                   'postprocessors': [
                       {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192', }]}
    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    with yt(ydl_options) as ydl:
        info = ydl.extract_info(song_link, download=False)
        song_link = info['formats'][0]['url']
        source = await discord.FFmpegOpusAudio.from_probe(song_link, **ffmpeg_options)
        if ctx.message.guild.id not in queue and ctx.message.guild.id not in duration:
            queue[ctx.message.guild.id] = []
            duration[ctx.message.guild.id] = []
        if len(queue[ctx.message.guild.id]) == 0 and not voice.is_playing():
            voice.play(source, after=lambda e: next_song(ctx))
        else:
            queue[ctx.message.guild.id].append(source)
            duration[ctx.message.guild.id].append(info['duration'] + 10)
            await ctx.channel.send(f"{info['title']} added to the queue.")

        await asyncio.sleep(info['duration'] + 10)
        if not voice.is_playing():
            await voice.disconnect()


@bot.command()
async def search(ctx, *, song):
    song_nospace = song.replace(' ', '')
    base = f'https://www.youtube.com/results?search_query={song_nospace}'
    html = urlopen(base)
    song_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    song_link = f'https://www.youtube.com/watch?v={song_ids[0]}'
    await player(ctx, song_link)


@bot.command()
async def skip(message):
    voice = get(bot.voice_clients, guild=message.guild)
    voice.stop()
    try:
        del duration[message.guild.id][0]
    except IndexError:
        pass
    try:
        next_song()
    except TypeError:
        pass


@bot.command()
async def commands(ctx):
    embed = discord.Embed(title='Commands', description='~play {Direct Link to Youtube} - Plays direct link from YouTube\n'\
                                                        '~search {song name} - If more than one band has song name use band name as well\n'\
                                                        '~skip - Skips current song and plays next in queue\n'\
                                                        '~disconnect - Removes bot from voice channel\n'\
                                                        '~pause - Pauses current song\n'\
                                                        '~resume - Continues song\n'\
                                                        '~stop - Stops music and disconnects bot')
    await ctx.channel.send(embed=embed)


bot.run(TOKEN)
