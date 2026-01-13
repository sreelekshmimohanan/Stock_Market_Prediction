from django.db import models



class regtable(models.Model):
    name=models.CharField(max_length=150)
    phone_number=models.CharField(max_length=120)
    email=models.CharField(max_length=120)
    password=models.CharField(max_length=120) 


class stocktable(models.Model):
    stock_name=models.CharField(max_length=150)
    stock_price=models.FloatField()
    stock_quantity=models.IntegerField()