import psycopg2
import re

def execute_sql_commands(connection, sql_commands):
    cursor = connection.cursor()
    for command in sql_commands:
        cursor.execute(command)
    cursor.close()
    connection.commit()

if __name__ == "__main__":
    # Connect to the target database (defaultdb)
    target_conn = psycopg2.connect(
        host='',
        port='25060',
        user='doadmin',
        password='',
        database='defaultdb',
        sslmode='require',
        sslrootcert='ca-certificate.crt'
    )
    print("Database Connected")
    file_encoding = 'utf-8'

    # Open the dump file and read its contents
    with open('neeceai.sql', 'r', encoding=file_encoding) as file:
        dump_contents = file.read()

    # Split the dump contents into separate SQL commands
    sql_commands = re.split(r';\s*\n', dump_contents)

    # Execute the SQL commands on the target database
    execute_sql_commands(target_conn, sql_commands)

    # Close the database connection
    target_conn.close()
