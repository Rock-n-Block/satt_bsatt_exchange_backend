from django.db import models
from exchange.api import mint_bsatt, burn_bsatt, send_bsatt, send_satt
import time


class SATTtoBSATT(models.Model):
    satt_address = models.CharField(max_length=100)
    satt_transaction_hash = models.CharField(max_length=100)
    satt_amount = models.DecimalField(max_digits=50, decimal_places=0)
    bsatt_address = models.CharField(max_length=100)
    bsatt_mint_hash = models.CharField(max_length=100)
    bsatt_mint_error = models.CharField(max_length=100)
    bsatt_send_hash = models.CharField(max_length=100)
    bsatt_send_error = models.CharField(max_length=100)
    bsatt_amount = models.DecimalField(max_digits=50, decimal_places=0)
    status = models.CharField(max_length=10)

    class Meta:
        verbose_name='SATT to BSATT'
        verbose_name_plural = 'SATT to BSATT transactions'

    def __str__(self):
        return (f'SATT ADDRESS: {self.satt_address}\n'
        f'SATT TRANSACTION HASH: {self.satt_transaction_hash}\n'
        f'SATT AMOUNT: {self.satt_amount}\n'
        f'BSATT ADDRESS: {self.bsatt_address}\n'
        f'BSATT MINT {"HASH: " + self.bsatt_mint_hash if self.bsatt_mint_hash else "ERROR: " + self.bsatt_mint_error}\n'
        f'BSATT SEND {"HASH: " + self.bsatt_send_hash if self.bsatt_send_hash else "ERROR: " + self.bsatt_send_error}\n'
        f'BSATT AMOUNT: {self.bsatt_amount}\n'
        f'STATUS: {self.status}')

    def continue_transaction(self):
        if self.status == 'SUCCESS':
            print('TRANSACTION IS ALREADY SUCCESSFUL', flush=True)
            return

        if not self.bsatt_mint_hash:
            is_mint_ok, mint_data = mint_bsatt(self.bsatt_amount)
            if is_mint_ok:
                self.bsatt_mint_hash = mint_data
                self.bsatt_mint_error = ''
                time.sleep(10)
            else:
                self.bsatt_mint_error = mint_data
                self.save()
                return

        if not self.bsatt_send_hash:
            is_send_ok, send_data = send_bsatt(self.bsatt_address, self.bsatt_amount)
            if is_send_ok:
                self.bsatt_send_hash = send_data
                self.bsatt_send_error = ''
                self.status = 'SUCCESS'
            else:
                self.bsatt_send_error = send_data

        self.save()


class BSATTtoSATT(models.Model):
    bsatt_address = models.CharField(max_length=100)
    bsatt_transaction_hash = models.CharField(max_length=100)
    bsatt_burn_hash = models.CharField(max_length=100)
    bsatt_burn_error = models.CharField(max_length=100)
    bsatt_amount = models.CharField(max_length=100)
    satt_address = models.CharField(max_length=100)
    satt_transaction_hash = models.CharField(max_length=100)
    satt_transaction_error = models.CharField(max_length=100)
    satt_amount = models.CharField(max_length=100)
    status = models.CharField(max_length=10)

    class Meta:
        verbose_name='BSATT to SATT'
        verbose_name_plural = 'BSATT to SATT transactions'

    def __str__(self):
        return (f'BSATT ADDRESS: {self.bsatt_address}\n'
        f'BSATT TRANSACTION HASH: {self.bsatt_transaction_hash}\n'
        f'BSATT BURN {"HASH: " + self.bsatt_burn_hash if self.bsatt_burn_hash else "ERROR: " + self.bsatt_burn_error}\n'
        f'BSATT AMOUNT: {self.bsatt_amount}\n'
        f'SATT ADDRESS: {self.satt_address}\n'
        f'SATT TRANSACTION {"HASH: " + self.satt_transaction_hash if self.satt_transaction_hash else "ERROR: " + self.satt_transaction_error}\n'
        f'SATT AMOUNT: {self.satt_amount}\n'
        f'STATUS: {self.status}')

    def continue_transaction(self):
        if self.status == 'SUCCESS':
            print('TRANSACTION IS ALREADY SUCCESSFUL', flush=True)
            return

        if not self.satt_transaction_hash:
            try:
                self.satt_transaction_hash = send_satt(self.satt_address, self.satt_amount)
                self.satt_transaction_error = ''
            except Exception as e:
                self.satt_transaction_error = repr(e)
                self.save()
                return

        if not self.bsatt_burn_hash:
            is_burn_ok, burn_data = burn_bsatt(self.bsatt_amount)
            if is_burn_ok:
                self.bsatt_burn_hash = burn_data
                self.bsatt_burn_error = ''
                self.status = 'SUCCESS'
            else:
                self.bsatt_burn_error = burn_data

        self.save()
