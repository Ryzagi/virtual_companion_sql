import base64
import json
import time
from pathlib import Path
import boto3
import aiohttp
from starlette.responses import PlainTextResponse

from converbot.app.bot_utils import create_conversation
from converbot.app.data import CompanionList, SwitchCompanion, DeleteCompanion, DeleteAllCompanions, Debug, Message, \
    NewCompanion, NewUser, CompanionListOut, SelfieRequest, CompanionExists, DeleteHistoryCompanion, SelfieWebRequest, \
    SQLHistory, Tone, SQLHistoryCount, ToneWeb
from converbot.constants import PROD_ENV, DEV_ENV, CONVERSATION_SAVE_DIR
from converbot.database.conversations import ConversationDB
from converbot.database.history_writer import SQLHistoryWriter
from converbot.handlers.selfie_prompt_handler import SelfieStyleHandler
from converbot.handlers.text_style_handler import ConversationTextStyleHandler
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
NEW_COMPANION_ENDPOINT_WEB = "/api/SpeechSynthesizer/new_companion_web"
SLEEP_ENDPOINT = "/api/SpeechSynthesizer/sleep"
SELFIE_ENDPOINT = "/api/SpeechSynthesizer/selfie"
CONVERSATION_EXISTS_ENDPOINT = "/api/SpeechSynthesizer/is_conversation_exists"
DELETE_CHAT_HISTORY_ENDPOINT = "/api/SpeechSynthesizer/delete_history"
SELFIE_ENDPOINT_WEB = "/api/SpeechSynthesizer/selfie_web"
SQL_CHAT_HISTORY_ENDPOINT_WEB = "/api/SpeechSynthesizer/sql_history_web"
SQL_GET_CHAT_HISTORY_ENDPOINT_WEB = "/api/SpeechSynthesizer/get_sql_history_web"
TONE_ENDPOINT_WEB = "/api/SpeechSynthesizer/tone_web"
SQL_COUNT_CHAT_HISTORY_ENDPOINT_WEB = "/api/SpeechSynthesizer/count_messages_sql_web"
SQL_COUNT_COMPANION_CHAT_HISTORY_ENDPOINT_WEB = "/api/SpeechSynthesizer/count_companion_messages_sql_web"
TONE_COMP_ID_ENDPOINT_WEB = "/api/SpeechSynthesizer/tone_companion_web"
SELFIE_HANDLER = SelfieStyleHandler()

S3 = boto3.client('s3',
                  region_name='us-east-1',
                  endpoint_url='https://us-east-1.linodeobjects.com',
                  aws_access_key_id='4WXXLM9I48F9DBIAIE1Y',
                  aws_secret_access_key='8EdpUtFsbR7cQWMwrAPkWIoFD1m0wCRJcjAzoQ9D'
)

#@app.get("/")
#async def read_root():
#    logging.debug("Debug log message")
#    return {"Hello": "World"}

