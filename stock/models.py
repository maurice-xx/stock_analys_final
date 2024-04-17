from django.db import models


# Create your models here.


# StockData 模型
class StockData(models.Model):
    ticker = models.CharField(max_length=10)  # 股票代码字段
    date = models.DateField()
    open_price = models.FloatField()
    high_price = models.FloatField()
    low_price = models.FloatField()
    close_price = models.FloatField()
    volume = models.BigIntegerField()
