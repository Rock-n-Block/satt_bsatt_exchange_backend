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
        print('BINANCE_MAINNET: scanning')
        client_transactions=client.get_transactions(address='bnb15hv3a52t2jfr0mwuz57nl6p6gt9hpa0gwhkanq')
        with open(os.path.join('../', self.base_dir, 'BINANCE_MAINNET'), 'r') as file:
            max_block = file.read()
        if len(max_block)==0:
            max_block=0
        max_block=int(max_block)
        new_transactions=[]
        for c_t in client_transactions['tx']:
            if c_t['blockHeight']<=max_block:
                break
            new_transactions.append(c_t)
        for t in new_transactions[::-1]:
            if t['code']==0 and t['txType']=='TRANSFER':
                stop=False
                for tx in commited:
                    if t['txHash']==tx['txHash']:
                        stop=True
                if stop==True:
                    continue
                commited.append(t)
        transactions=[]
        while len(commited)>len(processed):
            
            output = WrapperOutput(
                    commited[len(processed)]['txHash'],
                    commited[len(processed)]['txAsset'],
                    commited[len(processed)]['toAddr'],
                    commited[len(processed)]['value'],
                    commited[len(processed)]['memo']
            )
            transaction = WrapperTransaction(
                        commited[len(processed)]['txHash'],
                        commited[len(processed)]['fromAddr'],
                        [output],
                        False,
                        ""
            )

            if int(commited[len(processed)]['blockHeight'])>max_block:
                transactions.append(transaction)
                max_block=int(commited[len(processed)]['blockHeight'])
            processed.append(commited[len(processed)])
        block = WrapperBlock('','','', transactions)
                
        with open(os.path.join('../', self.base_dir, 'BINANCE_MAINNET'), 'w') as file:
            file.write(str(max_block))
        return block
