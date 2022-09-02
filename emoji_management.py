import re

ICONS_RDRUID = 1010581918070358156
ICONS_FERAL = 846367980207472671
ICONS_ALL = [ICONS_RDRUID,ICONS_FERAL]


def emojify(s: str, emoji_dict: dict) -> str:
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
