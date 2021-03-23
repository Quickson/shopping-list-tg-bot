# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import os
from models.create_tables import create_tables
from bot import start_bot



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    create_tables()
    start_bot()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
