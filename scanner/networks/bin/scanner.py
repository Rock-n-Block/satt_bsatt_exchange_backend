import collections
import time

from blockchain_common.wrapper_block import WrapperBlock
from eventscanner.queue.subscribers import pub
from scanner.events.block_event import BlockEvent
from scanner.services.scanner_polling import ScannerPolling


class BinScanner(ScannerPolling):

    def polling(self):
        while True:
            block=self.network.get_block()
            self.process_block(block)
            time.sleep(10)
            block=WrapperBlock(0,0,0,[])
            print('block: {}'.format(block))
    
    def process_block(self, block: WrapperBlock):
        address_transactions = collections.defaultdict(list)
        for transaction in block.transactions:
            self._check_tx_to(transaction, address_transactions)
        block_event = BlockEvent(self.network, block, address_transactions)
        pub.sendMessage(self.network.type, block_event=block_event)

    def _check_tx_to(self, tx, addresses):
        to_address = tx.outputs[0].address

        if to_address:
            addresses[to_address.lower()].append(tx)
