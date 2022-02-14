import os
from setuptools import setup



def post_install():
    data_directory = input("Specify a path for data to be stored: ")
    input("Specify a path for user info to be stored: ")
    input("Provide name of email address for use: ")
    



if __name__=="__main__":
    setup()