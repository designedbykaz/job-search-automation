import os


def get(name, default=None):
    return os.getenv(name, default)
