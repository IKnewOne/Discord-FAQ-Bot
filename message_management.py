import asyncio
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from re import match

import discord
import requests
from bs4 import BeautifulSoup
from discord import Message, Option
from discord.ext import commands

from constants import FILEPATH, reTitleGroup
from emoji_management import deemojify, emojify


class MessageManagement(commands.Cog):

    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    @staticmethod
    def fix_item_links(message: Message) -> None:
        # Regular expression to find unfixed links that are not already fixed
        unfixed_link_pattern = r'https://www.wowhead.com(?:/ru)?/item=\d+(?:/[^\s\)]*)?'
        fixed_link_pattern = r'\[.*?\]\(https://www.wowhead.com(?:/ru)?/item=\d+(?:/[^\s\)]*)?\)'

        def get_item_name(url):
            try:
                # Convert any English URL to its Russian equivalent
                url = re.sub(r'https://www.wowhead.com/item=', 'https://www.wowhead.com/ru/item=', url)

                response = requests.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                item_name = soup.find(class_='main').find(class_='text').find(class_='heading-size-1').get_text(strip=True)
                return item_name
            except Exception as e:
                print(f"Error fetching item name from {url}: {e}")
                return None

        def replace_link(url, item_name):
            item_id_match = re.search(r'item=(\d+)', url)
            if item_id_match and item_name:
                item_id = item_id_match.group(1)
                ru_url = f"https://www.wowhead.com/ru/item={item_id}"
                return f'[{item_name}]({ru_url})'
            return url

        # Split the content into parts where there are fixed links and unfixed links
        parts = re.split(f'({fixed_link_pattern})', message.content)
        new_parts = []
        links_to_fix = []

        # Collect all unfixed links in parts that need replacing
        for part in parts:
            if re.match(fixed_link_pattern, part):
                new_parts.append(part)
            else:
                # Find all unfixed links in this part
                unfixed_links = re.findall(unfixed_link_pattern, part)
                if unfixed_links:
                    links_to_fix.extend(unfixed_links)
                new_parts.append(part)

        # Use ThreadPoolExecutor to process links in parallel
        link_to_name = {}
        with ThreadPoolExecutor() as executor:
            future_to_url = {executor.submit(get_item_name, url): url for url in links_to_fix}
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    item_name = future.result()
                    link_to_name[url] = item_name
                except Exception as e:
                    print(f"Error processing link {url}: {e}")

        # Replace unfixed links in new_parts with the fetched item names
        for i, part in enumerate(new_parts):
            if not re.match(fixed_link_pattern, part):
                for url, item_name in link_to_name.items():
                    if url in part:
                        part = part.replace(url, replace_link(url, item_name))
                new_parts[i] = part

        # Reassemble the content
        message.content = ''.join(new_parts)

    @commands.slash_command(description="Dump messages to user id")
    @commands.is_owner()
    async def dump_messages(self, ctx: discord.ApplicationContext, id: Option(str)):
        user = self.bot.get_user(int(id))
        if user == None:
            await ctx.respond(f"Bad user name {user.name}")
            return
        await ctx.respond(f"Sending the messages to {user.name}", ephemeral=True)
        async for message in ctx.channel.history(oldest_first=True):
            await user.send(f"```{deemojify(message.content)}```", suppress=True)

    @commands.slash_command(description="Clears the channnel")
    @commands.is_owner()
    async def clear(self, ctx: discord.ApplicationContext, amount: Option(int, default=20)):
        cleared = await ctx.channel.purge(limit=amount)
        await ctx.respond(f"Done clearing {len(cleared)} messages", delete_after=10)

    @commands.slash_command(description="Republish")
    @commands.has_permissions(manage_messages=True)
    async def republish(self, ctx: discord.ApplicationContext):
        """Take every message in the channel, delete it and send their copies from bot account"""
        await ctx.respond("Starting the process", ephemeral=True)

        message: discord.Message
        async for message in ctx.channel.history(oldest_first=True):
            if message.content:
                if message.author == self.bot.user:
                    await ctx.channel.send(message.content, files=[await discord.Attachment.to_file(x) for x in message.attachments], embeds=message.embeds, suppress=False if message.embeds else True)
                else:
                    await ctx.channel.send(emojify(message.content), files=[await discord.Attachment.to_file(x) for x in message.attachments], embeds=message.embeds, suppress=False if message.embeds else True)
            else:
                if message.embeds and message.embeds[0].title == "Содержание":
                    await self.bot.get_command("summary").callback(self, ctx)
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
                                                    chn.fetch_message(chnl_bot_msgs[i + 1]))
            # remove all current message attachments then add attachments from next message to this one
            await msg_crt.edit(content=msg_nxt.content, attachments=[], files=[await discord.Attachment.to_file(x) for x in msg_nxt.attachments], embeds=msg_nxt.embeds, suppress=False if msg_nxt.embeds else True)
        await message.edit(content="**[PH]**", suppress=True, embeds=[])

    @commands.message_command(name="Turn into embed")
    @commands.has_permissions(manage_messages=True)
    async def embedify_message(self, ctx: discord.ApplicationContext, message: discord.Message):

        if not (message.author.id == self.bot.user.id):
            await ctx.respond("Cannot edit non-bot message", ephemeral=True)
            return

        title = match(reTitleGroup, message.content).group(1)
        messageContent = message.content.replace(title, "").strip()
        embed2 = discord.Embed(title=None, description=messageContent)

        await message.edit(content=title, embed=embed2, suppress=False)
        # await message.edit(title, suppress=True, attachments=[], files=[await discord.Attachment.to_file(x) for x in message.attachments], embed=embed)
        # await orgnl_msg.edit(emojify(answ.content), suppress=True, attachments=[], files=[await discord.Attachment.to_file(x) for x in answ.attachments])
        await ctx.respond(f"Successfully changed message at {message.jump_url}", ephemeral=True)

    @commands.message_command(name="Edit message")
    @commands.has_permissions(manage_messages=True)
    async def edit_message(self, ctx: discord.ApplicationContext, message: discord.Message):

        if not (message.author.id == self.bot.user.id):
            await ctx.respond("Cannot edit non-bot message", ephemeral=True)
            return

        originalMessage = message
        await ctx.respond("Sent you a dm", ephemeral=True)

        if message.embeds:
            await ctx.user.send(f' ```{deemojify(originalMessage.content)}\nEMBED\n{originalMessage.embeds[0].description}``` \n Write "Cancel" to stop the process',
                                files=[await discord.Attachment.to_file(x) for x in originalMessage.attachments], suppress=True)
        else:
            await ctx.user.send(f' ```{deemojify(originalMessage.content)}``` \n Write "Cancel" to stop the process', files=[await discord.Attachment.to_file(x) for x in originalMessage.attachments], suppress=True)

        # Pick up only non-empty message from the author of ctx command requrest in the DM channel
        def empty_message_check_dm(m):
            return m.author == ctx.author and m.channel == m.author.dm_channel and m.content

        answ: discord.Message = await self.bot.wait_for("message", check=empty_message_check_dm, timeout=240.0)

        if answ.content.lower() == "cancel":
            await ctx.user.send("Cancelled")
            return

        self.fix_item_links(answ)

        if 'EMBED' in answ.content:
            messageContent, embedContent = [
                x.strip() for x in answ.content.split("EMBED")]
            embed = discord.Embed(description=embedContent)
            await originalMessage.edit(content=emojify(messageContent), embed=embed)
        else:
            await originalMessage.edit(content=emojify(answ.content), attachments=[], files=[await discord.Attachment.to_file(x) for x in answ.attachments])
        await ctx.user.send(f"Successfully changed message at {originalMessage.jump_url}")

    @commands.has_permissions(manage_messages=True)
    @commands.slash_command(description="Summary", name="summary")
    async def summary(self, ctx: discord.ApplicationContext):
        await ctx.respond("Starting the process...", ephemeral=True)

        description = ""
        async for msg in ctx.channel.history(oldest_first=True):
            rslt = match(reTitleGroup, msg.content)
            # rslt = match("(\*{2}.*\*{2})", msg.content)

            if rslt is not None:
                description += f"[{rslt.group(1).replace('#', '').strip()}]({msg.jump_url})\n"

        await ctx.channel.send(content=None, embed=discord.Embed(
            title="Содержание",
            description=description,
            color=discord.Colour.blurple(),
        ))

    @commands.slash_command(description="Save channel messages", )
    async def save_messages(self, ctx: discord.ApplicationContext, filename: Option(str, "Filename", default=None)):
        await ctx.respond("Saving", ephemeral=True)
        chn_id = ctx.channel_id
        chn_name = ctx.channel.name

        msgs = [{
            "chn_name": chn_name,
            "chn_id": chn_id

        }]

        if filename == None:
            from datetime import date
            dt = date.today()

            match str(ctx.channel_id):
                case "862009501036838952":
                    filename = "resto"
                case "780149018104954921":
                    filename = "feral"
                case "780458782181294131":
                    filename = "guardian"
                case "779796524275204107":
                    filename = "boomkin"
                case _:
                    filename = ctx.channel.name

            filename += f"-{dt.day}.{dt.month}"

        Path(f"{FILEPATH}/{filename}").mkdir(parents=True, exist_ok=True)

        async for msg in ctx.channel.history(oldest_first=True):
            content = deemojify(msg.content)

            images = []
            # Save images in {FILEPATH}/channel_name/image_id
            # save this as data in the message description

            # Embeds
            embeds = []
            if msg.embeds:
                for embed in msg.embeds:
                    embeds.append(embed.description)

            for attachment in msg.attachments:
                img_id = 0
                with open(f'{FILEPATH}/{filename}/{img_id}.png', 'wb') as f:
                    f.write(await attachment.read())
                    images.append(f"{filename}/{img_id}.png")
                    img_id += 1
            msgs.append({
                "content": content,
                "images": images,
                "embeds": embeds
            })

        with open(f"{FILEPATH}/{filename}.json", "w", encoding='utf-8') as f:
            json.dump(msgs, f, ensure_ascii=False, indent=4)
        await ctx.respond("Done", ephemeral=True)

    @commands.slash_command(description="Publish")
    @commands.is_owner()
    async def publish(self, ctx: discord.ApplicationContext, filename: Option(str, "Name of file to publish", required=True)):

        if not Path(f"{FILEPATH}/{filename}.json").is_file():
            await ctx.respond(f"Bad filename: {filename}", ephemeral=True)
            return

        await ctx.respond("Starting")

        with open(f"{FILEPATH}/{filename}.json", 'r', encoding='utf-8') as f:
            messages = json.load(f)

            for msg in messages[1:]:
                files = []

                for image in msg["images"]:
                    files.append(discord.File(
                        f"{FILEPATH}/{image}")
                    )

                embeds = []
                for embed in msg["embeds"]:
                    embeds.append(discord.Embed(description=embed))

                await ctx.send(emojify(msg["content"]), files=files, embeds=embeds)


# def copyMessageContent(message: discord.Message):


def setup(bot):
    bot.add_cog(MessageManagement(bot))
