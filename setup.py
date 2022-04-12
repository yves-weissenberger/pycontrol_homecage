import os
from setuptools import setup



def post_install():
    data_directory = input("Specify a path for data to be stored: ")
    user_path = input("Specify a path for user data to be stored: ")
    input("Provide name of email address for use: ")



if __name__=="__main__":
    setup()