from datetime import datetime
from discord import File, AllowedMentions
from discord.errors import NotFound
from os import remove
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from sys import argv
from tb_db import sql_op
from tb_discord import bot
from tb_discord.data_structures import RolesMessage, role_messages as active_role_messages
from tb_discord.tb_ui import RolesView
import logging
import random
import re

__all__ = []

started = False
JETS = ["F16", "F18", "F15", "F35", "F22", "A10", "F14", "MIR2"]
HOLDING_POINTS = ["A", "B", "C", "D"]
AERODROMES = ["UG5X", "UG24", "UGKO", "UGKS", "URKA", "URKN", "URMM", "URSS"]
RUNWAYS = ["22", "04"]
DEPARTURES = ["GAM1D", "PAL1D", "ARN1D", "TIB1D", "SOR1D", "RUD1D", "AGI1D", "DIB1D", "TUN1D", "NAL1D"]


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")

    global started
    if not started:
        started = True
        if "-c" not in argv:
            role_messages = sql_op("SELECT * FROM role_messages", (), fetch_all=True)
            for view_data in role_messages:
                try:
                    channel = bot.get_channel(int(view_data[1]))
                    message = await channel.fetch_message(int(view_data[0]))
                except NotFound:
                    sql_op("DELETE FROM role_messages WHERE message_id = %s", (view_data[0],))
                    logging.warning(f"Message with ID {view_data[0]} in channel {view_data[1]} could not be found.")
                    continue

                # Could do this in a list comprehension, but it"d be extremely unreadable
                roles = []
                for role_id in [int("".join(i)) for i in zip(*[iter(view_data[2])] * 20)]:
                    roles.append(channel.guild.get_role(role_id))

                message_data = RolesMessage(await message.edit(view=RolesView(roles)), roles)
                active_role_messages.append(message_data)


@bot.event
async def on_member_join(member):
    time = str(datetime.now())
    strip_text = {
        "slot": f"{time[11:16]}",
        "squawk": f"{random.randint(0, 6)}{random.randint(0, 7)}{random.randint(0, 7)}{random.randint(0, 7)}",
        "callsign": (f"{re.sub('[^a-zA-Z0-9]', '', member.name.upper())[:4]}"
                     f"{random.randint(0, 9)}{random.randint(0, 9)}"),
        "aircraft": f"{random.choice(JETS)}",
        "hold": f"{random.choice(HOLDING_POINTS)}",
        "aerodrome": f"{random.choice(AERODROMES)}",
        "runway": f"{random.choice(RUNWAYS)}",
        "departure": f"{random.choice(DEPARTURES)}"
    }
    assets_path = Path(__file__).parent / "../assets"
    strip = Image.open(assets_path / "strip_blank.png")
    font = ImageFont.truetype(str(assets_path / "consolas.ttf"), 40)
    font_large = ImageFont.truetype(str(assets_path / "consolas.ttf"), 70)
    d = ImageDraw.Draw(strip)
    d.text((67, 101), strip_text["slot"], font=font, fill=(0, 0, 0), anchor="mm")
    d.text((305, 101), strip_text["callsign"], font=font_large, fill=(0, 0, 0), anchor="lm")
    d.text((914, 101), strip_text["hold"], font=font_large, fill=(0, 0, 0), anchor="mm")
    d.text((1339, 150), strip_text["aerodrome"], font=font, fill=(0, 0, 0), anchor="mm")
    d.text((1632, 101), strip_text["runway"], font=font_large, fill=(0, 0, 0), anchor="mm")
    d.text((1803, 101), strip_text["departure"], font=font_large, fill=(0, 0, 0), anchor="mm")
    d.text((646, 150), strip_text["squawk"], font=font, fill=(0, 0, 0), anchor="lm")
    d.text((646, 57), "M/" + strip_text["aircraft"], font=font, fill=(0, 0, 0), anchor="lm")
    strip.save(fp="strip.png")
    await bot.get_channel(1099805424934469652).send(f"Welcome to Digital Controllers, "
                                                    f"{member.mention}!", file=File("strip.png"), allowedmentions=AllowedMentions.none())
    remove("strip.png")
