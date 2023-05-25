from pathlib import Path
from typing import List

from langchain import LLMChain
from langchain.callbacks.base import CallbackManager
from langchain.chains.conversation.memory import \
    ConversationSummaryBufferMemory
from langchain.llms import OpenAI

from converbot.callbacks import DebugPromptCallback
from converbot.config.gptconversation import GPT3ConversationConfig
from converbot.constants import DEFAULT_CONFIG_PATH, DEFAULT_FRIENDLY_TONE
from converbot.handlers.mood_handler import ConversationToneHandler
from converbot.prompt.prompt import ConversationPrompt
from converbot.serialization.checkpoint import GPT3ConversationCheckpoint


class GPT3Conversation:
    """
    A conversation with a GPT-3 chatbot.

    Args:
        prompt: The prompt for the conversation.
        model_config: The configuration for the GPT-3 model.
        verbose: Whether to print verbose output.
    """

    def __init__(
        self,
        prompt: ConversationPrompt,
        model_config: GPT3ConversationConfig = GPT3ConversationConfig(),
        verbose: bool = False,
    ):
        self._config = model_config
        self._prompt = prompt
        self._language_model = OpenAI(
            model_name=model_config.model,
            temperature=model_config.temperature,
            max_tokens=model_config.max_tokens,
            top_p=model_config.top_p,
            frequency_penalty=model_config.frequency_penalty,
            presence_penalty=model_config.presence_penalty,
            best_of=model_config.best_of,
            stop=["\nUser:"]
        )

        self._memory = ConversationSummaryBufferMemory(
            llm=self._language_model,
            max_token_limit=model_config.summary_buffer_memory_max_token_limit,
            input_key=self._prompt.user_input_key,
            memory_key=self._prompt.memory_key,
            human_prefix=self._prompt.user_name,
            ai_prefix=self._prompt.chatbot_name,
        )

        self._debug_callback = DebugPromptCallback()
        self._conversation = LLMChain(
            llm=self._language_model,
            memory=self._memory,
            prompt=self._prompt.prompt,
            verbose=verbose,
            callback_manager=CallbackManager([self._debug_callback]),
        )

        self._tone_processor = ConversationToneHandler()
        self._debug = False

    @classmethod
    def from_config_file(
        cls,
        prompt: ConversationPrompt,
        config_path: Path = DEFAULT_CONFIG_PATH,
        verbose: bool = False,
    ) -> "GPT3Conversation":
        """
        Load the conversation from a configuration file.

        Args:
            prompt: The prompt for the conversation.
            config_path: The path to the configuration file.
            verbose: Whether to print verbose output.

        Returns: The conversation.
        """
        config = GPT3ConversationConfig.from_json(config_path)
        return cls(
            prompt=prompt,
            model_config=config,
            verbose=verbose,
        )

    def change_debug_mode(self):
        self._debug = not self._debug
        return self._debug

    def set_tone(self, tone: str) -> None:
        """
        Set the tone of the chatbot.

        Args:
            tone: The tone of the chatbot.

        Returns: None
        """
        self._config.tone = self._tone_processor(tone)

    def ask(self, user_input: str) -> str:
        """
        Ask the chatbot a question and get a response.

        Args:
            user_input: The question to ask the chatbot.

        Returns: The response from the chatbot.
        """
        output = self._conversation.predict(
            **{
                self._prompt.user_input_key: user_input,
                self._prompt.conversation_tone_key: self._config.tone,
                self._prompt.memory_key: self._memory,
            },
        )

        if not self._debug:
            return output

        return self._debug_callback.last_used_prompt + output

    def save(self, file_path: Path, bot_description) -> None:
        """
        Serialize the chatbot to .json file.

        Args:
            bot_description: description of the companion (e.g Name, age, hobby...)
            file_path: The path to the file to serialize to.
        """
        file_path.parent.mkdir(exist_ok=True, parents=True)

        checkpoint = GPT3ConversationCheckpoint(
            config=self._config,
            prompt_template=self._prompt.original_prompt_text,
            prompt_chatbot_name=self._prompt.chatbot_name,
            prompt_user_name=self._prompt.user_name,
            memory_buffer=self._memory.buffer,
            memory_moving_summary_buffer=self._memory.moving_summary_buffer,
            bot_description=bot_description
        )

        checkpoint.to_json(file_path)

    def setup_memory(
        self, buffer: List[str], moving_summary_buffer: str
    ) -> None:
        """
        Setup the memory of the chatbot.

        Args:
            buffer: The buffer to setup.
            moving_summary_buffer: The moving summary buffer to setup.

        Returns: None
        """
        self._memory.buffer = buffer
        self._memory.moving_summary_buffer = moving_summary_buffer

    @classmethod
    def from_checkpoint(
        cls, file_path: Path, verbose: bool = False
    ) -> "GPT3Conversation":
        """
        Load a chatbot from .json file.

        Args:
            file_path: The path to the file to load from.
            verbose: Whether to print verbose output.
        """
        checkpoint = GPT3ConversationCheckpoint.from_json(file_path)
        conversation = cls(
            prompt=ConversationPrompt(
                prompt_text=checkpoint.prompt_template,
                chatbot_name=checkpoint.prompt_chatbot_name,
                user_name=checkpoint.prompt_user_name,
            ),
            model_config=checkpoint.config,
            verbose=verbose,
        )
        conversation.setup_memory(
            buffer=checkpoint.memory_buffer,
            moving_summary_buffer=checkpoint.memory_moving_summary_buffer,
        )
        #conversation.set_tone(checkpoint.config.tone)
        return conversation


if __name__ == "__main__":
    import os

    os.environ[
        "OPENAI_API_KEY"
    ] = "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"
    prompt = ConversationPrompt(
        prompt_text="This is sample prompt.",
        chatbot_name="Chatbot",
        user_name="User",
    )

    conversation = GPT3Conversation.from_checkpoint(
        Path("checkpoint.json"), verbose=True
    )

    conversation.set_tone("friendly")

    while True:
        user_input = input("You: ")
        if user_input == "exit":
            break
        print("Converbot: " + conversation.ask(user_input))

    conversation.save(Path("checkpoint.json"))
