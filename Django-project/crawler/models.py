from django.db import models

# 建立資料庫的資料格式
class AgodaData(models.Model):
    title = models.CharField(max_length=255)
    price = models.FloatField()
    loc = models.CharField(max_length=255)
    link_url = models.URLField(max_length=600)
    photo_url = models.URLField(max_length=600)
    rate = models.FloatField()
    currency = models.CharField(max_length=50,default='JPY')
    platform = models.CharField(max_length=50)

#使用Meta更改資料表名稱、排序方法、後臺顯示的資料庫資料表名稱
    class Meta:
        db_table = "all_rooms_data"
        ordering = ['price']
        verbose_name = "訂房網站資料"
        verbose_name_plural = "訂房網站資料集"  
