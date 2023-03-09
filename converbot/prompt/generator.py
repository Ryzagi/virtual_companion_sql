import json
from pathlib import Path

from converbot.constants import DEFAULT_CHATBOT_NAME, DEFAULT_USER_NAME
from converbot.handlers.context_handler import ConversationBotContextHandler
from converbot.handlers.text_style_handler import ConversationTextStyleHandler
from converbot.prompt.prompt import ConversationPrompt


class ConversationalPromptGenerator:
    """
    The conversational prompt generator.

    Args:
        user_name: The user name.
        chatbot_name: The chatbot name.
        prompt_start_text: The start text for the prompt.
        style_definition_text: The style definition text for the prompt.
        welcoming_text: The welcoming text for the prompt.
    """

    def __init__(
        self,
        prompt_start_text: str,
        style_definition_text: str,
        welcoming_text: str,
        user_name: str = DEFAULT_USER_NAME,
        chatbot_name: str = DEFAULT_CHATBOT_NAME,
    ) -> None:
        self._text_style_handler = ConversationTextStyleHandler()
        self._context_handler = ConversationBotContextHandler()

        self._user_name = user_name
        self._chatbot_name = chatbot_name
        self._prompt_start_text = prompt_start_text
        self._style_definition_text = style_definition_text
        self._welcoming_text = welcoming_text

    @classmethod
    def from_json(cls, file_path: Path) -> "ConversationalPromptGenerator":
        """
        Load the configuration from a json file.
        Args:
            file_path: The path to load the configuration.
        """
        data = json.loads(file_path.read_text())
        return cls(**data)

    def __call__(self, context: str) -> ConversationPrompt:

        text_style = self._text_style_handler(context)
        context_summary = self._context_handler(context)

        return ConversationPrompt(
            prompt_text=(
                self._prompt_start_text
                + context_summary
                + self._style_definition_text
                + text_style
                + self._welcoming_text
            ),
            user_name=self._user_name,
            chatbot_name=self._chatbot_name,
        )
