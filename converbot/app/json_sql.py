import json
import os
from pathlib import Path
import psycopg2

from converbot.database.history_writer import SQLHistoryWriter


def insert_json_files_to_table(directory, connection):
    """
    Insert information from JSON files in a directory and its subdirectories into an SQL table.

    Args:
        directory (str): Path to the directory containing the JSON files.
        table_name (str): Name of the SQL table.
        connection (psycopg2.extensions.connection): Database connection object.

    Returns:
        None
    """

    path = Path(directory)
    json_files = path.glob("**/*.json")  # Get all JSON files recursively

    for file_path in sorted(json_files, key=lambda x: x.stat().st_mtime):
        with open(file_path, "r") as file:
            json_data = json.load(file)

        # Extract user_id from the parent directory name
        user_id = int(file_path.parent.name)

        # Extract checkpoint_id from the file name
        checkpoint_id = file_path.stem

        # Extract relevant information from JSON data
        model = json_data.get("config", {}).get("model")
        max_tokens = json_data.get("config", {}).get("max_tokens")
        temperature = json_data.get("config", {}).get("temperature")
        top_p = json_data.get("config", {}).get("top_p")
        frequency_penalty = json_data.get("config", {}).get("frequency_penalty")
        presence_penalty = json_data.get("config", {}).get("presence_penalty")
        best_of = json_data.get("config", {}).get("best_of")
        tone = json_data.get("config", {}).get("tone")
        summary_buffer_memory_max_token_limit = json_data.get("config", {}).get("summary_buffer_memory_max_token_limit")
        prompt_template = json_data.get("prompt_template")
        prompt_user_name = json_data.get("prompt_user_name")
        prompt_chatbot_name = json_data.get("prompt_chatbot_name")
        memory_buffer = json_data.get("memory_buffer")
        memory_moving_summary_buffer = json_data.get("memory_moving_summary_buffer")
        bot_description = json_data.get("bot_description")

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
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
                    )
                    VALUES (
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
                    """,
                {
                    "user_id": user_id,
                    "checkpoint_id": checkpoint_id,
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    "frequency_penalty": frequency_penalty,
                    "presence_penalty": presence_penalty,
                    "best_of": best_of,
                    "tone": tone,
                    "summary_buffer_memory_max_token_limit": summary_buffer_memory_max_token_limit,
                    "prompt_template": prompt_template,
                    "prompt_user_name": prompt_user_name,
                    "prompt_chatbot_name": prompt_chatbot_name,
                    "memory_buffer": memory_buffer,
                    "memory_moving_summary_buffer": memory_moving_summary_buffer,
                    "bot_description": bot_description
                }
            )
            connection.commit()

    print("Data insertion completed.")

if __name__ == "__main__":
    os.environ['SQL_CONFIG_PATH'] = '../../configs/sql_config_prod.json'
    HISTORY_WRITER = SQLHistoryWriter.from_config(Path(os.environ.get('SQL_CONFIG_PATH')))
    # Example usage:
    directory_path = "../../database/saved_conversations"  # Replace with the actual directory path
    table_name = "Companions"  # Replace with the actual table name
#
#
    connection = HISTORY_WRITER.connection
#
    insert_json_files_to_table(directory_path, connection)
#
    # Don't forget to close the database connection after you're done
    connection.close()
