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

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--telegram_token", help="Telegram bot token", type=str, required=True
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

bot = Bot(token=args.telegram_token)
storage = MemoryStorage()
dispatcher = Dispatcher(bot, storage=storage)

ENABLE_SLEEP =True

DEFAULT_KEYBOARD = types.ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton("/start")], [KeyboardButton("/debug")], [KeyboardButton("/companions_list")]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

IS_DEBUG = False


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
            await bot.send_message(
                message.from_user.id,
                "\nPlease, try again later, We are currently under heavy load",
            )
        else:
            await bot.send_message(
                message.from_user.id,
                '\nSomething went wrong, please type "/start" to start over',
            )
        return None

    return try_except


@dispatcher.message_handler(commands=["start"])
@try_
async def start(message: types.Message):
    """
    This handler will be called when user sends /start command
    """

    # Define the states for the conversation
    class BotInfo(StatesGroup):
        name = State()
        age = State()
        gender = State()
        interest = State()
        profession = State()
        appearance = State()
        relationship = State()
        mood = State()

    # Set the initial state to 'name'
    await BotInfo.name.set()

    # Ask for the bot's name
    await bot.send_message(
        message.from_user.id,
        text="Welcome to Neece.ai\n"
             "Let’s take a moment to describe the AI persona you want to talk to.",
        reply_markup=DEFAULT_KEYBOARD
    )
    await bot.send_message(
        message.from_user.id,
        text="What is the name you want to give your companion?",
        reply_markup=DEFAULT_KEYBOARD
    )

    # Define the handler for the bot's name
    @dispatcher.message_handler(state=BotInfo.name)
    async def process_name(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data["name"] = message.text
        await BotInfo.age.set()
        await bot.send_message(message.from_user.id, text="What is their age?", reply_markup=DEFAULT_KEYBOARD)

    @dispatcher.message_handler(
        state=BotInfo.age, content_types=types.ContentTypes.TEXT
    )
    async def process_age(message: types.Message, state: FSMContext):
        if not message.text.isdigit():
            return await message.reply(
                "Age should be a number.\nHow old is your bot?"
            )
        async with state.proxy() as data:
            data["age"] = message.text
        await BotInfo.gender.set()
        await bot.send_message(message.from_user.id, text="What gender?", reply_markup=DEFAULT_KEYBOARD)

    @dispatcher.message_handler(state=BotInfo.gender)
    async def process_gender(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data["gender"] = message.text
            # You can use the data dictionary here to create your bot object with the collected information
        await BotInfo.interest.set()
        await bot.send_message(
            message.from_user.id, text="What do they like to do for fun?", reply_markup=DEFAULT_KEYBOARD
        )

    @dispatcher.message_handler(state=BotInfo.interest)
    async def process_interest(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data["interest"] = message.text
        await BotInfo.profession.set()
        await bot.send_message(
            message.from_user.id, text="What is their profession?", reply_markup=DEFAULT_KEYBOARD
        )

    @dispatcher.message_handler(state=BotInfo.profession)
    async def process_profession(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data["profession"] = message.text
        await BotInfo.appearance.set()
        await bot.send_message(
            message.from_user.id, text="What do they look like?", reply_markup=DEFAULT_KEYBOARD
        )

    @dispatcher.message_handler(state=BotInfo.appearance)
    async def process_appearance(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data["appearance"] = message.text
        await BotInfo.relationship.set()
        await bot.send_message(
            message.from_user.id, text="What is their relationship status?", reply_markup=DEFAULT_KEYBOARD
        )

    @dispatcher.message_handler(state=BotInfo.relationship)
    async def process_relationship(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data["relationship"] = message.text
        await BotInfo.mood.set()
        await bot.send_message(
            message.from_user.id,
            text="Thank you. Finally, describe their personality.", reply_markup=DEFAULT_KEYBOARD
        )

    @dispatcher.message_handler(state=BotInfo.mood)
    async def process_mood(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data["mood"] = message.text
            # You can use the data dictionary here to create your bot object with the collected information

        state = dispatcher.current_state(
            chat=message.chat.id, user=message.from_user.id
        )
        data = await state.get_data()

        async with aiohttp.ClientSession() as session:
            # Example for NEW_COMPANION_ENDPOINT
            async with session.post(
                    "http://localhost:8000/api/SpeechSynthesizer/new_companion",
                    json={
                        "user_id": message.from_user.id,
                        "name": data.get('name', 'Not provided'),
                        "age": data.get('age', 'Not provided'),
                        "gender": data.get('gender', 'Not provided'),
                        "interest": data.get('interest', 'Not provided'),
                        "profession": data.get('profession', 'Not provided'),
                        "appearance": data.get('appearance', 'Not provided'),
                        "relationship": data.get('relationship', 'Not provided'),
                        "mood": data.get('mood', 'Not provided'),
                    },
            ) as response:
                context = await response.text()
        await bot.send_message(message.from_user.id, text=context, reply_markup=DEFAULT_KEYBOARD)
        # Try to handle context
        await state.finish()
        await bot.send_message(
            message.from_user.id,
            text="Thank you! Bot information has been saved. One moment...", reply_markup=DEFAULT_KEYBOARD
        )
        await bot.send_chat_action(
            message.from_user.id, action=types.ChatActions.TYPING
        )

        await bot.send_message(
            message.from_user.id,
            text="Lets start the conversation, can you tell me a little about yourself?", reply_markup=DEFAULT_KEYBOARD
        )
        return None


@dispatcher.message_handler(commands=["companions_list"])
async def companions_list(message: types.Message):
    # Example for COMPANION_LIST_ENDPOINT
    async with aiohttp.ClientSession() as session:
        async with session.post(
                "http://localhost:8000/api/SpeechSynthesizer/list_companion",
                json={"user_id": message.from_user.id},
        ) as response:
            bot_descriptions = await response.json()

    if bot_descriptions is None:
        await bot.send_message(
            message.from_user.id,
            text="You haven`t any conversations!\nPlease, /start new conversation with me!",
        )
        return None

    bot_description_output = []
    for companion_info in bot_descriptions:
        bot_description = f"Conversation ID #{companion_info['companion_id']}:\n\n{companion_info['description']}"
        bot_description_output.append(bot_description)

    message_bot_descriptions = "\n\n".join(bot_description_output)

    await bot.send_message(
        message.from_user.id,
        text=message_bot_descriptions
    )


@dispatcher.message_handler(commands=["load_conversation"])
async def load_conversation(message: types.Message):
    conv_id = message.text.split(" ")[-1]
    # loaded_conversation = CONVERSATIONS.load_conversation(message.from_user.id, conv_id)

    async with aiohttp.ClientSession() as session:
        # Example for SWITCH_COMPANION_ENDPOINT
        async with session.post(
                "http://localhost:8000/api/SpeechSynthesizer/switch_companion",
                json={"user_id": message.from_user.id, "companion_id": conv_id},
        ) as response:
            loaded_conversation = await response.text()

    await bot.send_message(
        message.from_user.id,
        text=loaded_conversation
    )

    await bot.send_message(
        message.from_user.id,
        text="Hi there! It's nice to meet you again.",
    )


@dispatcher.message_handler(commands=["delete_conversation"])
async def delete_conversation(message: types.Message):
    conv_id = message.text.split(" ")[-1]
    # deleted_conversation = CONVERSATIONS.delete_conversation(message.from_user.id, conv_id)
    async with aiohttp.ClientSession() as session:
        # Example for DELETE_COMPANION_ENDPOINT
        async with session.post(
                "http://localhost:8000/api/SpeechSynthesizer/delete_companion",
                json={"user_id": message.from_user.id, "companion_id": conv_id},
        ) as response:
            deleted_conversation = await response.text()

    await bot.send_message(
        message.from_user.id,
        text=deleted_conversation,
    )


@dispatcher.message_handler(commands=["delete_all_conversations"])
async def delete_all_conversations(message: types.Message):
    # deleted_all_conversations = CONVERSATIONS.delete_all_conversations_by_user_id(message.from_user.id)
    async with aiohttp.ClientSession() as session:
        # Example for DELETE_ALL_COMPANIONS_ENDPOINT
        async with session.post(
                "http://localhost:8000/api/SpeechSynthesizer/delete_all_companions",
                json={"user_id": message.from_user.id},
        ) as response:
            deleted_all_conversations = await response.text()

    await bot.send_message(
        message.from_user.id,
        text=deleted_all_conversations,
    )
    await bot.send_message(
        message.from_user.id,
        text="Please, /start new conversation with me!",
    )


@dispatcher.message_handler(commands=["debug"])
async def debug(message: types.Message):
    # conversation = CONVERSATIONS.get_conversation(message.from_user.id)
    async with aiohttp.ClientSession() as session:
        # Example for DEBUG_ENDPOINT
        async with session.post(
                "http://localhost:8000/api/SpeechSynthesizer/debug",
                json={"user_id": message.from_user.id},
        ) as response:
            conversation = await response.text()
            status_code = response.status

    if status_code == 406:
        await bot.send_message(
            message.from_user.id, text="Please, provide initial context."
        )

    await bot.send_message(
        message.from_user.id, text=conversation
    )

@dispatcher.message_handler(commands=["sleep"])
async def toggle_sleep(message: types.Message) -> None:
    #async with session.post(
    #        "http://localhost:8000/api/SpeechSynthesizer/sleep",
    #        json={"user_id": message.from_user.id},
    #) as response:
    #    mode = await response.text()
    global ENABLE_SLEEP

    ENABLE_SLEEP = not ENABLE_SLEEP
    await bot.send_message(
        message.from_user.id, text=f"Sleep functionality {'enabled' if ENABLE_SLEEP else 'disabled'}"
    )

@dispatcher.message_handler()
@try_
async def handle_message(message: types.Message) -> None:
    async with aiohttp.ClientSession() as session:
        # Example for MESSAGE_ENDPOINT
        async with session.post(
                "http://localhost:8000/api/SpeechSynthesizer/message",
                json={"user_id": message.from_user.id, "content": message.text},
        ) as response:
            chatbot_response = await response.text()
    num_messages = len(chatbot_response) // 4000

    await bot.send_chat_action(
        message.from_user.id, action=types.ChatActions.TYPING
    )
    if ENABLE_SLEEP:
        await asyncio.sleep(len(chatbot_response) * 0.07)
    await bot.send_chat_action(
        message.from_user.id, action=types.ChatActions.TYPING
    )
    for i in range(num_messages):
        await bot.send_message(
            message.from_user.id,
            text=chatbot_response[i * 4000: (i + 1) * 4000],
        )

    #await bot.send_message(message.from_user.id, text=chatbot_response, reply_markup=DEFAULT_KEYBOARD)


async def serialize_conversation_task():
    # CONVERSATIONS.serialize_conversations()
    pass


async def scheduler():
    aioschedule.every(60).seconds.do(serialize_conversation_task)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(dispatcher):
    asyncio.create_task(scheduler())


def main():
    executor.start_polling(
        dispatcher, skip_updates=False, on_startup=on_startup
    )
