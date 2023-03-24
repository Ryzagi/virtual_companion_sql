import argparse
import asyncio
import json
import os
from pathlib import Path

import aiohttp
import aioschedule
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import KeyboardButton
from aiogram.utils import executor
from converbot.constants import PROD_ENV, DEV_ENV


import discord
from discord.ext import commands
from discord.ext.commands import Bot, Context
from discord.ext import tasks
from discord import Message


ENABLE_SLEEP = True

intents = discord.Intents.default()
intents.members = True
bot = Bot(command_prefix='/', intents=intents)
MAX_MESSAGE_LENGTH = 2000


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--discord_token", help="Discord_token bot token", type=str, required=True
    )
    parser.add_argument(
        "--sql_config_path",
        help="Path to the sql config file",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--prompt_config_path",
        help="Path to the prompt config file",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--model_config_path",
        help="Path to the model config file",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--env",
        help="Environment name (Prod/dev)",
        type=str,
        choices=[PROD_ENV, DEV_ENV],
        required=False,
        default=DEV_ENV,
    )
    return parser.parse_args()


args = parse_args()

IS_DEBUG = False

questions = {
    'What is your name?': 'age',
    'How old are you?': 'gender',
    'What is your gender?': 'interest',
    'What are your interests?': 'done'
}

# Define the state of each user's conversation
conversation_states = {}

def try_(func):
    async def try_except(message):
        error = ""
        for i in range(4):
            try:
                await func(message)
                return None
            except Exception as e:
                print(e)
                error = str(e).lower()
                pass
            await asyncio.sleep(1)
        if "overloaded with other requests" in error:

            await message.channel.send("\nPlease, try again later, We are currently under heavy load")
        else:

            await message.channel.send('\nSomething went wrong, please type "/start" to start over')
        return None

    return try_except



@bot.command(name='companions_list')
async def companions_list(message: Message):
    # Example for COMPANION_LIST_ENDPOINT
    async with aiohttp.ClientSession() as session:
        async with session.post(
                "http://localhost:8000/api/SpeechSynthesizer/list_companion",
                json={"user_id": message.author.id},
        ) as response:
            bot_descriptions = await response.json()

    if bot_descriptions is None:

        await message.channel.send("You haven`t any conversations!\nPlease, /start new conversation with me!")

        return None

    bot_description_output = []
    for companion_info in bot_descriptions:
        bot_description = f"Conversation ID #{companion_info['companion_id']}:\n\n{companion_info['description']}"
        bot_description_output.append(bot_description)

    message_bot_descriptions = "\n\n".join(bot_description_output)


    await message.channel.send(message_bot_descriptions)



@bot.command(name='load_conversation')
async def load_conversation(message: Message):
    conv_id = message.content.split(" ")[-1]
    # loaded_conversation = CONVERSATIONS.load_conversation(message.author.id, conv_id)

    async with aiohttp.ClientSession() as session:
        # Example for SWITCH_COMPANION_ENDPOINT
        async with session.post(
                "http://localhost:8000/api/SpeechSynthesizer/switch_companion",
                json={"user_id": message.author.id, "companion_id": conv_id},
        ) as response:
            loaded_conversation = await response.text()


    await message.channel.send(loaded_conversation)

    await message.channel.send("Hi there! It's nice to meet you again.")



@bot.command(name='delete_conversation')
async def delete_conversation(message: Message):
    conv_id = message.content.split(" ")[-1]
    # deleted_conversation = CONVERSATIONS.delete_conversation(message.author.id, conv_id)
    async with aiohttp.ClientSession() as session:
        # Example for DELETE_COMPANION_ENDPOINT
        async with session.post(
                "http://localhost:8000/api/SpeechSynthesizer/delete_companion",
                json={"user_id": message.author.id, "companion_id": conv_id},
        ) as response:
            deleted_conversation = await response.text()


    await message.channel.send(deleted_conversation)



@bot.command(name='delete_all_conversations')
async def delete_all_conversations(message: Message):
    # deleted_all_conversations = CONVERSATIONS.delete_all_conversations_by_user_id(message.author.id)
    async with aiohttp.ClientSession() as session:
        # Example for DELETE_ALL_COMPANIONS_ENDPOINT
        async with session.post(
                "http://localhost:8000/api/SpeechSynthesizer/delete_all_companions",
                json={"user_id": message.author.id},
        ) as response:
            deleted_all_conversations = await response.text()


    await message.channel.send(deleted_all_conversations)


    await message.channel.send("Please, /start new conversation with me!")



@bot.command(name='debug')
async def debug(message: Message):
    # conversation = CONVERSATIONS.get_conversation(message.author.id)
    async with aiohttp.ClientSession() as session:
        # Example for DEBUG_ENDPOINT
        async with session.post(
                "http://localhost:8000/api/SpeechSynthesizer/debug",
                json={"user_id": message.author.id},
        ) as response:
            conversation = await response.text()
            status_code = response.status

    if status_code == 406:

        await message.channel.send("Please, provide initial context.")


    await message.channel.send(conversation)


async def toggle_sleep(message) -> None:
    #async with session.post(
    #        "http://localhost:8000/api/SpeechSynthesizer/sleep",
    #        json={"user_id": message.from_user.id},
    #) as response:
    #    mode = await response.text()
    global ENABLE_SLEEP

    ENABLE_SLEEP = not ENABLE_SLEEP

    await message.channel.send(f"Sleep functionality {'enabled' if ENABLE_SLEEP else 'disabled'}")

@bot.command(name='start')
async def start(ctx):
    """
    This command will be called when user sends !start command
    """
    author_id = ctx.author.id
    conversation_states[author_id] = create_conversation_state()
    await ctx.channel.typing()
    await ctx.channel.send("Welcome to Neece.ai\nLet’s take a moment to describe the AI persona you want to talk to.")
    await ctx.channel.typing()
    await ctx.channel.send("What is the name you want to give your companion?")


