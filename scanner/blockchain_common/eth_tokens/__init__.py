import json
import os

with open(os.path.join(os.getcwd(), 'blockchain_common/eth_tokens/erc20_abi.json'), 'r') as f:
    erc20_abi = json.load(f)

with open(os.path.join(os.getcwd(), 'blockchain_common/eth_tokens/erc223_abi.json'), 'r') as f:
    erc223_abi = json.load(f)
