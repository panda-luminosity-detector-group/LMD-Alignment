#!/usr/bin/env python3

"""
Minimum Logger object that can be passed to other objects
"""

import datetime
from pathlib import Path

class LMDrunLogger():
    def __init__(self, fileName=f'runLogs/autoLog-{datetime.date.today()}.log'):
        Path(fileName).parent.mkdir(exist_ok=True)
        self.contentlog = open(fileName, 'a')
    
    def log(self, message):
        self.contentlog.write(message)

if __name__ == "__main__":
    print("Sorry, this module can't be run directly")