from enum import Enum
from discord.ext import commands


class ConversationState(Enum):
    NAME = 0
    AGE = 1
    GENDER = 2
    INTEREST = 3
    PROFESSION = 4
    APPEARANCE = 5
    RELATIONSHIP = 6
    MOOD = 7
    FINISHED = 8


def create_conversation_state():
    return {
        'name': None,
        'age': None,
        'gender': None,
        'interest': None,
        'profession': None,
        'appearance': None,
        'relationship': None,
        'mood': None,
        'state': ConversationState.NAME
    }


@bot.event
async def on_message(message: Message) -> None:
    author_id = message.author.id

    if message.author == bot.user:
        return
    if not isinstance(message.channel, discord.DMChannel):
        return
    if message.content.startswith('/start'):
        await start(message)
        return

    if author_id not in conversation_states:
        await message.channel.send("Please enter /start to begin.")
        return

    state = conversation_states[author_id]['state']
    if state == ConversationState.NAME:
        conversation_states[author_id]['name'] = message.content
        conversation_states[author_id]['state'] = ConversationState.AGE
        await message.channel.typing()
        await message.channel.send("What is their age?")
        return
    elif state == ConversationState.AGE:
        if not message.content.isdigit():
            await message.channel.typing()
            await message.reply("Age should be a number.\nHow old is your bot?")
        else:
            conversation_states[author_id]['age'] = message.content
            conversation_states[author_id]['state'] = ConversationState.GENDER
            await message.channel.typing()
            await message.channel.send("What gender?")
            return
    elif state == ConversationState.GENDER:
        conversation_states[author_id]['gender'] = message.content
        conversation_states[author_id]['state'] = ConversationState.INTEREST
        await message.channel.typing()
        await message.channel.send("What do they like to do for fun?")
        return
    elif state == ConversationState.INTEREST:
        conversation_states[author_id]['interest'] = message.content
        conversation_states[author_id]['state'] = ConversationState.PROFESSION
        await message.channel.typing()
        await message.channel.send("What is their profession?")
        return
    elif state == ConversationState.PROFESSION:
        conversation_states[author_id]['profession'] = message.content
        conversation_states[author_id]['state'] = ConversationState.APPEARANCE
        await message.channel.typing()
        await message.channel.send("What do they look like?")
        return
    elif state == ConversationState.APPEARANCE:
        conversation_states[author_id]['appearance'] = message.content
        conversation_states[author_id]['state'] = ConversationState.RELATIONSHIP
        await message.channel.typing()
        await message.channel.send("What is their relationship status?")
        return
    elif state == ConversationState.RELATIONSHIP:
        conversation_states[author_id]['relationship'] = message.content
        conversation_states[author_id]['state'] = ConversationState.MOOD
        await message.channel.typing()
        await message.channel.send("Thank you. Finally, describe their personality.")
        return
    elif state == ConversationState.MOOD:
        conversation_states[author_id]['mood'] = message.content
        await message.channel.typing()
        await message.channel.send("Thank you! Bot information has been added")
        await message.channel.typing()
        async with aiohttp.ClientSession() as session:
            # Example for NEW_COMPANION_ENDPOINT
            async with session.post(
                    "http://localhost:8000/api/SpeechSynthesizer/new_companion",
                    json={
                        "user_id": message.author.id,
                        "name": conversation_states[author_id].get('name', 'Not provided'),
                        "age": conversation_states[author_id].get('age', 'Not provided'),
                        "gender": conversation_states[author_id].get('gender', 'Not provided'),
                        "interest": conversation_states[author_id].get('interest', 'Not provided'),
                        "profession": conversation_states[author_id].get('profession', 'Not provided'),
                        "appearance": conversation_states[author_id].get('appearance', 'Not provided'),
                        "relationship": conversation_states[author_id].get('relationship', 'Not provided'),
                        "mood": conversation_states[author_id].get('mood', 'Not provided'),
                    },
            ) as response:
                context = await response.text()
        await message.channel.send(context)
        # Try to handle context
        await message.channel.typing()
        await message.channel.send("Thank you! Bot information has been saved. One moment...")
        await message.channel.typing()
        await message.channel.send("Lets start the conversation, can you tell me a little about yourself?")
        conversation_states[author_id]['state'] = ConversationState.FINISHED
        return

    if message.content.startswith('/debug'):
        await debug(message)
        return
    if message.content.startswith('/companions_list'):
        await companions_list(message)
        return
    if message.content.startswith('/delete_all_conversations'):
        await delete_all_conversations(message)
        return
    if message.content.startswith('/load_conversation'):
        await load_conversation(message)
        return
    if message.content.startswith('/delete_conversation'):
        await delete_conversation(message)
        return
    if message.content.startswith('/sleep'):
        await toggle_sleep(message)
        return
    async with aiohttp.ClientSession() as session:
        # Example for MESSAGE_ENDPOINT
        async with session.post(
                "http://localhost:8000/api/SpeechSynthesizer/message",
                json={"user_id": message.author.id, "content": message.content},
        ) as response:
            chatbot_response = await response.text()
    num_messages = len(chatbot_response) // MAX_MESSAGE_LENGTH
    await message.channel.typing()
    for i in range(num_messages + 1):
        await message.channel.typing()
        await message.channel.send(chatbot_response[i * MAX_MESSAGE_LENGTH: (i + 1) * MAX_MESSAGE_LENGTH])
    if ENABLE_SLEEP:
        await asyncio.sleep(len(chatbot_response) * 0.07)





if __name__ == "__main__":
    bot_token = args.discord_token
    bot.run(bot_token)