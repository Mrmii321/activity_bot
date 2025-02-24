import sys
import os
import paramiko

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Variables.sensitiveVars import SensitiveVariables
import json
import pandas as pd

sensitive_vars = SensitiveVariables()

def load_user_data():
    """
    Loads user data from multiple SFTP sources defined in `sensitive_vars.sftp_sources`.
    The function connects to each SFTP server, reads a user data file, parses the data,
    and merges it into a single list of dictionaries. Each dictionary maps a Discord
    ID to a Minecraft UUID.
    Returns:
        pd.DataFrame: A DataFrame where each row contains a Discord ID and a Minecraft UUID.
    Raises:
        Exception: If there is an error connecting to an SFTP server or reading/parsing the user data file.
    Logs:
        - A warning if an SFTP source configuration is incomplete.
        - Notices and info messages for connection and file operations.
        - Success messages upon successful data loading.
        - Error messages if any exceptions occur during the process.
    """
    user_data = []

    sftp_host = sensitive_vars.sftp_sources[0].get('host')
    sftp_port = sensitive_vars.sftp_sources[0].get('port')
    sftp_path = sensitive_vars.sftp_sources[0].get('path')

    for sftp_source in sensitive_vars.sftp_sources[1:]:
        sftp_username = sftp_source.get('username')
        sftp_password = sftp_source.get('password')

        # Check if any of the required SFTP configuration details are missing
        if not all([sftp_host, sftp_port, sftp_path, sftp_username, sftp_password]):
            continue

        try:
            # Log the attempt to connect to the SFTP server
            transport = paramiko.Transport((sftp_host, sftp_port))
            transport.connect(username=sftp_username, password=sftp_password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            
            # Log the attempt to open the user data file on the SFTP server
            with sftp.open(sftp_path, 'r') as file:
                aof_data = file.read().decode('utf-8')  # Decode bytes to string
                user_data_json = parse_aof_data(aof_data)
                source_user_data = json.loads(user_data_json)
            
            # Close the SFTP connection
            sftp.close()
            transport.close()

            # Merge the source user data into the main user data list
            user_data.extend(source_user_data)
        except Exception as e:
            # Log any errors that occur during the SFTP connection or file reading process
            print(f"Error: {e}")

    # Update the database with the linked user data
    with get_db_connection() as conn:
        with conn:
            for entry in user_data:
                conn.execute('''
                    UPDATE messages
                    SET is_linked = 1
                    WHERE user_id = ?
                ''', (entry['discord_id'],))

    return pd.DataFrame(user_data)

def parse_aof_data(aof_data):
    """
    Accepts a string containing lines of the form:
        <discord_id> <minecraft_uuid>
    and returns a JSON string containing a list of objects with
    "discord_id" and "minecraft_uuid".
    """
    lines = aof_data.strip().splitlines()
    entries = []

    for line in lines:
        line = line.strip()
        if not line:
            continue  # Skip empty lines
        discord_id, minecraft_uuid = line.split(maxsplit=1)
        entries.append({
            "discord_id": discord_id,
            "minecraft_uuid": minecraft_uuid
        })

    return json.dumps(entries, indent=2)


if __name__ == "__main__":
    print(load_user_data())