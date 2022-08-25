from http.client import HTTPException
from discord.ext import commands
import discord

ICONS_DRUID = 1010581918070358156


class Administration(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    @commands.is_owner()
    @commands.message_command(description="Test")
    async def TEST(self, ctx: discord.ApplicationContext, message: discord.Message):
        await ctx.respond("Sent you a dm", ephemeral=True)
        await ctx.user.send(f"```{message.content}```")

    @commands.is_owner()
    @commands.slash_command()
    async def migrate_emojis(self,
                             ctx: discord.ApplicationContext,
                             from_id: discord.Option(str),
                             to_id: discord.Option(str, default=ICONS_DRUID)):
        reciever_guild = await self.bot.fetch_guild(int(to_id))
        # reciever_emojis = await discord.Guild.fetch_emojis(reciever_guild)
        sender_emojis = await discord.Guild.fetch_emojis(await self.bot.fetch_guild(int(from_id)))

        await ctx.respond("Starting the process")

        try:
            for i in list(sender_emojis):
                await reciever_guild.create_custom_emoji(name=i.name, image=await i.read())
        except HTTPException:
            await ctx.respond("Not enough space on reciever's end")

        await ctx.respond(f"Done")


def setup(bot):
    bot.add_cog(Administration(bot))
