from langchain import PromptTemplate


class ConversationPrompt:
    memory_key = "chat_history"
    user_input_key = "user_input"
    conversation_tone_key = "conversation_tone"

    def __init__(
        self,
        prompt_text: str,
        user_name: str = "Man",
        chatbot_name: str = "You",
    ):
        self._prompt_text = prompt_text

        string_base_template = """PROMPT_TEXT
{chat_history}
USER_NAME: {user_input}
CHATBOT_NAME ({conversation_tone}):"""
        string_base_template = string_base_template.replace(
            "PROMPT_TEXT", prompt_text
        )
        string_base_template = string_base_template.replace(
            "USER_NAME", user_name
        )
        string_base_template = string_base_template.replace(
            "CHATBOT_NAME", chatbot_name
        )

        self._prompt = PromptTemplate(
            input_variables=["chat_history", "user_input", "conversation_tone"],
            template=string_base_template,
        )

        self._user_name = user_name
        self._chatbot_name = chatbot_name

    @property
    def original_prompt_text(self) -> str:
        return self._prompt_text

    @property
    def prompt(self) -> PromptTemplate:
        return self._prompt

    @property
    def chatbot_name(self) -> str:
        return self._chatbot_name

    @property
    def user_name(self) -> str:
        return self._user_name
