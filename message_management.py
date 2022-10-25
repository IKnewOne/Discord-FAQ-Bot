import asyncio
from re import match

import discord
from discord import Option
from discord.ext import commands

from emoji_management import deemojify, emojify


class MessageManagement(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    @commands.slash_command(description="Dump messages to user id")
    @commands.is_owner()
    async def dump_messages(self, ctx: discord.ApplicationContext, id: Option(str)):
        user = self.bot.get_user(int(id))
        if user == None:
            await ctx.respond(f"Bad user name {user.name}")
            return
        await ctx.respond(f"Sending the messages to {user.name}")
        async for message in ctx.channel.history(oldest_first=True):
            await user.send(f"```{deemojify(message.content)}```")

    @commands.slash_command(description="Clears the channnel")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx: discord.ApplicationContext, amount: Option(int, default=20)):
        cleared = await ctx.channel.purge(limit=amount)
        await ctx.respond(f"Done clearing {len(cleared)} messages", delete_after=10)

    @commands.slash_command(description="Purge via channel history and manual deletion method")
    @commands.has_permissions(manage_messages=True)
    async def hardclear(self, ctx: discord.ApplicationContext):

        for message in ctx.channel.history(oldest_first=True):
            message.delete

        await ctx.respond("Done", ephemeral=True)

    @commands.slash_command(description="Republish")
    @commands.has_permissions(manage_messages=True)
    async def republish(self, ctx: discord.ApplicationContext):
        """Take every message in the channel, delete it and send their copies from bot account"""
        await ctx.respond("Starting the process", ephemeral=True)
        async for message in ctx.channel.history(oldest_first=True):
            if message.content:
                if message.author == self.bot.user:
                    await ctx.channel.send(message.content, suppress=True, files=[await discord.Attachment.to_file(x) for x in message.attachments])
                else:
                    await ctx.channel.send(emojify(message.content), suppress=True, files=[await discord.Attachment.to_file(x) for x in message.attachments])
            else:
                await ctx.channel.send("*** ***")
            await message.delete()

    @commands.message_command(name="Insert empty message")
    @commands.has_permissions(manage_messages=True)
    async def insert_message(self, ctx: discord.ApplicationContext, message: discord.Message):
        chnl_bot_msgs = list()
        chn = ctx.channel

        await ctx.respond(f"Inserted empty message at {message.jump_url}", ephemeral=True)

        # Create an empty message to move last message into
        await ctx.channel.send("*** ***")

        # Get list of bot messages from the end to the one being replaced
        async for msg in ctx.channel.history():
            if msg.author == self.bot.user:
                if message.id == msg.id:
                    chnl_bot_msgs.append(msg.id)
                    break
                chnl_bot_msgs.append(msg.id)

        # Start from the end, take the current message content and earlier message content, move
        # earlier message into current one. Walk along all message ids except the one being replaced
        #
        #               A <- Insert position    >     *** ***
        #               ↓                       >        |
        #               B                       >        A
        #               ↓                       >        |
        #   Created empty message "*** ***"     >        B

        for i in range(len(chnl_bot_msgs[0:-1])):
            msg_crt, msg_nxt = await asyncio.gather(chn.fetch_message(chnl_bot_msgs[i]),
                                                    chn.fetch_message(chnl_bot_msgs[i+1]))
            # remove all current message attachments then add attachments from next message to this one
            await msg_crt.edit(msg_nxt.content, suppress=True, attachments=[], files=[await discord.Attachment.to_file(x) for x in msg_nxt.attachments])
        await message.edit(content="**[PH]**")

    @commands.message_command(name="Edit message")
    @commands.has_permissions(manage_messages=True)
    async def edit_message(self, ctx: discord.ApplicationContext, message: discord.Message):

        if not (message.author.id == self.bot.user.id):
            await ctx.respond("Cannot edit non-bot message", ephemeral=True)
            return

        orgnl_msg = message
        await ctx.respond("Sent you a dm", ephemeral=True)
        await ctx.user.send(f' ```{deemojify(orgnl_msg.content)}``` \n Write "Cancel" to stop the process', suppress=True, files=[await discord.Attachment.to_file(x) for x in orgnl_msg.attachments])

        try:
            # Pick up only non-empty message from the author of ctx command requrest in the DM channel
            def check(m):
                return m.author == ctx.author and m.channel == m.author.dm_channel and m.content
            answ = await self.bot.wait_for("message", check=check, timeout=120.0)
        except asyncio.TimeoutError:
            await ctx.user.send("Took too long")
        else:
            if answ.content.lower() == "cancel":
                await ctx.user.send("Cancelled")
                return
            await orgnl_msg.edit(emojify(answ.content), suppress=True, attachments=[], files=[await discord.Attachment.to_file(x) for x in answ.attachments])
            await ctx.user.send(f"Successfully changed message at {orgnl_msg.jump_url}")

    @commands.has_permissions(manage_messages=True)
    @commands.slash_command(description="Summary")
    async def summary(self, ctx: discord.ApplicationContext):
        await ctx.respond("Starting the process...", ephemeral=True)

        description = ""
        async for msg in ctx.channel.history(oldest_first=True):
            rslt = match("(\*{2}.*\*{2})", msg.content)

            if rslt is not None:
                description += f"[{rslt.group(1)}]({msg.jump_url})\n"

        await ctx.channel.send("\n", embed=discord.Embed(
            title="Содержание",
            description=description,
            color=discord.Colour.blurple(),
        ))


def setup(bot):
    bot.add_cog(MessageManagement(bot))
