import json
from http.client import HTTPException
from pathlib import Path

import discord
from discord import Option
from discord.ext import commands

from constants import ICONS_ALL


class Administration(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    @commands.is_owner()
    @commands.slash_command(description="List all emotes")
    async def list_emotes(self, ctx: discord.ApplicationContext):
        await ctx.respond('Listing', delete_after=3)
        for i in ICONS_ALL.values():

            guildName = (self.bot.get_guild(i)).name
            await ctx.send(f"```Channel {guildName}```")

            for j in list(await self.bot.get_guild(i).fetch_emojis()):
                await ctx.send(f"{j.name} -> {j}\n")
        await ctx.respond("Done")

    @commands.is_owner()
    @commands.slash_command(description="Move emotes from one server to another")
    async def migrate_emojis(self, ctx: discord.ApplicationContext, from_id: discord.Option(str), to_id: discord.Option(str)):
        reciever_guild = await self.bot.fetch_guild(int(to_id))
        sender_emojis = await discord.Guild.fetch_emojis(await self.bot.fetch_guild(int(from_id)))

        await ctx.respond("Starting the process", ephemeral=True)

        try:
            for i in list(sender_emojis):
                await reciever_guild.create_custom_emoji(name=i.name, image=await i.read())
        except HTTPException:
            await ctx.respond("Not enough space on reciever's end")

        await ctx.respond(f"Done")

    @commands.is_owner()
    @commands.slash_command(descriptino="Send the contens of the channel")
    async def send_channel(self, ctx: discord.ApplicationContext, reciever_id: discord.Option(str)):
        await ctx.respond("Starting the process", ephemeral=True)

        reciever = await self.bot.fetch_user(int(reciever_id))

        async for message in ctx.channel.history(oldest_first=True):
            if message.author == self.bot.user:
                await reciever.send(f"```{message.content}```")


def setup(bot):
    bot.add_cog(Administration(bot))