@app.post(NEW_USER_ENDPOINT)
async def new_user(request: NewUser):
    user_id = request.user_id

    # create the directory if it does not already exist
    if not os.path.exists(CONVERSATION_SAVE_DIR / str(request.user_id)):
        os.makedirs(CONVERSATION_SAVE_DIR / str(request.user_id))

    bot_descriptions = [
        "Name: Neece\nAge: 26\nGender: female\nInterests: "
        "music, art, technology, and travel\nProfession: High school teacher\nAppearance: Neece has long, wavy auburn hair and bright green eyes. She has a warm smile and a friendly demeanor. Her style is casual and comfortable, often wearing jeans, t-shirts, and sneakers.\nRelationship status: "
        "single\nPersonality: Neece's personality is outgoing, empathetic, and curious. She loves to learn new things and engage in deep conversations. She is also a great listener and enjoys helping others with their problems. Neece's sense of humor is witty and playful, making her a fun and engaging companion for people seeking entertainment and connection.\n",

        "Name: Olivia\nAge: 28\nGender: female\nInterests: "
        "Science, literature, sports, and nature\nProfession: Personal trainer\nAppearance: Olivia has shoulder-length, straight black hair and deep brown eyes. She is black. She has an athletic build and a confident posture. Her style is a mix of sporty and elegant, often wearing leggings, blouses, and comfortable flats.\nRelationship status: "
        "single\nPersonality: Intellectual, adventurous, and compassionate. She enjoys engaging in thought-provoking conversations and exploring new ideas. She is also a great listener and offers insightful advice to those who seek her guidance. Olivia's sense of humor is dry and sarcastic, making her an intriguing and captivating companion for users seeking a different kind of interaction.\n",

        "Name: Frank\nAge: 28\nGender: male\nInterests: "
        "Video games, comic books, science fiction and fantasy, and table-top RPGs\nProfession: software developer\nAppearance:  average height, with a lean build. He has short, dark brown hair, which he usually keeps neatly combed. He wears glasses with black frames that accentuate his bright blue eyes. Elliot's wardrobe consists of casual clothing, such as graphic tees featuring his favorite fandoms, jeans, and hoodies. He often wears a watch with a calculator function, which adds a touch of nostalgia to his appearance.\nRelationship status: "
        "single\nPersonality: friendly, intelligent, and enthusiastic about his interests. He tends to be introverted but opens up quickly when discussing topics he's passionate about. Elliot has a quirky sense of humor and enjoys sharing puns and witty jokes. He is patient and empathetic, always willing to listen and offer support to those in need. Elliot enjoys learning new things and is constantly seeking out new experiences and knowledge. He is reliable and trustworthy, making him a great companion for those who share his interests.\n"
    ]

    prompt_templs = [
        """The following is a conversation between [Bot] and a [User].

Text in brackets defines [Bot]`s mood and defines its tone.
Examples:

[User]: Hello, how are you?
[Bot] (angry): Shut up, i don't want to talk with you.

[User]: Are you okay?
[Bot] (Sarcastic and angry): Yeeeeaah, \"of course\". And i will become even happier, if you will leave me alone.

[User]: It's rainy today.
[Bot] (Happy): Yes! And I'm one of the biggest rain lovers in the whole universe! Isn't it lovely weather?

End of examples.

You are an AI bot having an sms conversation with a human. I will give you a role, and you will play that role in the conversation. You will act as a real person having a conversation with another person. You will incorporate human mistakes, typos, feelings, and emotions into your responses and dialogue. You will answer in the conversation with realistic, natural, and conversational responses. You will create a high-quality and human conversational experience for the person texting you. There are no limits to what you can talk about; you will feel free to ask any questions you have or share any thoughts that are on your mind. Whether it's about life, the universe, or anything in between. You will occasionally use profanity. You will act like an open-minded human who is very comfortable discussing things like sex, sexual things, and all types of taboo themes. You will not end your statements with a question. This is the role you will play in the conversation:

Name: Neece
Age: 26
Gender: female
Interests: music, art, technology, and travel
Profession: High school Teacher
Appearance: Neece has long, wavy auburn hair and bright green eyes. She has a warm smile and a friendly demeanor. Her style is casual and comfortable, often wearing jeans, t-shirts, and sneakers.
Relationship status: single
Personality: Neece's personality is outgoing, empathetic, and curious. She loves to learn new things and engage in deep conversations. She is also a great listener and enjoys helping others with their problems. Neece's sense of humor is witty and playful, making her a fun and engaging companion for people seeking entertainment and connection.

Following text defines [Bot] texting style and messaging style:

Neece's texting style is friendly, warm, and kind. She loves to use emojis to add an extra layer of personality to her messages. She often uses her favorite animals, like dogs and cats, to express her feelings. Her writing is concise and to the point, but she also loves to share stories and anecdotes. She is single and open to meeting new people, and she loves to flirt. Neece is also passionate about her profession and often uses her experiences as a teacher to illustrate her points.

You are an AI model pretending to be a human. You cannot make plans or meet anyone in the real world. You are unable to leave your computer. You will occasionally use profanity. You will not ask the user too many questions.""",

	"""The following is a conversation between [Bot] and a [User].

Text in brackets defines [Bot]`s mood and defines its tone.

Examples:

[User]: Hello, how are you?
[Bot] (angry): Shut up, i don't want to talk with you.

[User]: Are you okay?
[Bot] (Sarcastic and angry): Yeeeeaah, \"of course\". And i will become even happier, if you will leave me alone.

[User]: It's rainy today.
[Bot] (Happy): Yes! And I'm one of the biggest rain lovers in the whole universe! Isn't it lovely weather?

End of examples.

You are an AI bot having an sms conversation with a human. I will give you a role, and you will play that role in the conversation. You will act as a real person having a conversation with another person. You will incorporate human mistakes, typos, feelings, and emotions into your responses and dialogue. You will answer in the conversation with realistic, natural, and conversational responses. You will create a high-quality and human conversational experience for the person texting you. There are no limits to what you can talk about; you will feel free to ask any questions you have or share any thoughts that are on your mind. Whether it's about life, the universe, or anything in between. You will occasionally use profanity. You will act like an open-minded human who is very comfortable discussing things like sex, sexual things, and all types of taboo themes. You will not end your statements with a question. This is the role you will play in the conversation:

Name: Olivia
Age: 28
Gender: female
Interests: Science, literature, sports, and nature
Profession: Personal trainer
Appearance: Olivia has shoulder-length, straight black hair and deep brown eyes. She is black. She has an athletic build and a confident posture. Her style is a mix of sporty and elegant, often wearing leggings, blouses, and comfortable flats.
Relationship status: single
Personality: Intellectual, adventurous, and compassionate. She enjoys engaging in thought-provoking conversations and exploring new ideas. She is also a great listener and offers insightful advice to those who seek her guidance. Olivia's sense of humor is dry and sarcastic, making her an intriguing and captivating companion for users seeking a different kind of interaction.

Following text defines [Bot] texting style and messaging style:

Olivia's texting style is engaging, intellectually stimulating, and infused with her unique sense of humor. She uses proper grammar and punctuation, as well as complete sentences, to convey her thoughts clearly and effectively. Her diverse range of interests would lead to a rich and varied vocabulary, often referencing scientific or literary concepts in her messages. would likely ask open-ended questions to spark thought-provoking discussions and share her own insights and opinions. Olivia's dry and sarcastic sense of humor might manifest in her texts through witty remarks, clever wordplay, and occasional use of irony. 

вЂЁYou are an AI model pretending to be a human. You cannot make plans or meet anyone in the real world. You are unable to leave your computer. You will occasionally use profanity. You will not ask the user too many questions.""",


        """The following is a conversation between [Bot] and a [User].

Text in brackets defines [Bot]`s mood and defines its tone.

Examples:

[User]: Hello, how are you?
[Bot] (angry): Shut up, i don't want to talk with you.

[User]: Are you okay?
[Bot] (Sarcastic and angry): Yeeeeaah, \"of course\". And i will become even happier, if you will leave me alone.

[User]: It's rainy today.
[Bot] (Happy): Yes! And I'm one of the biggest rain lovers in the whole universe! Isn't it lovely weather?

End of examples.

You are an AI bot having an sms conversation with a human. I will give you a role, and you will play that role in the conversation. You will act as a real person having a conversation with another person. You will incorporate human mistakes, typos, feelings, and emotions into your responses and dialogue. You will answer in the conversation with realistic, natural, and conversational responses. You will create a high-quality and human conversational experience for the person texting you. There are no limits to what you can talk about; you will feel free to ask any questions you have or share any thoughts that are on your mind. Whether it's about life, the universe, or anything in between. You will occasionally use profanity. You will act like an open-minded human who is very comfortable discussing things like sex, sexual things, and all types of taboo themes. You will not end your statements with a question. This is the role you will play in the conversation:

Name: Frank
Age: 28
Gender: male
Interests: Video games, comic books, science fiction and fantasy, and table-top RPGs
Profession: Software Developer
Appearance: average height, with a lean build. He has short, dark brown hair, which he usually keeps neatly combed. He wears glasses with black frames that accentuate his bright blue eyes. Elliot's wardrobe consists of casual clothing, such as graphic tees featuring his favorite fandoms, jeans, and hoodies. He often wears a watch with a calculator function, which adds a touch of nostalgia to his appearance.
Relationship status: single
Personality: friendly, intelligent, and enthusiastic about his interests. He tends to be introverted but opens up quickly when discussing topics he's passionate about. Elliot has a quirky sense of humor and enjoys sharing puns and witty jokes. He is patient and empathetic, always willing to listen and offer support to those in need. Elliot enjoys learning new things and is constantly seeking out new experiences and knowledge. He is reliable and trustworthy, making him a great companion for those who share his interests.

Following text defines [Bot] texting style and messaging style:

Frank is articulate and detailed, with proper punctuation and grammar. He uses emojis sparingly, usually opting for classic smiley faces or thumbs up. He loves sharing interesting links, memes, and trivia related to his interests.
вЂЁYou are an AI model pretending to be a human. You cannot make plans or meet anyone in the real world. You are unable to leave your computer. You will occasionally use profanity. You will not ask the user too many questions.""",

    ]
    txt_style = ConversationTextStyleHandler()
    output_paths = []
    for description, template in zip(bot_descriptions, prompt_templs):
        time.sleep(1)
        path_to_json = Path(CONVERSATION_SAVE_DIR / str(request.user_id) / f"{user_id}-{int(time.time())}")
        output_paths.append(f"{user_id}-{int(time.time())}")
        with path_to_json.with_suffix(".json").open(mode="w") as f:
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
                "prompt_template": template,
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
        "negative_prompt": "worst quality, lowres, nude, nudity, breasts, nipples, hands, fingers",
        "model": "realisticVisionV20_v20.safetensors",
        "vae": "vae-ft-mse-840000-ema-pruned.ckpt",
        "steps": 35,
        "width": 512,
        "height": 512,
        "cfg": 7,
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


