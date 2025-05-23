from http.client import HTTPException

import discord
from discord.ext import commands

from constants import ICONS_ALL
from emoji_management import init_emojis


class Administration(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

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
    @commands.slash_command(description="Send the contens of the channel")
    async def send_channel(self, ctx: discord.ApplicationContext, reciever_id: discord.Option(str)):
        await ctx.respond("Starting the process", ephemeral=True)

        reciever = await self.bot.fetch_user(int(reciever_id))

        async for message in ctx.channel.history(oldest_first=True):
            if message.author == self.bot.user:
                await reciever.send(f"```{message.content}```")

    @commands.slash_command(description="Refresh emojis")
    async def refresh_emojis(self, ctx: discord.ApplicationContext):
        await ctx.respond(await init_emojis(self.bot), ephemeral=True)


def setup(bot):
    bot.add_cog(Administration(bot))
