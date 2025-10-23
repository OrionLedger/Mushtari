from abc import ABC, abstractmethod

class IDB_Initializer(ABC):
    @abstractmethod
    def initialize_db(self):
        pass