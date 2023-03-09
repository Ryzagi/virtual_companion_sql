import argparse
import asyncio
import json
import os
from pathlib import Path

import aioschedule
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import KeyboardButton
from aiogram.utils import executor

from converbot.app.bot_utils import create_conversation
from converbot.constants import PROD_ENV, DEV_ENV
from converbot.database.conversations import ConversationDB
from converbot.database.history_writer import SQLHistoryWriter
from converbot.prompt.generator import ConversationalPromptGenerator


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

HISTORY_WRITER = SQLHistoryWriter.from_config(Path(args.sql_config_path))

CONVERSATIONS = ConversationDB()
PROMPT_GENERATOR = ConversationalPromptGenerator.from_json(
    args.prompt_config_path
)

bot = Bot(token=args.telegram_token)
storage = MemoryStorage()
dispatcher = Dispatcher(bot, storage=storage)

DEFAULT_KEYBOARD = types.ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton("/start")], [KeyboardButton("/debug")]],
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
             "Let’s take a moment to describe the AI persona you want to talk to."
    )
    await bot.send_message(
        message.from_user.id,
        text="What is the name you want to give your companion?",
    )

    # Define the handler for the bot's name
    @dispatcher.message_handler(state=BotInfo.name)
    async def process_name(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data["name"] = message.text
        await BotInfo.age.set()
        await bot.send_message(message.from_user.id, text="What is their age?")

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
        await bot.send_message(message.from_user.id, text="What gender?")

    @dispatcher.message_handler(state=BotInfo.gender)
    async def process_gender(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data["gender"] = message.text
            # You can use the data dictionary here to create your bot object with the collected information
        await BotInfo.interest.set()
        await bot.send_message(
            message.from_user.id, text="What do they like to do for fun?"
        )

    @dispatcher.message_handler(state=BotInfo.interest)
    async def process_interest(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data["interest"] = message.text
        await BotInfo.profession.set()
        await bot.send_message(
            message.from_user.id, text="What is their profession?"
        )

    @dispatcher.message_handler(state=BotInfo.profession)
    async def process_profession(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data["profession"] = message.text
        await BotInfo.appearance.set()
        await bot.send_message(
            message.from_user.id, text="What do they look like?"
        )

    @dispatcher.message_handler(state=BotInfo.appearance)
    async def process_appearance(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data["appearance"] = message.text
        await BotInfo.relationship.set()
        await bot.send_message(
            message.from_user.id, text="What is their relationship status?"
        )

    @dispatcher.message_handler(state=BotInfo.relationship)
    async def process_relationship(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data["relationship"] = message.text
        await BotInfo.mood.set()
        await bot.send_message(
            message.from_user.id,
            text="Thank you. Finally, describe their personality.",
        )

    @dispatcher.message_handler(state=BotInfo.mood)
    async def process_mood(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data["mood"] = message.text
            # You can use the data dictionary here to create your bot object with the collected information
        context, tone = await show_data(message)
        await bot.send_message(message.from_user.id, text=context)
        # Try to handle context
        await state.finish()
        await bot.send_message(
            message.from_user.id,
            text="Thank you! Bot information has been saved. One moment...",
        )
        await bot.send_chat_action(
            message.from_user.id, action=types.ChatActions.TYPING
        )

        conversation = create_conversation(
            prompt=PROMPT_GENERATOR(context),
            tone=tone,
            config_path=args.model_config_path
        )
        CONVERSATIONS.add_conversation(message.from_user.id, conversation, context)
        await bot.send_message(
            message.from_user.id,
            text="Lets start the conversation, can you tell me a little about yourself?",
        )
        return None


async def show_data(message: types.Message):
    state = dispatcher.current_state(
        chat=message.chat.id, user=message.from_user.id
    )
    data = await state.get_data()

    #    res = f"Here's the information about your companion:\n\n" \
    res = (
        f"Name: {data.get('name', 'Not provided')}\n"
        f"Age: {data.get('age', 'Not provided')}\n"
        f"Gender: {data.get('gender', 'Not provided')}\n"
        f"interests: {data.get('interest', 'Not provided')}\n"
        f"Profession: {data.get('profession', 'Not provided')}\n"
        f"Appearance: {data.get('appearance', 'Not provided')}\n"
        f"Relationship status: {data.get('relationship', 'Not provided')}\n"
        f"Personality: {data.get('mood', 'Not provided')}\n"
    )
    return res, data.get("mood", "Not provided")


@dispatcher.message_handler(commands=["debug"])
async def debug(message: types.Message):
    conversation = CONVERSATIONS.get_conversation(message.from_user.id)
    if conversation is None:
        await bot.send_message(
            message.from_user.id, text="Please, provide initial context."
        )
    state = conversation.change_debug_mode()
    if state:
        await bot.send_message(
            message.from_user.id,
            text="«Debug mode on»\nPlease continue the discussion with your "
                 "companion",
        )
    else:
        await bot.send_message(
            message.from_user.id,
            text="«Debug mode off»\nPlease continue the discussion with your "
                 "companion",
        )


@dispatcher.message_handler()
@try_
async def handle_message(message: types.Message) -> None:
    # Agent side:
    if message.text.startswith("/"):
        conversation = CONVERSATIONS.get_conversation(message.from_user.id)
        tone_info = f"Information «{message.text[1:]}» has been added."
        conversation.set_tone(message.text[1:])
        # Proxy side:
        await bot.send_chat_action(
            message.from_user.id, action=types.ChatActions.TYPING
        )
        await asyncio.sleep(1)

        await bot.send_message(
            message.from_user.id,
            text=tone_info,
        )
        return None

    # Handle conversation
    await bot.send_chat_action(
        message.from_user.id, action=types.ChatActions.TYPING
    )

    conversation = CONVERSATIONS.get_conversation(message.from_user.id)
    chatbot_response = conversation.ask(message.text)

    HISTORY_WRITER.write_message(
        user_id=message.from_user.id,
        conversation_id=CONVERSATIONS.get_conversation_id(message.from_user.id),
        user_message=message.text,
        chatbot_message=chatbot_response,
        env=args.env,
    )

    await bot.send_chat_action(
        message.from_user.id, action=types.ChatActions.TYPING
    )
    await asyncio.sleep(len(chatbot_response) * 0.07)
    await bot.send_chat_action(
        message.from_user.id, action=types.ChatActions.TYPING
    )
    await bot.send_message(message.from_user.id, text=chatbot_response)


async def serialize_conversation_task():
    CONVERSATIONS.serialize_conversations()
    pass


async def scheduler():
    aioschedule.every(60).seconds.do(serialize_conversation_task)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(dispatcher):
    CONVERSATIONS.load_conversations()

    asyncio.create_task(scheduler())


def main():
    executor.start_polling(
        dispatcher, skip_updates=False, on_startup=on_startup
    )
