import pika
import os
import sys
import threading
import traceback
import json
import django
import binascii

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'satt_bsatt_exchange_backend.settings')
django.setup()

from satt_bsatt_exchange_backend.settings import NETWORK_SETTINGS, DECIMALS_DIFFERENCE
from exchange.models import SATTtoBSATT, BSATTtoSATT
from exchange.api import send_satt, mint_bsatt, send_bsatt, burn_bsatt, TransferException


class Receiver(threading.Thread):
    def __init__(self, network):
        super().__init__()
        self.network = network
        self.queue_name = NETWORK_SETTINGS[self.network]['queue']

    def run(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            'localhost',
            5672,
            'satt_bsatt_backend',
            pika.PlainCredentials('satt_bsatt_backend', 'satt_bsatt_backend'),
        ))

        channel = connection.channel()

        channel.queue_declare(
                queue=self.queue_name,
                durable=True,
        )
        channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self.callback
        )

        print(
            'RECEIVER MAIN: started on {net} with queue `{queue_name}`'
            .format(net=self.network, queue_name=self.queue_name), flush=True
        )

        channel.start_consuming()

    def exchange_bsatt(self, message):
        print('BSATT EXCHANGE MESSAGE RECEIVED', flush=True)

        satt_address = message.get('memo')
        amount = message.get('amount')

        transaction_hash = send_satt(satt_address, amount * DECIMALS_DIFFERENCE)
        print('SATT SENDING DONE, HASH: ', transaction_hash, flush=True)

        is_burn_ok, burn_data = burn_bsatt(amount)
        if not is_burn_ok:
            print('BSATT BURNING FAIL: ', burn_data)
            raise TransferException(burn_data)
        print('BSATT BURNING DONE, HASH: ', burn_data, flush=True)

        BSATTtoSATT(
            bsatt_address = message.get('address', ''),
            bsatt_transaction_hash=message.get('transactionHash', ''),
            bsatt_burn_hash = burn_data,
            satt_address = satt_address,
            satt_transaction_hash = transaction_hash,
            amount = amount,
        ).save()

    def exchange_satt(self, message):
        print('SATT EXCHANGE MESSAGE RECEIVED', flush=True)

        bsatt_address = binascii.unhexlify(message.get('memo')).decode('utf-8')
        amount = message.get('amount') // DECIMALS_DIFFERENCE

        is_mint_ok, mint_data = mint_bsatt(amount)
        if not is_mint_ok:
            print('BSATT MINTING FAIL: ', mint_data, flush=True)
            raise TransferException(mint_data)
        print('BSATT MINTING DONE, HASH: ', mint_data, flush=True)

        is_send_ok, send_data = send_bsatt(bsatt_address, amount)
        if not is_send_ok:
            print('BSATT SENDING FAIL: ', send_data, flush=True)
            raise TransferException(send_data)
        print('BSATT SENDING DONE, HASH: ', send_data, flush=True)

        SATTtoBSATT(
            satt_address=message.get('address'),
            satt_transaction_hash=message.get('transactionHash', ''),
            bsatt_address=bsatt_address,
            bsatt_mint_hash=mint_data,
            bsatt_send_hash=send_data,
            amount=amount,
        ).save()

    def callback(self, ch, method, properties, body):
        try:
            message = json.loads(body.decode())
            print('RECEIVED ', message)
            if message.get('success', '') == 'SUCCESS':
                getattr(self, self.queue_name.replace('-', '_'), self.unknown_handler)(message)
        except TransferException:
            pass
        except Exception:
            print('\n'.join(traceback.format_exception(*sys.exc_info())),
                  flush=True)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def unknown_handler(self, message):
        print('UNKNOWN MESSAGE', message, flush=True)


networks = NETWORK_SETTINGS.keys()


for network in networks:
    rec = Receiver(network)
    rec.start()