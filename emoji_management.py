import re

import discord
from discord.ext import commands

from constants import ICONS_ALL

# Create dictionary with bot emojis
emoji_dict = {}


async def init_emojis(bot) -> int:
    ecount = 0
    for i in ICONS_ALL.values():
        for j in list(await bot.get_guild(i).fetch_emojis()):
            emoji_dict[f':{j.name}:'] = str(j)
            ecount += 1
    return f"Initialized {ecount} emojis"


def emojify(s: str) -> str:
    """Turns all :emoji: style emojis into correct form for bot to send.

    Args:
        s (str): message content to transform
        emoji_dict (dict): your saved emoji dictionary

    Returns:
        str: Transformed message
    """
    for emoji, emoji_link in emoji_dict.items():
        s = s.replace(emoji, emoji_link)
    return s


def deemojify(s: str) -> str:
    """Turns content of a message into human-readable by transforming every emoji into :emoji: style

    Args:
        s (str): message content to transform

    Returns:
        str: Transformed message
    """
    return re.sub("\<(:[\d\w_]*:)\d*\>", r"\1", s)


class EmojiManagement(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Initializing emojis...")
        print(await init_emojis(self.bot))
        print("Done")

    @commands.is_owner()
    @commands.slash_command(description="List all emotes")
    async def list_emotes(self, ctx: discord.ApplicationContext):
        await ctx.respond('Starting', ephemeral=True)

        for i in ICONS_ALL.values():

            guildName = (self.bot.get_guild(i)).name
            await ctx.send(f"```Channel {guildName}```")
            guildEmotes = sorted(list(await self.bot.get_guild(i).fetch_emojis()), key=lambda x: x.name.lower())

            for i in range(2):
                msg = ""

                # Do 0-25 and 26-50 separately to not exceed the 2000 char limit
                for e in guildEmotes[i*25:(i+1)*25]:
                    msg += f"{e.name} -> {e}\n"

                await ctx.send(msg)

        await ctx.respond("Done", ephemeral=True)


def setup(bot):
    bot.add_cog(EmojiManagement(bot))
