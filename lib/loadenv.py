from dotenv import load_dotenv
import os

load_dotenv()

API_AI_KEY = os.getenv("API_AI_KEY")


if os.name == 'nt':
    PATH = os.getenv("WINDOWS_PATH")
else:
    PATH = os.getenv("DEBIAN_PATH")
