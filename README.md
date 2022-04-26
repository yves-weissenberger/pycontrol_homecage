[![Tests](https://github.com/yves-weissenberger/pycontrol_homecage/actions/workflows/test.yml/badge.svg?branch=cleanup)](https://github.com/yves-weissenberger/pycontrol_homecage/actions/workflows/test.yml)


[![Tests](https://github.com/yves-weissenberger/pycontrol_homecage/actions/workflows/test.yml/badge.svg?branch=cleanup)](https://github.com/yves-weissenberger/pycontrol_homecage/actions/workflows/test.yml)


# Installation instructions

Installing the package requires just a few short steps

1. Navigate to 'src/pycontrol_homecage' and open the 'config.json' file
    - Set ROOT, which is the folder where all data will be saved
    - Currently the system has a mandatory email part to it where you must create a system email account (strongly recommend gmail for simplicity) that can be used to send emails. If you are FIRMLY against this, go to src/pycontrol_homecage/dialogs/add_user_dialog.py and uncomment line 51. You can then when you try to add a new user see the required code in terminal and just use this
    - For information about how to create an app password, which is what you need see https://support.google.com/mail/answer/185833?hl=en-GB


2. After this, to install the package simply navigate to this folder (i.e. the one containing the README file) and run

        pip install .

    This should take care of dependency installation so a clean python installation (Python>=3.7)

After that you should be able to run the command

    PyhomecageGUI

in your terminal to pbring up the pycontrol GUI.

# How to use it

Type PyhomecageGUI into your terminal and hit enter. Assuming you have configured everything correctly you should be able to create a new user account. After doing so, to start a new experiment, at the system tab hit **Start New Experiment** . The variables table here doesn't work but if after setting up your experiment, you navigate to the Mouse Overview tab, you can set them at the bottom. It is also in the Mouse Overview tab that you can change the task a subject is performing

# How it works

The GUI is organised into separate tabs, each of which function more independely than they used to.

All communication between different parts of the application is through the database defined in src/pycontrol_homecage/db.py which uses some strange python to act as an instance of a module import that can be accessed by any file in the package.


## Logging to consoles
Print commands 