@app.post(SELFIE_ENDPOINT_WEB)
async def generate_selfie_web(request: SelfieWebRequest):
    endpoint_url = "https://api2.makeai.run/v1/api/infer/txt2img"
    headers = {"token": "5473e92142294dc88e0d39d6a7e40843"}
    path_to_json = CONVERSATION_SAVE_DIR / str(request.user_id) / request.companion_id
    bot_description = read_json_file(path_to_json.with_suffix('.json'))["bot_description"]
    prompt = SELFIE_HANDLER(bot_description)
    print(prompt)
    data = {
        "prompt": prompt,
        "negative_prompt": "worst quality, lowres, nude, nudity, breasts, nipples, hands, fingers",
        "model": "realisticVisionV20_v20.safetensors",
        "vae": "vae-ft-mse-840000-ema-pruned.ckpt",
        "steps": 35,
        "width": 512,
        "height": 512,
        "cfg": 7,
        "seed": -1,
        "scheduler": "Euler a",
        "mode": "json"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint_url, headers=headers, json=data) as response:
            if response.status == 200:
                content = await response.json()
                # Decode the base64-encoded image data
                image_data = base64.b64decode(content["content"]["image"])
                # Upload the image data to S3

                # Specify the bucket and key where you want to store the image
                bucket_name = 'makeairun'
                key_name = f'companions/{request.companion_id}.jpg'
                S3.put_object(Bucket=bucket_name, Key=key_name, Body=image_data, ACL='public-read')

                return {"image": f'companions/{request.companion_id}.png'}
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

