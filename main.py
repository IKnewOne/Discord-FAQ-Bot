import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TOKEN")

EXTENSIONS = [
    'emoji_management',
    'message_management',
    'admin',
    'special',
    # 'carousel',
]


intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")


@commands.is_owner()
@bot.slash_command(name="reload")
async def reload(ctx: discord.ApplicationContext):
    await bot.reload_extension(*EXTENSIONS)

    await ctx.respond("Reloaded all extensions", ephemeral=True)


@bot.event
async def on_application_command_error(ctx, error):
    await ctx.respond(f"Error: {error}", ephemeral=True)


@bot.command(description="hi")
async def hi(ctx: discord.ApplicationContext):
    await ctx.respond("​", delete_after=0.1)
    await ctx.send("OwO привет <:eshy:1012397593118113792>")


bot.load_extensions(*EXTENSIONS)
bot.run(TOKEN)
