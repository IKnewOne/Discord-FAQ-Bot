import re

import discord
from discord.ext import commands

from constans import ICONS_ALL

# Create dictionary with bot emojis
emoji_dict = {}


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

        for i in ICONS_ALL.values():
            for j in list(await self.bot.get_guild(i).fetch_emojis()):
                emoji_dict[f':{j.name}:'] = str(j)

        print("Done")


def setup(bot):
    bot.add_cog(EmojiManagement(bot))
