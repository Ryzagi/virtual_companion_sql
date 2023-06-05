import datetime
import json
import os
from pathlib import Path
from typing import Optional, List, Tuple

import psycopg2

from converbot.constants import DEV_ENV


class SQLHistoryWriter:
    """
    A class to manage the ConversationHistory database.

    Args:
        host: PostgreSQL Database host.
        port: PostgreSQL Database port.
        user: PostgreSQL Database user.
        password: PostgreSQL Database user password.
        database: PostgreSQL Database name.
        **kwargs: Additional arguments to pass to psycopg2.connect.
    """

    def __init__(
            self,
            host: str,
            port: str,
            user: str,
            password: str,
            database: str,
            **kwargs
    ) -> None:
        self._connection = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            **kwargs
        )

        self._create_database()
        self._create_companions_table()

    @property
    def connection(self) -> psycopg2.extensions.connection:
        return self._connection

    @classmethod
    def from_config(cls, file_path: Path) -> "SQLHistoryWriter":
        """
        Load the database configuration from a JSON file.

        Args:
            file_path: Path to JSON file.
        """
        data = json.loads(file_path.read_text())
        return cls(**data)

    #def __del__(self) -> None:
    #    self._connection.close()

    def _create_database(self) -> None:
        """
        Create the ConversationHistory database.
        """
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS ConversationHistory (
                    id SERIAL PRIMARY KEY,
                    conversation_id VARCHAR(255) NOT NULL,
                    user_id BIGINT NOT NULL,
                    user_message TEXT,
                    chatbot_message TEXT,
                    env VARCHAR(255) NOT NULL,
                    timestamp TIMESTAMP DEFAULT NOW() NOT NULL
                )
                """
            )
        self._connection.commit()

    def write_message(
            self,
            conversation_id: str,
            user_id: int,
            user_message: str,
            chatbot_message: str,
            env: str = DEV_ENV,
            timestamp: Optional[str] = None,
    ) -> None:
        """
        Add a new row to the ConversationHistory table.

        Args:
            conversation_id: Unique ID for the conversation.
            user_id: ID of the user who sent the message.
            user_message: Message sent by the user.
            chatbot_message: Message sent by the chatbot.
            env: Environment where the message was sent (default: PROD_ENV).
            timestamp: Timestamp for the message.
        """
        timestamp = (
            timestamp
            if timestamp
            else datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO ConversationHistory (conversation_id, user_id, user_message, chatbot_message, env, timestamp)
                VALUES (%s, %s, %s, %s, %s, to_timestamp(%s, 'YYYY-MM-DD HH24:MI:SS'))
                """,
                (
                    conversation_id,
                    user_id,
                    user_message,
                    chatbot_message,
                    env,
                    timestamp,
                ),
            )
        self._connection.commit()

    def _create_companions_table(self) -> None:
        """
        Create the Companions table.
        """
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS Companions (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    checkpoint_id TEXT,                   
                    model TEXT,
                    max_tokens INTEGER,
                    temperature FLOAT,
                    top_p FLOAT,
                    frequency_penalty FLOAT,
                    presence_penalty FLOAT,
                    best_of INTEGER,
                    tone TEXT,
                    summary_buffer_memory_max_token_limit INTEGER,
                    prompt_template TEXT,
                    prompt_user_name TEXT,
                    prompt_chatbot_name TEXT,
                    memory_buffer TEXT,
                    memory_moving_summary_buffer TEXT,
                    bot_description TEXT                    
                )
                """
            )
        self._connection.commit()


    def get_all_messages(self):
        """
        Returns a list of all messages in the ConversationHistory table.
        """
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM ConversationHistory
                """
            )
            rows = cursor.fetchall()
        return rows

    def get_chat_history(
            self,
            conversation_id: str,
            user_id: int
    ) -> List[dict]:
        """
        Retrieve the chat history for a given conversation_id and user_id.

        Args:
            conversation_id: Unique ID for the conversation.
            user_id: ID of the user.

        Returns:
            A list of tuples, where each tuple represents a message in the conversation.
            The tuple contains the following fields:
            - user_id: ID of the user who sent the message.
            - message: The text of the message.
            - is_user: True if the message was sent by the user, False if sent by the chatbot.
            - timestamp: The timestamp of the message.
        """

        messages = []
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT conversation_id, user_id, user_message, chatbot_message, env, timestamp
                FROM ConversationHistory
                WHERE conversation_id = %s AND user_id = %s
                ORDER BY timestamp ASC
                """,
                (conversation_id, user_id)
            )
            rows = cursor.fetchall()
            for row in rows:
                messages.append({
                    "conversation_id": row[0],
                    "user_id": row[1],
                    "user_message": row[2],
                    "chatbot_message": row[3],
                    "env": row[4],
                    "timestamp": row[5].strftime("%Y-%m-%d %H:%M:%S")
                })
            return messages

    def get_message_count_by_user_id(
            self,
            user_id: int
    ) -> int:
        """
        Retrieve the count of messages sent by a given user_id across all conversations.

        Args:
            user_id: ID of the user.

        Returns:
            The count of messages sent by the given user_id across all conversations.
        """

        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM ConversationHistory
                WHERE user_id = %s
                """,
                (user_id,)
            )
            return cursor.fetchone()[0]

    def get_message_count_by_user_and_conversation_id(
            self,
            user_id: int,
            conversation_id: str
    ) -> int:
        """
        Retrieve the count of messages sent between two users across all conversations.

        Args:
            user_id: ID of the first user.
            companion_id: ID of the second user.

        Returns:
            The count of messages sent between the two users across all conversations.
        """

        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM ConversationHistory
                WHERE user_id = %s AND conversation_id = %s                
                """,
                (user_id, conversation_id)
            )
            return cursor.fetchone()[0]


if __name__ == "__main__":
    os.environ['SQL_CONFIG_PATH'] = '../../configs/sql_config_prod.json'
    HISTORY_WRITER = SQLHistoryWriter.from_config(Path(os.environ.get('SQL_CONFIG_PATH')))

    db = SQLHistoryWriter(
        host="localhost",
        port="5432",
        user="postgres",
        password="admin",
        database="mydatabase",
    )
#
    db.write_message(
        conversation_id="123",
        user_id=456,
        user_message="Hello",
        chatbot_message="Hi there!",
    )
    messages = db.get_all_messages()
    for message in messages:
        print(message)
