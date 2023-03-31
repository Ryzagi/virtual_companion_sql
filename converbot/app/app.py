import argparse
import asyncio
import base64
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
from starlette.responses import PlainTextResponse

from converbot.app.bot_utils import create_conversation
from converbot.app.data import CompanionList, SwitchCompanion, DeleteCompanion, DeleteAllCompanions, Debug, Message, \
    NewCompanion, NewUser, CompanionListOut, SelfieRequest
from converbot.constants import PROD_ENV, DEV_ENV, CONVERSATION_SAVE_DIR
from converbot.database.conversations import ConversationDB
from converbot.database.history_writer import SQLHistoryWriter
from converbot.handlers.selfie_prompt_handler import SelfieStyleHandler
from converbot.prompt.generator import ConversationalPromptGenerator
from fastapi import FastAPI, Response, status, HTTPException
import os

from converbot.utils.utils import read_json_file

ENABLE_SLEEP = True
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
SLEEP_ENDPOINT = "/api/SpeechSynthesizer/sleep"
SELFIE_ENDPOINT = "/api/SpeechSynthesizer/selfie"

SELFIE_HANDLER = SelfieStyleHandler()


@app.post(NEW_USER_ENDPOINT)
async def new_user(request: NewUser):
    pass


@app.post(SELFIE_ENDPOINT)
async def generate_selfie(request: SelfieRequest):
    endpoint_url = "https://api2.makeai.run/v1/api/infer/txt2img"
    headers = {"token": "92d20745-f419-43f8-92be-d6c3724b2c63"}
    conv_id = Path(CONVERSATIONS.get_conversation_id(request.user_id)).with_suffix('.json')
    path_to_json = CONVERSATION_SAVE_DIR / str(request.user_id) / conv_id
    bot_description = read_json_file(path_to_json)["bot_description"]
    prompt = SELFIE_HANDLER(bot_description)
    print(prompt)
    data = {
        "prompt": prompt,
        "negative_prompt": "worst quality, lowres",
        "model": "realisticVisionV20_v20.safetensors",
        "vae": "vae-ft-mse-840000-ema-pruned.ckpt",
        "loras": [{"name": "", "strength": 0.0}],
        "embeddings": [{"name": "", "type": "positive", "strength": 0.0}],
        "steps": 25,
        "width": 512,
        "height": 512,
        "cfg": 11,
        "seed": -1,
        "scheduler": "Euler a",
        "mode": "json"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint_url, headers=headers, json=data) as response:
            if response.status == 200:
                content = await response.json()
                return {"image": content["content"]["image"]}
            else:
                raise HTTPException(status_code=response.status, detail=response.reason)


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
        f"Name: {name}\n"
        f"Age: {age}\n"
        f"Gender: {gender}\n"
        f"Interests: {interest}\n"
        f"Profession: {profession}\n"
        f"Appearance: {appearance}\n"
        f"Relationship status: {relationship}\n"
        f"Personality: {mood}\n"
    )
    intro = f"This is the role you will play in the conversation:\n\n"
    conversation = create_conversation(
        prompt=PROMPT_GENERATOR(intro + context),
        tone=mood,
        config_path=Path(os.environ.get('MODEL_CONFIG_PATH'))
    )
    CONVERSATIONS.add_conversation(user_id, conversation, context)
    CONVERSATIONS.serialize_conversations()
    #CONVERSATIONS.serialize_user_conversation(user_id=request.user_id)
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

#@app.post(SLEEP_ENDPOINT)
#async def toggle_sleep(request: Message) -> None:
#    global ENABLE_SLEEP
#    enable_sleep = not ENABLE_SLEEP
#    text=f"Sleep functionality {'enabled' if enable_sleep else 'disabled'}"
#    return PlainTextResponse(text)


@app.post(MESSAGE_ENDPOINT)
# TODO: TRY func
async def handle_message(request: Message):
    # Agent side:
    if request.content.startswith("/tone"):
        tone = request.content[6:]
        conversation = CONVERSATIONS.get_conversation(request.user_id)
        tone_info = f"Information «{tone}» has been added."
        conversation.set_tone(tone)

        return PlainTextResponse(tone_info)

    conversation = CONVERSATIONS.get_conversation(request.user_id)
    chatbot_response = conversation.ask(request.content)
    HISTORY_WRITER.write_message(
        user_id=request.user_id,
        conversation_id=CONVERSATIONS.get_conversation_id(request.user_id),
        user_message=request.content,
        chatbot_message=chatbot_response,
        env=os.environ.get('ENVIRONMENT'),
    )
    #CONVERSATIONS.serialize_user_conversation(user_id=request.user_id)
    CONVERSATIONS.serialize_conversations()
    return PlainTextResponse(chatbot_response)