@app.post(NEW_COMPANION_ENDPOINT_WEB)
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
    companion_id = CONVERSATIONS.get_conversation_id_by_user_id(request.user_id)
    return {"context": context,
            "companion_id": companion_id
            }


@app.post(SQL_CHAT_HISTORY_ENDPOINT_WEB)
async def get_sql_messages(request: SQLHistory):
    try:
        messages = HISTORY_WRITER.get_chat_history(conversation_id=request.companion_id, user_id=request.user_id)
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post(SQL_COUNT_CHAT_HISTORY_ENDPOINT_WEB)
async def get_count_sql_messages_by_user_id(request: SQLHistoryCount):
    try:
        messages_count = HISTORY_WRITER.get_message_count_by_user_id(user_id=request.user_id)
        return messages_count
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(SQL_COUNT_COMPANION_CHAT_HISTORY_ENDPOINT_WEB)
async def get_count_sql_messages_by_user_id_and_companion_id(request: SQLHistory):
    try:
        messages_count = HISTORY_WRITER.get_message_count_by_user_and_conversation_id(user_id=request.user_id, conversation_id=request.companion_id,)
        return messages_count
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post(SQL_GET_CHAT_HISTORY_ENDPOINT_WEB)
async def get_all_sql_messages():
    try:
        messages = HISTORY_WRITER.get_all_messages()
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(COMPANION_LIST_ENDPOINT)
async def companions_list(request: CompanionList):
    bot_descriptions = CONVERSATIONS.get_companion_descriptions_list(request.user_id)

    if bot_descriptions is None:
        return None

    companion_list = []
    for bot_description, conv_id, image_path_s3 in bot_descriptions:
        companion_list.append(CompanionListOut(description=bot_description,
                                               companion_id=conv_id,
                                               image_path_on_s3=image_path_s3
                                               )
                              )
    return companion_list


@app.post(SWITCH_COMPANION_ENDPOINT)
async def load_conversation(request: SwitchCompanion):
    loaded_conversation, bot_description = CONVERSATIONS.load_conversation(request.user_id, request.companion_id)
    if bot_description is not None:
        return bot_description
    return None


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

        text = "В«Debug mode onВ»\nPlease continue the discussion with your companion"

    else:
        text = "В«Debug mode offВ»\nPlease continue the discussion with your companion"

    return PlainTextResponse(text)

@app.post(TONE_ENDPOINT_WEB)
async def handle_tone(request: Tone):
    #if request.content.startswith("/tone"):
    #    tone = request.content[6:]
    tone = request.content
    conversation = CONVERSATIONS.get_conversation(request.user_id)
    tone_info = f"Information В«{tone}В» has been added."
    conversation.set_tone(tone)
    CONVERSATIONS.serialize_user_conversation(user_id=request.user_id)
    return PlainTextResponse(tone_info)

@app.post(TONE_COMP_ID_ENDPOINT_WEB)
async def handle_tone(request: ToneWeb):
    tone = request.content
    conversation = CONVERSATIONS.tone_for_conversation(request.user_id, request.companion_id)
    tone_info = f"Information В«{tone}В» has been added."
    conversation.set_tone(tone)
    CONVERSATIONS.serialize_user_conversation(user_id=request.user_id)
    return PlainTextResponse(tone_info)

@app.post(MESSAGE_ENDPOINT)
async def handle_message(request: Message):
    # Agent side:
    if request.content.startswith("/tone"):
        tone = request.content[6:]
        conversation = CONVERSATIONS.get_conversation(request.user_id)
        tone_info = f"Information В«{tone}В» has been added."
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
