import asyncio
import itertools
import json
import os
from asyncio import TimeoutError
from http.client import ResponseNotReady

import discord
from discord.ext.commands import has_permissions, is_owner
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())
TOKEN = os.environ.get("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot(intents=intents)

# Create dictionary with bot emojis
emoji_dict = {}


def emojify(s: str) -> str:
    for emoji, emoji_link in emoji_dict.items():
        s = s.replace(emoji, emoji_link)
    return s


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})\n------")
    print("Initializing emojis...")
    for i in list(await discord.Client.get_guild(bot, 942472342444048425).fetch_emojis()):
        emoji_dict[f':{i.name}:'] = str(i)
    print("Done")


@bot.event
async def on_application_command_error(ctx, error):
    await ctx.respond(error, ephemeral=True)


@bot.command(description="hi")
async def hi(ctx: discord.ApplicationContext):
    await ctx.respond("​", delete_after=0.1)
    await ctx.send(f"Hi <:eshy:1010604641802801172>")


@bot.command(description="Republish")
@has_permissions(manage_messages=True)
async def republish(ctx: discord.ApplicationContext):
    await ctx.respond("Starting the process", ephemeral=True)
    async for message in ctx.channel.history(oldest_first=True):
        if message.content:
            await ctx.channel.send(message.content, suppress=True, files=[await discord.Attachment.to_file(x) for x in message.attachments])
        await message.delete()


@bot.command(description="Clears the channnel")
@has_permissions(manage_messages=True)
async def clear(ctx: discord.ApplicationContext):
    clea = await ctx.channel.purge()
    await ctx.respond(f"Done clearing {len(clea)} messages", delete_after=3)


@bot.message_command(description="Test")
@is_owner()
async def test(ctx: discord.ApplicationContext, message: discord.Message):
    await ctx.respond("Sent you a dm", ephemeral=True)
    await ctx.user.send(message)


@bot.message_command(name="Edit message")
@has_permissions(manage_messages=True)
async def edit_message(ctx: discord.ApplicationContext, message: discord.Message):

    if not (message.author.id == bot.user.id):
        await ctx.respond("Cannot edit non-bot message", ephemeral=True)
        return

    orgnl_msg = message
    await ctx.respond("Sent you a dm", ephemeral=True)
    await ctx.user.send(f' ```{message.content}``` ', suppress=True, files=[await discord.Attachment.to_file(x) for x in message.attachments])

    try:
        def check(m):
            return m.user == ctx.user and m.channel == m.user.dm_channel and m.content
        answ = await bot.wait_for("message", timeout=120.0)
    except asyncio.TimeoutError:
        await ctx.user.send("Took too long")
    else:
        await orgnl_msg.edit(emojify(answ.content), suppress=True, attachments=[], files=[await discord.Attachment.to_file(x) for x in answ.attachments])
        await ctx.user.send(f"Successfully changed message {orgnl_msg.jump_url}")


@bot.message_command(name="Insert empty message")
@has_permissions(manage_messages=True)
async def insert_message(ctx: discord.ApplicationContext, message: discord.Message):
    chnl_bot_msgs = list()
    chn = ctx.channel

    await ctx.respond(f"Created empty message at {message.jump_url}", ephemeral=True)
    await ctx.channel.send("Temp msg")

    # Get list of bot messages
    async for msg in ctx.channel.history():
        if msg.author == bot.user:
            chnl_bot_msgs.append(msg.id)

    for i in range(len(chnl_bot_msgs[:chnl_bot_msgs.index(message.id)])):
        msg_nxt = await chn.fetch_message(chnl_bot_msgs[i+1])
        msg_crt = await chn.fetch_message(chnl_bot_msgs[i])
        await msg_crt.edit(msg_nxt.content, supress=True, files=[await discord.Attachment.to_file(x) for x in msg_nxt.attachments])

    await message.edit(content="*** ***")
bot.run(TOKEN)
