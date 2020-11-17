from django.db import models


class SATTtoBSATT(models.Model):
    satt_address = models.CharField(max_length=100)
    satt_transaction_hash = models.CharField(max_length=100)
    bsatt_address = models.CharField(max_length=100)
    bsatt_mint_hash = models.CharField(max_length=100)
    bsatt_send_hash = models.CharField(max_length=100)
    amount = models.BigIntegerField()


class BSATTtoSATT(models.Model):
    bsatt_address = models.CharField(max_length=100)
    bsatt_transaction_hash = models.CharField(max_length=100)
    bsatt_burn_hash = models.CharField(max_length=100)
    satt_address = models.CharField(max_length=100)
    satt_transaction_hash = models.CharField(max_length=100)
    amount = models.BigIntegerField()





