from base64 import encode
from http.client import HTTPException
import json
from discord.ext import commands
import discord
from emoji_management import deemojify

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
    @commands.slash_command(description="Save channel messages")
    async def save_messages(self, ctx: discord.ApplicationContext):
        await ctx.respond("Saving", ephemeral=True)
        img_id = 0
        msgs = []
        async for msg in ctx.channel.history(oldest_first=True):
            content = deemojify(msg.content)
            chn_id = ctx.channel_id
            images = []
            for attachment in msg.attachments:
                with open(f'messages/{chn_id}/{img_id}.jpg', 'wb') as f:
                    f.write(await attachment.read())
                    images.append(f"{chn_id}/{img_id}.jpg")
                    img_id = img_id + 1
            msgs.append({
                "content": content,
                "channel_id": chn_id,
                "images": images
            })
        with open(f"messages/{chn_id}-messages.json", "w", encoding='utf-8') as f:
            json.dump(msgs, f, ensure_ascii=False, indent=4)
        await ctx.respond("Done", ephemeral = True)

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
