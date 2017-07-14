import discord
import asyncio

import os
import random
import re


class InputError(Exception):
    """Exception raised for errors in input"""


def get_roll(dice_str, rng=random.SystemRandom()):
    """
    Simulates the effect of rolling one or more dice.

    :param dice_str: A dice string with the following format (invalid format raises an InputError):

        <x>d<y>[(+|-)<z>]

        where x, y, and z are all positive integers.

    :param rng: A random number generator. Defaults to random.SystemRandom()

    :return: A space-separated list of all the dice rolled, preceded by the original dice string
    """
    match = re.match(r'^(\d+)d(\d+)([+-]\d+)?$', dice_str)
    if match:
        result = []
        add = 0
        if match.group(3):
            add = int(match.group(3))
        for x in range(0, int(match.group(1))):
            roll = str(rng.randint(1, int(match.group(2))) + add)
            result.append(roll)
        return "**" + dice_str + "**: " + str(" ".join(result))
    else:
        raise InputError


client = discord.Client()


@client.event
async def on_ready():
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    print("------")


@client.event
async def on_message(message):
    try:
        command, *args = message.content.split()
        if command == '!roll':
            rng = random.SystemRandom()
            dice_list = args
            response_format = "{0.mention} rolled {1}."
            error_response_format = "Error: {0.mention} provided invalid dice. Valid format is <x>d<y>[(+|-)<z>]."
            if len(dice_list) == 0:
                await client.send_message(message.channel, response_format.format(message.author, rng.randint(1, 20)))
            else:
                try:
                    output = ", ".join(map(get_roll, dice_list))
                    await client.send_message(message.channel, response_format.format(message.author, output))
                except InputError:
                    await client.send_message(message.channel, error_response_format.format(message.author))
    except ValueError:
        # Empty message. Do nothing
        pass


client.run(os.environ['DISCORD_DICEROLL_TOKEN'])
