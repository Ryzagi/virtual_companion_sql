import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from psycopg2.extras import Json
from converbot.config.gptconversation import GPT3ConversationConfig
from io import open
import psycopg2
from psycopg2 import extensions

@dataclass
class GPT3ConversationCheckpoint:
    """
    A checkpoint for a GPT-3 conversation.

    Args:
        config: The configuration for the GPT-3 conversation.
        prompt_template: The template for the prompt.
        prompt_user_name: The name of the user.
        prompt_chatbot_name: The name of the chatbot.
        memory_buffer: The buffer for the memory.
        memory_moving_summary_buffer: The moving summary buffer for the memory.
    """

    config: GPT3ConversationConfig
    prompt_template: str
    prompt_user_name: str
    prompt_chatbot_name: str
    memory_buffer: List[str]
    memory_moving_summary_buffer: str
    bot_description: Optional[str] = None

    @classmethod
    def from_sql(cls, checkpoint_id: str, connection: psycopg2.extensions.connection) -> "GPT3ConversationCheckpoint":
        """
        Load a checkpoint from the SQL table.

        Args:
            checkpoint_id: The ID of the checkpoint.
            connection: The psycopg2 connection object.

        Returns:
            The loaded GPT3ConversationCheckpoint object.
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM Checkpoints
                WHERE checkpoint_id = %(checkpoint_id)s
                """,
                {'checkpoint_id': checkpoint_id}
            )
            row = cursor.fetchone()
            if row:
                data = {
                    'config': GPT3ConversationConfig(
                        model=row['model'],
                        max_tokens=row['max_tokens'],
                        temperature=row['temperature'],
                        top_p=row['top_p'],
                        frequency_penalty=row['frequency_penalty'],
                        presence_penalty=row['presence_penalty'],
                        best_of=row['best_of'],
                        tone=row['tone'],
                        summary_buffer_memory_max_token_limit=row['summary_buffer_memory_max_token_limit'],
                    ),
                    'prompt_template': row['prompt_template'],
                    'prompt_user_name': row['prompt_user_name'],
                    'prompt_chatbot_name': row['prompt_chatbot_name'],
                    'memory_buffer': json.loads(row['memory_buffer']),
                    'memory_moving_summary_buffer': row['memory_moving_summary_buffer'],
                    'bot_description': row['bot_description'],
                }
                return cls(**data)
        raise RuntimeError(f'Checkpoint {checkpoint_id} not found.')

    def to_sql(self, user_id: int,  checkpoint_id: str, connection: psycopg2.extensions.connection) -> None:
        """
        Save the checkpoint to the SQL table.

        Args:
            user_id:
            checkpoint_id: The ID of the checkpoint.
            connection: The psycopg2 connection object.
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """
            INSERT INTO Companions (
                user_id,
                checkpoint_id,
                model,
                max_tokens,
                temperature,
                top_p,
                frequency_penalty,
                presence_penalty,
                best_of,
                tone,
                summary_buffer_memory_max_token_limit,
                prompt_template,
                prompt_user_name,
                prompt_chatbot_name,
                memory_buffer,
                memory_moving_summary_buffer,
                bot_description
            ) VALUES (
                %(user_id)s,
                %(checkpoint_id)s,
                %(model)s,
                %(max_tokens)s,
                %(temperature)s,
                %(top_p)s,
                %(frequency_penalty)s,
                %(presence_penalty)s,
                %(best_of)s,
                %(tone)s,
                %(summary_buffer_memory_max_token_limit)s,
                %(prompt_template)s,
                %(prompt_user_name)s,
                %(prompt_chatbot_name)s,
                %(memory_buffer)s,
                %(memory_moving_summary_buffer)s,
                %(bot_description)s
            )
            ON CONFLICT (user_id, checkpoint_id)
            DO UPDATE SET
                model = EXCLUDED.model,
                max_tokens = EXCLUDED.max_tokens,
                temperature = EXCLUDED.temperature,
                top_p = EXCLUDED.top_p,
                frequency_penalty = EXCLUDED.frequency_penalty,
                presence_penalty = EXCLUDED.presence_penalty,
                best_of = EXCLUDED.best_of,
                tone = EXCLUDED.tone,
                summary_buffer_memory_max_token_limit = EXCLUDED.summary_buffer_memory_max_token_limit,
                prompt_template = EXCLUDED.prompt_template,
                prompt_user_name = EXCLUDED.prompt_user_name,
                prompt_chatbot_name = EXCLUDED.prompt_chatbot_name,
                memory_buffer = EXCLUDED.memory_buffer,
                memory_moving_summary_buffer = EXCLUDED.memory_moving_summary_buffer,
                bot_description = EXCLUDED.bot_description
            """,
                {
                    'user_id': user_id,
                    'checkpoint_id': checkpoint_id,
                    'model': self.config.model,
                    'max_tokens': self.config.max_tokens,
                    'temperature': self.config.temperature,
                    'top_p': self.config.top_p,
                    'frequency_penalty': self.config.frequency_penalty,
                    'presence_penalty': self.config.presence_penalty,
                    'best_of': self.config.best_of,
                    'tone': self.config.tone,
                    'summary_buffer_memory_max_token_limit': self.config.summary_buffer_memory_max_token_limit,
                    'prompt_template': self.prompt_template,
                    'prompt_user_name': self.prompt_user_name,
                    'prompt_chatbot_name': self.prompt_chatbot_name,
                    'memory_buffer': json.dumps(self.memory_buffer),
                    'memory_moving_summary_buffer': self.memory_moving_summary_buffer,
                    'bot_description': self.bot_description,
                }
            )
        connection.commit()
