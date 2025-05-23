import os

import discord
from discord.ext import commands
from dotenv import find_dotenv, load_dotenv

import discord.ext

load_dotenv(find_dotenv())
TOKEN = os.environ.get("TOKEN")
EXTENSIONS = [
    'emoji_management',
    'message_management',
    'admin',
    'special'
]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})\n------")


@bot.event
async def on_application_command_error(ctx, error):
    await ctx.respond(error, ephemeral=True)


@bot.slash_command(description="hi")
async def hi(ctx: discord.ApplicationContext):
    await ctx.respond("​", delete_after=0.1)
    await ctx.send(f"OwO привет <:eshy:1012397593118113792>")


@bot.slash_command(name="reload")
async def reload(ctx: discord.ApplicationContext):
    for i in EXTENSIONS:
        bot.reload_extension(i)
    await ctx.respond("Done", ephemeral=True)

bot.load_extensions(*EXTENSIONS)
bot.run(TOKEN)
