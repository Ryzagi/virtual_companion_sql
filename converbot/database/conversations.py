import json
import time
from pathlib import Path
from typing import Dict, Tuple, List, Optional, Union

from converbot.constants import CONVERSATION_SAVE_DIR
from converbot.core import GPT3Conversation


class ConversationDB:
    """
    A database for storing conversations with GPT-3 chatbots.

    Args:
        conversation_save_dir: The directory to serialize conversations to.
    """

    def __init__(
            self,
            conversation_save_dir: Path = CONVERSATION_SAVE_DIR,
    ) -> None:
        self._conversation_save_dir = conversation_save_dir
        self._conversation_save_dir.mkdir(parents=True, exist_ok=True)

        self._user_to_conversation: Dict[str, GPT3Conversation] = {}
        self._user_to_conversation_id: Dict[str, str] = {}
        self._conversation_id_to_bot_description: Dict[str, str] = {}

    def exists(self, user_id: int) -> bool:
        return str(user_id) in self._user_to_conversation

    def remove_conversation(self, user_id: int) -> None:
        self._user_to_conversation.pop(str(user_id), None)

    def get_conversation(self, user_id: int) -> GPT3Conversation:
        return self._user_to_conversation.get(str(user_id), None)

    def get_conversation_id(self, user_id: int) -> str:
        return self._user_to_conversation_id.get(str(user_id), None)

    def add_conversation(
            self, user_id: int, conversation: GPT3Conversation, bot_description: str
    ) -> str:
        conversation_id = f"{user_id}-{int(time.time())}"
        self._user_to_conversation[str(user_id)] = conversation
        self._user_to_conversation_id[str(user_id)] = conversation_id
        self._conversation_id_to_bot_description[conversation_id] = bot_description
        return conversation_id

    def serialize_user_conversation(self, user_id: int) -> None:
        """
        Serialize the conversations to disk.

        Returns: None
        """
        user_id = str(user_id)
        conversation_id = self._user_to_conversation_id[user_id]
        chatbot_description = self._conversation_id_to_bot_description[conversation_id]
        conversation_save_path = self._conversation_save_dir / str(user_id)
        conversation_save_path.mkdir(exist_ok=True)
        conversation_save_path = (
                conversation_save_path / self._user_to_conversation_id[user_id]
        )
        conversation_save_path = conversation_save_path.with_suffix(".json")
        self._user_to_conversation[user_id].save(conversation_save_path, bot_description=chatbot_description)


    def serialize_conversations(self) -> None:
        """
        Serialize the conversations to disk.

        Returns: None
        """
        for user_id, conversation in self._user_to_conversation.items():
            conversation_id = self._user_to_conversation_id[user_id]
            chatbot_description = self._conversation_id_to_bot_description[conversation_id]

            conversation_save_path = self._conversation_save_dir / str(user_id)
            conversation_save_path.mkdir(exist_ok=True)

            conversation_save_path = (
                    conversation_save_path / self._user_to_conversation_id[user_id]
            )
            conversation_save_path = conversation_save_path.with_suffix(".json")

            conversation.save(conversation_save_path, bot_description=chatbot_description)

    @staticmethod
    def get_latest_conversation_checkpoint_path(
            checkpoints_path: Path,
    ) -> Tuple[Path, str]:
        """
        Find the latest conversation checkpoint for the user at disk.

        Args:
            checkpoints_path: The path to the checkpoints directory.
        """
        checkpoints = list(checkpoints_path.glob("*.json"))
        latest_checkpoint = sorted(
            checkpoints, key=lambda x: int(x.name.split("-")[-1].replace(".json", "")), reverse=True
        )[0]

        return latest_checkpoint, latest_checkpoint.stem

    def get_companion_descriptions_list(
            self,
            user_id: int
    ) -> Union[List[Tuple[str, str]], str]:
        """
        Display the list of companion descriptions by user_id.

        Args:
            user_id: Telegram user_ids of the user.
        """
        checkpoints = list(self._conversation_save_dir.rglob(f"{user_id}-*.json"))
        bot_descriptions = []
        for file in checkpoints:
            data = json.loads(file.read_text())
            bot_descriptions.append((data["bot_description"], file.stem))
        if len(bot_descriptions) == 0:
            return None
        return bot_descriptions

    def get_checkpoint_path_by_conversation_id(
            self,
            user_id: int,
            conversation_id: str
    ) -> Path:
        """
        Find the checkpoint path by conversation id of the user.

        Args:
            conversation_id: conversation id of the user.
            user_id: Telegram user_ids of the user.
        """

        path = self._conversation_save_dir / str(user_id) / conversation_id
        path = path.with_suffix('.json')
        return path

    def delete_conversation(
            self,
            user_id: int,
            conversation_id: str
    ) -> str:
        file_path = self.get_checkpoint_path_by_conversation_id(user_id, conversation_id)
        if file_path.exists():
            file_path.unlink()
            return f"#{conversation_id} conversation ID has been delete."
        else:
            return f"#{conversation_id} conversation ID does not exist."

    def load_conversation(
            self,
            user_id: int,
            conversation_id: str
    ) -> str:
        file_path = self.get_checkpoint_path_by_conversation_id(user_id, conversation_id)
        if file_path.exists():
            conversation = GPT3Conversation.from_checkpoint(file_path)
            self._user_to_conversation[str(user_id)] = conversation
            self._user_to_conversation_id[
                str(user_id)
            ] = conversation_id

            return f"#{conversation_id} conversation ID has been loaded."
        else:
            return f"#{conversation_id} conversation ID does not exist."

    def delete_all_conversations_by_user_id(
            self,
            user_id: int
    ) -> str:
        directory_path = self._conversation_save_dir / str(user_id)
        for file_path in directory_path.glob("*.json"):
            file_path.unlink()
        return "All conversation ID`s deleted successfully."

    def load_conversations(self) -> None:
        """
        Load the conversations from disk.

        Returns: None
        """
        for user_id in self._conversation_save_dir.iterdir():
            if user_id.is_dir() and len(list(user_id.iterdir())) > 0:
                (
                    checkpoint,
                    conversation_id,
                ) = self.get_latest_conversation_checkpoint_path(user_id)
                conversation = GPT3Conversation.from_checkpoint(checkpoint)
                self._user_to_conversation[str(user_id.name)] = conversation
                self._user_to_conversation_id[
                    str(user_id.name)
                ] = conversation_id

    def __del__(self) -> None:
        """
        Serialize the conversations to disk when the object is deleted.
        """
        self.serialize_conversations()
