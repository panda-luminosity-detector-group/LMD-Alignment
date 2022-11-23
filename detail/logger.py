#!/usr/bin/env python3

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de or r.klasen@ep1.rub.de

Minimum Logger object that can be passed to other objects
"""

import datetime
from pathlib import Path


class LMDrunLogger:
    def __init__(self, fileName=f"runLogs/autoLog-{datetime.date.today()}.log"):
        Path(fileName).parent.mkdir(exist_ok=True, parents=True)
        self.contentlog = open(fileName, "a+", buffering=1)

    def log(self, message):
        self.contentlog.write(message)


if __name__ == "__main__":
    print("Sorry, this module can't be run directly")
