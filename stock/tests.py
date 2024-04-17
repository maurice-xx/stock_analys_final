# Create your tests here.
import datetime

from django.test import TestCase

from .models import StockData


class UtilityFunctionTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # 创建一些测试数据
        StockData.objects.create(
            ticker="AAPL",
            date=datetime.date(2021, 1, 1),
            open_price=150,  # 提供 open_price 的值
            high_price=155,
            low_price=148,
            close_price=150,
            volume=1000
        )

    def test_load_and_clean_data(self):
        # 调用工具函数
        cleaned_data = load_and_clean_data()

        # 断言：测试数据是否如预期被清洗
        # 例如，检查是否没有缺失值
        self.assertFalse(cleaned_data.isnull().any().any())

        # 可以添加更多断言来测试其他数据清洗逻辑
