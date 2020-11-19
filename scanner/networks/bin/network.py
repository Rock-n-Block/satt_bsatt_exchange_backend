import os
import sys
import time
import requests
import json
from hexbytes import HexBytes

from blockchain_common.eth_tokens import erc20_abi
from blockchain_common.wrapper_block import WrapperBlock
from blockchain_common.wrapper_network import WrapperNetwork
from blockchain_common.wrapper_output import WrapperOutput
from blockchain_common.wrapper_transaction import WrapperTransaction
from blockchain_common.wrapper_transaction_receipt import WrapperTransactionReceipt
from settings.settings_local import NETWORKS, ERC20_TOKENS


from binance_chain.http import HttpApiClient
from binance_chain.http import PeerType
from binance_chain.constants import KlineInterval
from binance_chain.environment import BinanceEnvironment
from binance_chain.node_rpc.http import HttpRpcClient


client = HttpApiClient()
httpapiclient = HttpApiClient()
peers = httpapiclient.get_node_peers()
listen_addr = peers[0]['listen_addr']
rpc_client = HttpRpcClient(listen_addr)
processed=[]
commited=[]

class BinNetwork(WrapperNetwork):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(BASE_DIR)
    base_dir = 'settings'
    
    def __init__(self, type):
        super().__init__(type)
        url = NETWORKS[type]['url']
        is_testnet = NETWORKS[type].get('is_testnet')

    def get_last_block(self):
        pass
    
    def get_block(self,) -> WrapperBlock:
        print('BINANCE_MAINNET: scanning', flush=True)
        client_transactions=client.get_transactions(address='bnb15hv3a52t2jfr0mwuz57nl6p6gt9hpa0gwhkanq', tx_asset='BSATT-9F8M', start_time=s_time, limit=1000)
        tx_count=client_transactions['total']
        client_transactions=client_transactions['tx']
        offset=0
        while tx_count>len(client_transactions):
            offset+=1000
            client_transactions_append=client.get_transactions(address='bnb15hv3a52t2jfr0mwuz57nl6p6gt9hpa0gwhkanq', tx_asset='BSATT-9F8M', offset=offset, start_time=s_time, limit=1000)
            tx_count=client_transactions_append['total']
            client_transactions+=client_transactions_append['tx']
            time.sleep(1)
        with open(os.path.join('../', self.base_dir, 'BINANCE_MAINNET'), 'r') as file:
            max_block = file.read()
        if len(max_block)==0:
            max_block=0
        max_block=int(max_block)
        new_transactions=[]
        for c_t in client_transactions:
            if c_t['blockHeight']<=max_block:
                break
            new_transactions.append(c_t)
        transactions=[]
        for t in new_transactions[::-1]:
            if t['code']==0 and t['txType']=='TRANSFER':
                output = WrapperOutput(
                    t['txHash'],
                    t['txAsset'],
                    t['toAddr'],
                    t['value'],
                    t['memo']
                )
                transaction = WrapperTransaction(
                        t['txHash'],
                        t['fromAddr'],
                        [output],
                        False,
                        ""
                )

                transactions.append(transaction)
                if int(t['blockHeight'])>max_block:
                    max_block=int(t['blockHeight'])
        block = WrapperBlock('','','', transactions)
                
        with open(os.path.join(self.base_dir, 'BINANCE_MAINNET'), 'w') as file:
            file.write(str(max_block))
        return block
