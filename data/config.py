import os

from dotenv import load_dotenv
from environs import Env

# Теперь используем вместо библиотеки python-dotenv библиотеку environs
env = Env()
env.read_env()

load_dotenv()

BOT_TOKEN = str(os.getenv("BOT_TOKEN"))

PGUSER = str(os.getenv("PGUSER"))
PGPASSWORD = str(os.getenv("PGPASSWORD"))
DATABASE = str(os.getenv("DATABASE"))
ip = str(os.getenv("ip"))
POSTGRESURI = f"postgresql://{PGUSER}:{PGPASSWORD}@{ip}/{DATABASE}"
aiogram_redis = {'host': ip,}
IP = env.str("ip")  # Тоже str, но для айпи адреса хоста


#texts

