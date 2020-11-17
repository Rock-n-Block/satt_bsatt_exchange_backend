import json
from satt_bsatt_exchange_backend.settings import NETWORK_SETTINGS, SWAP_CONTRACT_ADDRESS, SWAP_CONTRACT_ABI, GAS_LIMIT
from satt_bsatt_exchange_backend.binance_settings import BNB_CLI_PATH, BNB_TOKEN_SYMBOL
from web3 import Web3, HTTPProvider
from subprocess import Popen, PIPE

w3 = Web3(HTTPProvider(NETWORK_SETTINGS['SATT']['endpoint']))
swap_contract = w3.eth.contract(address=SWAP_CONTRACT_ADDRESS, abi=SWAP_CONTRACT_ABI)


class TransferException(Exception):
    def __init__(self, text):
        self.value = text

    def __str__(self):
        return self.value


def send_satt(satt_address, amount):
    tx_params = {
        'nonce': w3.eth.getTransactionCount(NETWORK_SETTINGS['SATT']['address']),  # 'pending'?
        'gasPrice': w3.eth.gasPrice,
        'gas': GAS_LIMIT,
    }
    initial_tx = swap_contract.functions.exit(Web3.toChecksumAddress(satt_address), amount).buildTransaction(tx_params)
    signed = w3.eth.account.signTransaction(initial_tx, NETWORK_SETTINGS['SATT']['private'])
    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
    tx_hex = tx_hash.hex()
    return tx_hex


def execute_bnbcli_command(command_list):
    process = Popen(command_list, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate(input=(NETWORK_SETTINGS['BSATT']['key-password'] + '\n').encode())
    is_ok = process.returncode == 0
    if is_ok:
        message = json.loads(stdout.decode())
        return_data = message['TxHash']
    else:
        return_data = stderr.decode()
    # return_data = re.findall(r'tx hash: (\w+)', stdout.decode())[0] if is_ok else stderr.decode()
    # return_data = message['TxHash'] if is_ok else message.get('message', stderr.decode())
    return is_ok, return_data


def mint_bsatt(amount):
    command_list = [BNB_CLI_PATH, 'token', 'mint',
                    '--amount', str(amount),
                    '--symbol', BNB_TOKEN_SYMBOL,
                    '--from', NETWORK_SETTINGS['BSATT']['key'],
                    '--chain-id', NETWORK_SETTINGS['BSATT']['chain-id'],
                    '--node', NETWORK_SETTINGS['BSATT']['endpoint'],
                    '--trust-node', '--json']
    return execute_bnbcli_command(command_list)


def send_bsatt(bsatt_address, amount):
    command_list = [BNB_CLI_PATH, 'send',
                    '--from', NETWORK_SETTINGS['BSATT']['key'],
                    '--to', bsatt_address,
                    '--amount', f'{amount}:{BNB_TOKEN_SYMBOL}',
                    '--chain-id', NETWORK_SETTINGS['BSATT']['chain-id'],
                    '--node', NETWORK_SETTINGS['BSATT']['endpoint'],
                    '--json']
    return execute_bnbcli_command(command_list)


def burn_bsatt(amount):
    command_list = [BNB_CLI_PATH, 'token', 'burn', '--amount', str(amount),
                    '--symbol', BNB_TOKEN_SYMBOL,
                    '--from', NETWORK_SETTINGS['BSATT']['key'],
                    '--chain-id', NETWORK_SETTINGS['BSATT']['chain-id'],
                    '--node', NETWORK_SETTINGS['BSATT']['endpoint'],
                    '--trust-node', '--json']
    return execute_bnbcli_command(command_list)
