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

class TrainedStock(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    model_file = models.FileField(upload_to='models/')
    created_at = models.DateTimeField(auto_now_add=True)

class Feedback(models.Model):
    user = models.ForeignKey(regtable, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Prediction(models.Model):
    user = models.ForeignKey(regtable, on_delete=models.CASCADE)
    stock_symbol = models.CharField(max_length=10)
    stock_name = models.CharField(max_length=100)
    predicted_price = models.FloatField()
    prediction_date = models.DateTimeField(auto_now_add=True)
    rmse = models.FloatField(null=True, blank=True)  # Root Mean Square Error