import importlib.util
import pymumble_py3.users

from main import Reverb

class Command:
    name = None
    module = None

    def __init__(self, name: str):
        self.name = name
        self.module = importlib.import_module(f"commands.{name}")


    def run(self, reverb: Reverb, user: pymumble_py3.users.User, args: list[str]):
        self.module.run(reverb, user, args)