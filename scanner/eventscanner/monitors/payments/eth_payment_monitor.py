from eventscanner.queue.pika_handler import send_to_backend
#from mywish_models.models import ExchangeRequests, session
from scanner.events.block_event import BlockEvent
from settings.settings_local import NETWORKS, ERC20_TOKENS


class EthPaymentMonitor:

    network_types = ['ETHEREUM_MAINNET']
    event_type = 'payment'
    queue = NETWORKS[network_types[0]]['queue']

    currency = 'ETH'
    tokenc_contract=['0xdf49c9f599a0a9049d97cff34d0c30e468987389']
    swap_contract=['0xA186415565BF4d0E0A4B61DaE4ec44DF37EF790c'.lower()]
    tokens = ERC20_TOKENS

    @classmethod
    def address_from(cls, model):
        s = cls.currency.lower() + '_address'
        return getattr(model, s)

    @classmethod
    def on_new_block_event(cls, block_event: BlockEvent):
        if block_event.network.type not in cls.network_types:
            return
        addresses = block_event.transactions_by_address.keys()
        for token_name, token_address in cls.tokens.items():
            token_address = token_address.lower()
            if token_address in addresses:
                transactions = block_event.transactions_by_address[token_address]
                cls.handle(token_address, token_name, transactions, block_event.network)
        
        
    @classmethod
    def handle(cls, token_address: str, token_name, transactions, network):
        for tx in transactions:
            if token_address.lower() != tx.outputs[0].address.lower():
                continue

            processed_receipt = network.get_processed_tx_receipt(tx.tx_hash, token_name)
            if not processed_receipt:
                print('{}: WARNING! Can`t handle tx {}, probably we dont support this event'.format(
                    cls.network_types[0], tx.tx_hash), flush=True)
                return

            transfer_to=processed_receipt[0].args.to
            amount=processed_receipt[0].args.value

            if transfer_to.lower() not in cls.swap_contract:
                print('{}: Wrong address. Skip Transaction'.format(cls.network_types[0]))
                continue 
        
            tx_receipt = network.get_tx_receipt(tx.tx_hash)
            if tx_receipt.success==True:
                success='SUCCESS'
            else:
                success='ERROR'
            print(tx.outputs[0].raw_output_script)
            message = {
                'address': tx.inputs[0],
                'transactionHash': tx.tx_hash,
                'amount': amount,
                'memo': tx.outputs[0].raw_output_script[-128:-44],
                'success': success,
            }
            
            send_to_backend(cls.event_type, cls.queue, message)
