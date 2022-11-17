'''Shared utils between blocking and async tests'''
from __future__ import annotations

import logging
from configparser import ConfigParser

def configLogging() -> None:
    logging.basicConfig()
    logging.getLogger("omada").setLevel(logging.DEBUG)


def loadConfig() -> ConfigParser:
    config = ConfigParser()
    # TODO parameterize test.cfg file name
    config.read("test.cfg")
    return config