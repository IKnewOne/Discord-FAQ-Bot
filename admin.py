import json
from http.client import HTTPException

import discord
from discord import Option
from discord.ext import commands

from emoji_management import ICONS_ALL, deemojify


class Administration(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    @commands.is_owner()
    @commands.slash_command(description="List all emotes")
    async def list_emotes(self, ctx: discord.ApplicationContext):
        await ctx.respond('Listing', delete_after=3)
        for i in ICONS_ALL:
            message = ""
            gname = (self.bot.get_guild(i)).name
            await ctx.send(f"```Channel {gname}```")
            for j in list(await self.bot.get_guild(i).fetch_emojis()):
                # message += f"{j.name} -> {j}\n"
                await ctx.send(f"{j.name} -> {j}\n")
        await ctx.respond("Done")

    @commands.is_owner()
    @commands.slash_command(description="Save channel messages", )
    async def save_messages(self, ctx: discord.ApplicationContext, filename: Option(str, "Custom filename", default=None)):
        await ctx.respond("Saving", ephemeral=True)
        chn_id = ctx.channel_id
        chn_name = ctx.channel.name
        msgs = [{
            "chn_id": chn_id,
            "chn_name": chn_name
        }]
        async for msg in ctx.channel.history(oldest_first=True):
            content = deemojify(msg.content)

            images = []
            # Save images in /messages/channel_id/image_id
            # save this as data in the message description
            img_id = 0
            if msg.embeds:
                continue
            for attachment in msg.attachments:
                with open(f'messages/{chn_id}/{img_id}.png', 'wb') as f:
                    f.write(await attachment.read())
                    images.append(f"{chn_id}/{img_id}.png")
                    img_id = img_id + 1
            msgs.append({
                "content": content,
                "images": images
            })
        # Custom file name if given
        fn = filename if filename is not None else f"{chn_name}_{chn_id}"
        with open(f"messages/{fn}.json", "w", encoding='utf-8') as f:
            json.dump(msgs, f, ensure_ascii=False, indent=4)
        await ctx.respond("Done", ephemeral=True)

    @commands.is_owner()
    @commands.slash_command()
    async def migrate_emojis(self, ctx: discord.ApplicationContext, from_id: discord.Option(str), to_id: discord.Option(str)):
        reciever_guild = await self.bot.fetch_guild(int(to_id))
        # reciever_emojis = await discord.Guild.fetch_emojis(reciever_guild)
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
