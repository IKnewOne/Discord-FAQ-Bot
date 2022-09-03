import asyncio
import os

import discord
from discord.ext import commands
from dotenv import find_dotenv, load_dotenv

from admin import Administration
from emoji_management import EmojiManagement
from message_management import MessageManagement

load_dotenv(find_dotenv())
TOKEN = os.environ.get("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})\n------")


@bot.event
async def on_application_command_error(ctx, error):
    await ctx.respond(error, ephemeral=True)


@bot.command(description="hi")
async def hi(ctx: discord.ApplicationContext):
    await ctx.respond("​", delete_after=0.1)
    await ctx.send(f"OwO привет <:eshy:1012397593118113792>")

@commands.is_owner()
@commands.message_command(description="Test")
async def TEST(self, ctx: discord.ApplicationContext, message: discord.Message):
    await ctx.respond("Sent you a dm", ephemeral=True)
    await ctx.user.send(f"```{message.content}```")


bot.add_cog(EmojiManagement(bot))
bot.add_cog(MessageManagement(bot))
bot.add_cog(Administration(bot))
bot.run(TOKEN)
