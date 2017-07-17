import discord
import asyncio
from discord.errors import HTTPException

import os
import random
import re


# Use these variable to limit overloading of the dice roller
MAXIMUM_DICE_ARGS = 10
MAXIMUM_DICE_COUNT = 1000
MAXIMUM_DICE_SIDES = 1000

MAX_MESSAGE_LENGTH = 2000


class Error(Exception):
    """Base class for exceptions"""
    pass


class DiceFormatError(Error):
    """Exception raised for errors in dice string format.

    Attributes:
        invalid_dice_str -- the invalid dice string which caused this exception to be raised
    """

    error_format = "__Error__: {0.mention} provided invalid dice [{1}].\n" \
                   "Valid format is <x>d<y>[(+|-)<z>].\n" \
                   "All values must be positive integers."

    def __init__(self, invalid_dice_str):
        self.invalid_dice_str = invalid_dice_str

    def get_error_string(self, author):
        return self.error_format.format(author, self.invalid_dice_str)


class DiceValueError(Error):
    """Exception raised for errors in dice values

    Attributes:
        invalid_dice_str -- the invalid dice string which caused this exception to be raised
    """

    error_format = "__Error__: {0.mention} gave a bad value for [{1}].\n" \
                   "Dice count maximum: {2}\n" \
                   "Dice sides maximum: {3}"

    def __init__(self, invalid_dice_str):
        self.invalid_dice_str = invalid_dice_str

    def get_error_string(self, author):
        return self.error_format.format(
            author,
            self.invalid_dice_str,
            MAXIMUM_DICE_COUNT,
            MAXIMUM_DICE_SIDES,
        )


def get_roll(dice_str, rng=random.SystemRandom()):
    """
    Simulates the effect of rolling one or more dice.

    :param dice_str: A dice string with the following format (invalid format raises an InputError):

        <x>d<y>[(+|-)<z>]

        where x, y, and z are all positive integers.
        x and y may be no greater than 1000, else a ValueError is raised.

    :param rng: A random number generator. Defaults to random.SystemRandom()

    :return: An int list of all dice rolled
    """

    match = re.match(r'^(\d+)d(\d+)([+-]\d+)?$', dice_str)
    if match:
        result = []
        add = 0
        num_dice = int(match.group(1))
        num_sides = int(match.group(2))
        if match.group(3):
            add = int(match.group(3))
        # Check for valid dice count and sides
        if num_dice > MAXIMUM_DICE_COUNT or num_sides > MAXIMUM_DICE_SIDES:
            raise DiceValueError(dice_str)
        for x in range(0, num_dice):
            roll = rng.randint(1, num_sides) + add
            result.append(roll)
        return result
    else:
        raise DiceFormatError(dice_str)


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
        if command == '!roll-help':
            #
            # !help
            #
            pass
        elif command == '!roll':
            #
            # !roll
            #
            rng = random.SystemRandom()
            if len(args) > MAXIMUM_DICE_ARGS:
                # Let the author know that only the first MAXIMUM_DICE_ARGS dice were considered
                output = "Warning {0.mention}: maximum dice arguments is {1}. Proceeding with first {1} " \
                         "arguments...".format(message.author, MAXIMUM_DICE_ARGS)
                await client.send_message(message.channel, output)
            dice_list = args[:MAXIMUM_DICE_ARGS]
            response_format = "{0.mention} rolled:\n{1}"
            roll_format = "**{0}**: {1}"
            if len(dice_list) == 0:
                output = roll_format.format("1d20", str(rng.randint(1, 20)))
                await client.send_message(message.channel, response_format.format(message.author, output))
            else:
                try:
                    rolls = [roll_format.format(dice_str, " ".join([str(x) for x in get_roll(dice_str, rng)]))
                             for dice_str in dice_list]
                    output = "\n".join(rolls)
                    # Check to make sure the message isn't too long
                    if len(output) > MAX_MESSAGE_LENGTH:
                        # TODO: split up the message and deliver in pieces
                        await client.send_message(message.channel, "__Error__: {0.mention} The response was too long "
                                                                   "for the server to handle. Try fewer/smaller dice.".
                                                  format(message.author))
                    else:
                        await client.send_message(message.channel, response_format.format(message.author, output))
                except DiceFormatError as e:
                    await client.send_message(message.channel, e.get_error_string(message.author))
                except DiceValueError as e:
                    await client.send_message(message.channel, e.get_error_string(message.author))
                except HTTPException:
                    await client.send_message(message.channel, "__Error__: {0.mention} An error occurred while "
                                                               "attempting to communicate with the server.".
                                              format(message.author))
                # TODO: catch all other exceptions and log to file
                # TODO: Add "try !roll-help" to end of every error message
    except ValueError:
        # Empty message. Do nothing
        pass


client.run(os.environ['DISCORD_DICEROLL_TOKEN'])
