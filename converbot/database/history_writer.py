import datetime
import json
from pathlib import Path
from typing import Optional

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

    @classmethod
    def from_config(cls, file_path: Path) -> "SQLHistoryWriter":
        """
        Load the database configuration from a JSON file.

        Args:
            file_path: Path to JSON file.
        """
        data = json.loads(file_path.read_text())
        return cls(**data)

    def __del__(self) -> None:
        self._connection.close()

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


if __name__ == "__main__":
    db = SQLHistoryWriter(
        host="localhost",
        port="5432",
        user="postgres",
        password="123",
        database="mydatabase",
    )
    db.write_message(
        conversation_id="123",
        user_id=456,
        user_message="Hello",
        chatbot_message="Hi there!",
    )
    messages = db.get_all_messages()
    for message in messages:
        print(message)
