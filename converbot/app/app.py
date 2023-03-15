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
from starlette.responses import PlainTextResponse

from converbot.app.bot_utils import create_conversation
from converbot.app.data import CompanionList, SwitchCompanion, DeleteCompanion, DeleteAllCompanions, Debug, Message, \
    NewCompanion, NewUser, CompanionListOut
from converbot.constants import PROD_ENV, DEV_ENV
from converbot.database.conversations import ConversationDB
from converbot.database.history_writer import SQLHistoryWriter
from converbot.prompt.generator import ConversationalPromptGenerator
from fastapi import FastAPI, Response, status
import os


app = FastAPI()


os.environ['SQL_CONFIG_PATH'] = '../../configs/sql_config_prod.json'
os.environ['MODEL_CONFIG_PATH'] = '../../configs/model_config.json'
os.environ['PROMPT_CONFIG_PATH'] = '../../configs/prompt_config.json'
os.environ['ENVIRONMENT'] = 'dev'

HISTORY_WRITER = SQLHistoryWriter.from_config(Path(os.environ.get('SQL_CONFIG_PATH')))

CONVERSATIONS = ConversationDB()
CONVERSATIONS.load_conversations()

PROMPT_GENERATOR = ConversationalPromptGenerator.from_json(
    Path(os.environ.get('PROMPT_CONFIG_PATH'))
)

COMPANION_LIST_ENDPOINT = "/api/SpeechSynthesizer/list_companion"
SWITCH_COMPANION_ENDPOINT = "/api/SpeechSynthesizer/switch_companion"
DELETE_COMPANION_ENDPOINT = "/api/SpeechSynthesizer/delete_companion"
DELETE_ALL_COMPANIONS_ENDPOINT = "/api/SpeechSynthesizer/delete_all_companions"
MESSAGE_ENDPOINT = "/api/SpeechSynthesizer/message"
DEBUG_ENDPOINT = "/api/SpeechSynthesizer/debug"
NEW_USER_ENDPOINT = "/api/SpeechSynthesizer/new_user"
NEW_COMPANION_ENDPOINT = "/api/SpeechSynthesizer/new_companion"


@app.post(NEW_USER_ENDPOINT)
async def new_user(request: NewUser):
    pass


@app.post(NEW_COMPANION_ENDPOINT)
async def new_companion(request: NewCompanion):
    user_id = request.user_id
    name = request.name
    age = request.age
    gender = request.gender
    interest = request.interest
    profession = request.profession
    appearance = request.appearance
    relationship = request.relationship
    mood = request.mood

    context = (
        f"Here's the information about your companion:\n"
        f"Name: {name}\n"
        f"Age: {age}\n"
        f"Gender: {gender}\n"
        f"Interests: {interest}\n"
        f"Profession: {profession}\n"
        f"Appearance: {appearance}\n"
        f"Relationship status: {relationship}\n"
        f"Personality: {mood}\n"
    )
    conversation = create_conversation(
        prompt=PROMPT_GENERATOR(context),
        tone=mood,
        config_path=Path(os.environ.get('MODEL_CONFIG_PATH'))
    )
    CONVERSATIONS.add_conversation(user_id, conversation, context)
    return PlainTextResponse(context)


@app.post(COMPANION_LIST_ENDPOINT)
async def companions_list(request: CompanionList):
    bot_descriptions = CONVERSATIONS.get_companion_descriptions_list(request.user_id)

    if bot_descriptions is None:
        return None

    companion_list = []
    for bot_description, conv_id in bot_descriptions:
        companion_list.append(CompanionListOut(description=bot_description, companion_id=conv_id))
    return companion_list


@app.post(SWITCH_COMPANION_ENDPOINT)
async def load_conversation(request: SwitchCompanion):
    loaded_conversation = CONVERSATIONS.load_conversation(request.user_id, request.companion_id)

    return PlainTextResponse(loaded_conversation)


@app.post(DELETE_COMPANION_ENDPOINT)
async def delete_conversation(request: DeleteCompanion):
    deleted_conversation = CONVERSATIONS.delete_conversation(request.user_id, request.companion_id)

    return PlainTextResponse(deleted_conversation)


@app.post(DELETE_ALL_COMPANIONS_ENDPOINT)
async def delete_all_conversations(request: DeleteAllCompanions):
    deleted_all_conversations = CONVERSATIONS.delete_all_conversations_by_user_id(request.user_id)

    return PlainTextResponse(deleted_all_conversations)


@app.post(DEBUG_ENDPOINT)
async def debug(request: Debug):
    conversation = CONVERSATIONS.get_conversation(request.user_id)
    if conversation is None:
        return Response(status_code=status.HTTP_406_NOT_ACCEPTABLE)
    state = conversation.change_debug_mode()
    if state:

        text = "«Debug mode on»\nPlease continue the discussion with your companion"

    else:
        text = "«Debug mode off»\nPlease continue the discussion with your companion"

    return PlainTextResponse(text)


@app.post(MESSAGE_ENDPOINT)
# TODO: TRY func
async def handle_message(request: Message):
    # Agent side:
    if request.content.startswith("/"):
        conversation = CONVERSATIONS.get_conversation(request.user_id)
        tone_info = f"Information «{request.content[1:]}» has been added."
        conversation.set_tone(request.content[1:])

        return tone_info

    conversation = CONVERSATIONS.get_conversation(request.user_id)
    chatbot_response = conversation.ask(request.content)

    HISTORY_WRITER.write_message(
        user_id=request.user_id,
        conversation_id=CONVERSATIONS.get_conversation_id(request.user_id),
        user_message=request.content,
        chatbot_message=chatbot_response,
        env=os.environ.get('ENVIRONMENT'),
    )
    CONVERSATIONS.serialize_user_conversation(user_id=request.user_id)

    return PlainTextResponse(chatbot_response)


