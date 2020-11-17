from scanner.services.last_block_persister import LastBlockPersister

from .network import BinNetwork
from .scanner import BinScanner


class BinMaker:

    def __init__(self, network_name: str, polling_interval: int, commitment_chain_length: int):
        network = BinNetwork(network_name)
        last_block_persister = LastBlockPersister(network)
        self.scanner = BinScanner(network, last_block_persister,
                                  polling_interval, commitment_chain_length)
