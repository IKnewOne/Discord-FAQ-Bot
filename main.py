import asyncio
import os

import discord
from discord.ext import commands
from dotenv import find_dotenv, load_dotenv
from admin import Administration
from emoji_management import emojify, deemojify

load_dotenv(find_dotenv())
TOKEN = os.environ.get("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot(intents=intents)

# Create dictionary with bot emojis
ICONS_RDRUID = 1010581918070358156
ICONS_FERAL = 846367980207472671
ICONS_ALL = [ICONS_RDRUID,ICONS_FERAL]
emoji_dict = {}


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})\n------")
    print("Initializing emojis...")

    for i in ICONS_ALL:
        for j in list(await bot.get_guild(i).fetch_emojis()):
            emoji_dict[f':{j.name}:'] = str(j)

    print("Done")


@bot.event
async def on_application_command_error(ctx, error):
    await ctx.respond(error, ephemeral=True)


@bot.command(description="hi")
async def hi(ctx: discord.ApplicationContext):
    await ctx.respond("​", delete_after=0.1)
    await ctx.send(f"OwO привет <:eshy:1012397593118113792>")


@bot.command(description="Republish")
@commands.has_permissions(manage_messages=True)
async def republish(ctx: discord.ApplicationContext):
    await ctx.respond("Starting the process", ephemeral=True)
    async for message in ctx.channel.history(oldest_first=True):
        if message.content:
            if message.author == bot.user:
                await ctx.channel.send(message.content, suppress=True, files=[await discord.Attachment.to_file(x) for x in message.attachments])
            else:
                await ctx.channel.send(emojify(message.content, emoji_dict), suppress=True, files=[await discord.Attachment.to_file(x) for x in message.attachments])
        else:
            await ctx.channel.send("*** ***")
        await message.delete()


@bot.command(description="Clears the channnel")
@commands.has_permissions(manage_messages=True)
async def clear(ctx: discord.ApplicationContext, amount: discord.Option(str, default=20),):
    cleared = await ctx.channel.purge(limit=int(amount))
    await ctx.respond(f"Done clearing {len(cleared)} messages", delete_after=10)


@bot.message_command(name="Edit message")
@commands.has_permissions(manage_messages=True)
async def edit_message(ctx: discord.ApplicationContext, message: discord.Message):

    if not (message.author.id == bot.user.id):
        await ctx.respond("Cannot edit non-bot message", ephemeral=True)
        return

    orgnl_msg = message
    await ctx.respond("Sent you a dm", ephemeral=True)
    await ctx.user.send(f' ```{deemojify(message.content)}``` \n Write "Cancel" to stop the process', suppress=True, files=[await discord.Attachment.to_file(x) for x in message.attachments])

    try:
        def check(m):
            return m.author == ctx.author and m.channel == m.author.dm_channel and m.content
        answ = await bot.wait_for("message", check=check, timeout=120.0)
    except asyncio.TimeoutError:
        await ctx.user.send("Took too long")
    else:
        if answ.content.lower() == "cancel":
            await ctx.user.send("Cancelled")
            return
        await orgnl_msg.edit(emojify(answ.content, emoji_dict), suppress=True, attachments=[], files=[await discord.Attachment.to_file(x) for x in answ.attachments])
        await ctx.user.send(f"Successfully changed message {orgnl_msg.jump_url}")


@bot.message_command(name="Insert empty message")
@commands.has_permissions(manage_messages=True)
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
        await msg_crt.edit(msg_nxt.content, suppress=True, files=[await discord.Attachment.to_file(x) for x in msg_nxt.attachments])

    await message.edit(content="*** ***")


# bot.load_extension('testing')
bot.add_cog(Administration(bot))
bot.run(TOKEN)
