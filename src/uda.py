import pyuda
from mast.mast_client import ListType

class UDAClient:


    def __init__(self, logger):
        self.client = pyuda.Client()
        self.client.set_property("get_meta", True)
        self.logger = logger

    def list_signals(self, shot):
        try:
            return self.client.list(ListType.SIGNALS, shot=shot, signal_type='A')
        except pyuda.ServerException as exception:
            self.logger.info(f'Skipping {shot} due to {exception}')
            return None

    def list_sources(self, shot: int):
        try:
            return self.client.list(ListType.SOURCES, shot=shot)
        except pyuda.ServerException as exception:
            self.logger.info(f'Failed to get sources due to {exception}')
            return None
