from abc import ABC, abstractmethod
#from typing import Optional


class GUI_Tab(ABC):

    @abstractmethod
    def run(self):
        pass
