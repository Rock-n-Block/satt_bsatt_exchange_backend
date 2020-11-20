import pika
import os
import sys
import threading
import traceback
import json
import django
import binascii
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'satt_bsatt_exchange_backend.settings')
django.setup()

from satt_bsatt_exchange_backend.settings import NETWORK_SETTINGS, DECIMALS_DIFFERENCE, SATT_BSATT_RATE
from satt_bsatt_exchange_backend.binance_settings import BSATT_OWNER_ADDRESS
from exchange.models import SATTtoBSATT, BSATTtoSATT
from exchange.api import send_satt, mint_bsatt, send_bsatt, burn_bsatt


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
        bsatt_tx_hash = message.get('transactionHash')
        saved_transactions = BSATTtoSATT.objects.filter(bsatt_transaction_hash=bsatt_tx_hash)
        if not saved_transactions.count() > 0:
            memo = message.get('memo')
            if not memo:
                print('ERROR: MEMO CANNOT BE EMPTY, TRANSACTION DECLINED', flush=True)
                return

            tx = BSATTtoSATT(
                bsatt_address=message.get('address'),
                bsatt_transaction_hash=bsatt_tx_hash,
                bsatt_amount=message.get('amount'),
                satt_address=memo,
                satt_amount=message.get('amount') * DECIMALS_DIFFERENCE * SATT_BSATT_RATE
            )

            try:
                tx.satt_transaction_hash = send_satt(tx.satt_address, tx.satt_amount)
                is_burn_ok, burn_data = burn_bsatt(tx.bsatt_amount)
                if is_burn_ok:
                    tx.bsatt_burn_hash = burn_data
                    tx.status = 'SUCCESS'
                else:
                    tx.bsatt_burn_error = burn_data
                    tx.status = 'FAIL'
            except Exception as e:
                tx.satt_transaction_error = repr(e)
                tx.status = 'FAIL'

            print('BSATT to SATT TRANSFER INFO:\n' + str(tx), flush=True)
            tx.save()
        else:
            print('RECEIVED TRANSACTION EXISTS IN DATABASE:\n' + str(saved_transactions[0]), flush=True)

    def exchange_satt(self, message):
        satt_tx_hash = message.get('transactionHash')
        saved_transactions = SATTtoBSATT.objects.filter(satt_transaction_hash=satt_tx_hash)
        if not saved_transactions.count() > 0:
            memo = message.get('memo')
            if not memo:
                print('ERROR: MEMO CANNOT BE EMPTY, TRANSACTION DECLINED', flush=True)
                return
            try:
                bsatt_address = binascii.unhexlify(memo).decode('utf-8')
                if bsatt_address == BSATT_OWNER_ADDRESS:
                    print(f'BSATT ADDRESS IS TOKEN OWNER ADDRESS, TRANSACTION DECLINED', flush=True)
                    return
            except Exception as e:
                print(f'ERROR WHILE DECODING MEMO: {repr(e)}, TRANSACTION DECLINED', flush=True)
                return

            tx = SATTtoBSATT(
                satt_address=message.get('address'),
                satt_transaction_hash=satt_tx_hash,
                satt_amount=message.get('amount'),
                bsatt_address=bsatt_address,
                bsatt_amount= message.get('amount') // (DECIMALS_DIFFERENCE * SATT_BSATT_RATE)
            )

            is_mint_ok, mint_data = mint_bsatt(tx.bsatt_amount)
            if is_mint_ok:
                tx.bsatt_mint_hash = mint_data
                time.sleep(10)
                is_send_ok, send_data = send_bsatt(tx.bsatt_address, tx.bsatt_amount)
                if is_send_ok:
                    tx.bsatt_send_hash = send_data
                    tx.status = 'SUCCESS'
                else:
                    tx.bsatt_send_error = send_data
                    tx.status = 'FAIL'
            else:
                tx.bsatt_mint_error = mint_data
                tx.status = 'FAIL'
            print('SATT to BSATT TRANSFER INFO:\n' + str(tx), flush=True)
            tx.save()
        else:
            print('RECEIVED TRANSACTION EXISTS IN DATABASE:\n' + str(saved_transactions[0]), flush=True)

    def callback(self, ch, method, properties, body):
        try:
            message = json.loads(body.decode())
            print(f'\n\n{self.queue_name.upper()} QUEUE RECEIVED ', message)
            if message.get('success', '') == 'SUCCESS':
                getattr(self, self.queue_name.replace('-', '_'), self.unknown_handler)(message)
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
