from rest_framework import serializers
from .models import AgodaData

#建立序列器，在使用api的時候可以將資料庫內的資料建立成json格式的資料
class AgodaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgodaData
        fields = '__all__'
