import json
import time
from pathlib import Path

import aiohttp
from starlette.responses import PlainTextResponse

from converbot.app.bot_utils import create_conversation
from converbot.app.data import CompanionList, SwitchCompanion, DeleteCompanion, DeleteAllCompanions, Debug, Message, \
    NewCompanion, NewUser, CompanionListOut, SelfieRequest, CompanionExists, DeleteHistoryCompanion
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
CONVERSATION_EXISTS_ENDPOINT = "/api/SpeechSynthesizer/is_conversation_exists"
DELETE_CHAT_HISTORY_ENDPOINT = "/api/SpeechSynthesizer/delete_history"
SELFIE_HANDLER = SelfieStyleHandler()


@app.post(NEW_USER_ENDPOINT)
async def new_user(request: NewUser):
    user_id = request.user_id

    # create the directory if it does not already exist
    if not os.path.exists(CONVERSATION_SAVE_DIR / str(request.user_id)):
        os.makedirs(CONVERSATION_SAVE_DIR / str(request.user_id))

    bot_descriptions = ["Here's the information about your companion:\nName: Neece\nAge: 26\nGender: female\nInterests: "
                        "dogs and cats\nProfession: teacher\nAppearance: beautiful\nRelationship status: "
                        "single\nPersonality: kind\n",

                        "Here's the information about your companion:\nName: Olivia\nAge: 27\nGender: female\nInterests: "
                        "hiking\nProfession: dancer\nAppearance: beautiful\nRelationship status: "
                        "married\nPersonality: kind\n",

                        "Here's the information about your companion:\nName: Frank\nAge: 29\nGender: male\nInterests: "
                        "programming robots\nProfession: software developer\nAppearance: handsome\nRelationship status: "
                        "single\nPersonality: kind\n"
                        ]
    output_paths = []
    for description in bot_descriptions:
        time.sleep(1)
        path_to_json = Path(CONVERSATION_SAVE_DIR / str(request.user_id)/f"{user_id}-{int(time.time())}").with_suffix(".json")
        output_paths.append(f"{user_id}-{int(time.time())}")
        with path_to_json.open(mode="w") as f:
            json.dump({"config": {
                "model": "text-davinci-003",
                "max_tokens": 256,
                "temperature": 0.9,
                "top_p": 1,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "best_of": 1,
                "tone": "Nice, warm and polite",
                "summary_buffer_memory_max_token_limit": 1000
            },
                "prompt_template": "The following is a conversation between [Bot] and a [User].\n\nText in brackets "
                                   "defines [Bot]`s mood and defines its tone.\n\nExamples:\n\n[User]: Hello, "
                                   "how are you?\n[Bot] (angry): Shut up, i don't want to talk with you.\n\n[User]: Are "
                                   "you okay?\n[Bot] (Sarcastic and angry): Yeeeeaah, \"of course\". And i will become "
                                   "even happier, if you will leave me alone.\n\n[User]: It's rainy today.\n[Bot] ("
                                   "Happy): Yes! And I'm one of the biggest rain lovers in the whole universe! Isn't it "
                                   "lovely weather?\n\nEnd of examples.\n\nYou are an AI bot having an sms conversation "
                                   "with a human. I will give you a role, and you will play that role in the "
                                   "conversation. You will act as a real person having a conversation with another "
                                   "person. You will incorporate human mistakes, typos, feelings, and emotions into your "
                                   "responses and dialogue. You will answer in the conversation with realistic, natural, "
                                   "and conversational responses. You will create a high-quality and human conversational "
                                   "experience for the person texting you. There are no limits to what you can talk "
                                   "about; you will feel free to ask any questions you have or share any thoughts that "
                                   "are on your mind. Whether it's about life, the universe, or anything in between. You "
                                   "will occasionally use profanity. You will act like an open-minded human who is very "
                                   "comfortable discussing things like sex, sexual things, and all types of taboo themes. "
                                   "You will not end your statements with a question.\nHere's the information about your "
                                   "companion:\nName: artem\nAge: 29\nGender: male\nInterests: programming\nProfession: "
                                   "dancer\nAppearance: handsome\nRelationship status: free\nPersonality: "
                                   "kind\n\n\nFollowing text defines [Bot] texting style and messaging style:\nArtem's "
                                   "texting style is friendly and easygoing. He loves to use emojis, GIFs, and memes to "
                                   "bring humor and fun to his messages. He's not afraid to use slang and abbreviations, "
                                   "but he also likes to use proper grammar and punctuation. He is direct and honest when "
                                   "communicating, but he also has a gentle and kind nature. Artem is single and open to "
                                   "meeting new people. He is interested in meaningful conversations, but he also loves "
                                   "to joke around and have fun.\n\nYou are an AI model pretending to be a human. You "
                                   "cannot make plans or meet anyone in the real world. You are unable to leave your "
                                   "computer.\n\nConversation:\n[Bot]: Lets start the conversation, can you tell me a "
                                   "little about yourself?",
                "prompt_user_name": "[User]",
                "prompt_chatbot_name": "[Bot]",
                "memory_buffer": [],
                "memory_moving_summary_buffer": "",
                "bot_description": description
            }, f, indent=4)
    return output_paths


@app.post(DELETE_CHAT_HISTORY_ENDPOINT)
async def delete_chat_history(request: DeleteHistoryCompanion):
    deleted_conversation = CONVERSATIONS.delete_conversation_history(request.user_id, request.companion_id)
    return PlainTextResponse(deleted_conversation)

@app.get(CONVERSATION_EXISTS_ENDPOINT)
async def is_conversation_exists(request: CompanionExists):
    conversation = CONVERSATIONS.get_conversation(request.user_id)
    exists = True
    if conversation is None:
        exists = False
    return {"exists": exists}


@app.post(SELFIE_ENDPOINT)
async def generate_selfie(request: SelfieRequest):
    endpoint_url = "https://api2.makeai.run/v1/api/infer/txt2img"
    headers = {"token": "5473e92142294dc88e0d39d6a7e40843"}
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
    CONVERSATIONS.serialize_user_conversation(user_id=request.user_id)
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
async def handle_message(request: Message):
    # Agent side:
    if request.content.startswith("/tone"):
        tone = request.content[6:]
        conversation = CONVERSATIONS.get_conversation(request.user_id)
        tone_info = f"Information «{tone}» has been added."
        conversation.set_tone(tone)

        return PlainTextResponse(tone_info)

    conversation = CONVERSATIONS.get_conversation(request.user_id)
    if conversation is None:
        return Response(status_code=status.HTTP_406_NOT_ACCEPTABLE)
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
