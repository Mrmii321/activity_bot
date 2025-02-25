import os
from dotenv import load_dotenv

load_dotenv()

class SensitiveVariables:
    def __init__(self):
        self.bot_token = os.getenv("BOT_TOKEN")
        self.sftp_sources = [
            {
                "host": os.getenv("SFTP_HOST"),
                "port": int(os.getenv("SFTP_PORT")),
                "path": os.getenv("SFTP_PATH")
            },
            {
                "username": os.getenv("SFTP_USERNAME_1"),
                "password": os.getenv("SFTP_PASSWORD_1")
            },
            {
                "username": os.getenv("SFTP_USERNAME_2"),
                "password": os.getenv("SFTP_PASSWORD_2")
            },
            {
                "username": os.getenv("SFTP_USERNAME_3"),
                "password": os.getenv("SFTP_PASSWORD_3")
            },
            {
                "username": os.getenv("SFTP_USERNAME_4"),
                "password": os.getenv("SFTP_PASSWORD_4")
            },
            {
                "username": os.getenv("SFTP_USERNAME_5"),
                "password": os.getenv("SFTP_PASSWORD_5")
            },
            {
                "username": os.getenv("SFTP_USERNAME_6"),
                "password": os.getenv("SFTP_PASSWORD_6")
            },
            {
                "username": os.getenv("SFTP_USERNAME_7"),
                "password": os.getenv("SFTP_PASSWORD_7")
            }
        ]

    @property
    def sftp_sources_info(self):
        return self.sftp_sources