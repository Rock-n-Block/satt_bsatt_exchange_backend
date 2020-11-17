from pubsub import pub

from eventscanner.monitors.payments import (BinPaymentMonitor, EthPaymentMonitor)

pub.subscribe(BinPaymentMonitor.on_new_block_event, 'BINANCE_MAINNET')
pub.subscribe(EthPaymentMonitor.on_new_block_event, 'ETHEREUM_MAINNET')
