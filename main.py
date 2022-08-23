import asyncio
import itertools
import json
import os
from asyncio import TimeoutError

import discord
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
    for i in list(await discord.Client.get_guild(bot, 1010581918070358156).fetch_emojis()):
        emoji_dict[f':{i.name}:'] = str(i)
    print("Done")


@bot.event
async def on_application_command_error(ctx, error):
    await ctx.respond(error, ephemeral=True)


@bot.command(description="Привет комрад")
async def hi(ctx):
    await ctx.respond("​", delete_after=0.1)
    await ctx.send(f"Hi {emoji_dict.get(':eshy:')}")


@bot.command(description="Clears the channnel")
async def clear(ctx):
    clea = await ctx.channel.purge()
    await ctx.respond(f"Done clearing {len(clea)} messages", delete_after=3)


@bot.message_command(name="Edit message")
@discord.ext.commands.has_permissions(manage_messages=True)
async def edit_message(ctx, message):

    if not (message.author.id == bot.user.id):
        await ctx.respond("Cannot edit non-bot message", ephemeral=True)
        return

    orgnl_msg = message
    await ctx.respond("Sent you a dm", ephemeral=True)
    await ctx.user.send(f' ```{message.content}``` ', embed=None, files = [await discord.Attachment.to_file(x) for x in message.attachments])

    try:
        answ = await bot.wait_for("message", timeout=120.0)
    except asyncio.TimeoutError:
        await ctx.user.send("Took too long")
    else:
        await orgnl_msg.edit(emojify(answ.content), embed=None, files = [await discord.Attachment.to_file(x) for x in answ.attachments])
        await ctx.user.send(f"Successfully changed message {orgnl_msg.jump_url}")


@bot.message_command(name="Insert empty message")
@discord.ext.commands.has_permissions(manage_messages=True)
async def insert_message(ctx, message):
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
        await msg_crt.edit(msg_nxt.content, embed=None, files = [await discord.Attachment.to_file(x) for x in msg_nxt.attachments])

    await message.edit(content="[PH]")
bot.run(TOKEN)
