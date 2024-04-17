import base64
from datetime import datetime, timedelta
from io import BytesIO

import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
from dateutil import parser
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render
from tiingo import TiingoClient

from user.models import SimpleUser
from user.views import user_login_required
from .models import StockData


@user_login_required
def save_stock_data_to_db(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = SimpleUser.objects.get(id=user_id)
        username = user.username
    else:
        username = None
    context = {
        'username': username,
    }
    if request.method == 'POST' and 'download' in request.POST:
        config = {
            'session': True,
            'api_key': 'd026500853ccbdcafbe636dcd9e9d905cab63b54'
        }
        selected_company = request.POST.get('company')
        client = TiingoClient(config)

        ticker_symbol = selected_company
        start_date = datetime(2020, 1, 1).strftime('%Y-%m-%d')
        end_date = datetime(2023, 3, 23).strftime('%Y-%m-%d')
        price_data = client.get_ticker_price(ticker_symbol,
                                             fmt='json',
                                             startDate=start_date,
                                             endDate=end_date)

        for entry in price_data:
            try:
                date_obj = parser.parse(entry['date']).date()
            except (ValueError, TypeError) as e:
                raise ValidationError(f"Invalid date format: {entry['date']} - {str(e)}")

            stock_entry = StockData(
                ticker=ticker_symbol,
                date=date_obj,
                open_price=entry['open'],
                high_price=entry['high'],
                low_price=entry['low'],
                close_price=entry['close'],
                volume=entry['volume'],
            )
            stock_entry.save()
        messages.success(request, '下载到本地数据库成功')
        return render(request, 'stock/save.html', context)
    else:
        # 只是加载页面但不进行数据保存
        return render(request, 'stock/save.html', context)


def generate_stock_analysis(selected_company, start_date, end_date):
    # 配置 matplotlib 以支持中文
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 指定默认字体
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号'-'显示为方块的问题

    # Tiingo API 配置
    config = {
        'session': True,
        'api_key': 'd026500853ccbdcafbe636dcd9e9d905cab63b54'
    }

    # 创建 TiingoClient
    client = TiingoClient(config)

    # 获取股票数据
    stock_data = client.get_dataframe(selected_company, startDate=start_date, endDate=end_date)
    stock_data.index = pd.to_datetime(stock_data.index)  # 确保索引为 DatetimeIndex

    # 创建图表1
    fig, axs = plt.subplots(figsize=(12, 6))
    axs.plot(stock_data.index, stock_data['close'], label='收盘价', color='blue')
    axs.set_xlabel('日期')
    axs.set_ylabel('价格')
    axs.legend()
    buffer1 = BytesIO()
    plt.savefig(buffer1, format='png')
    plt.close(fig)
    buffer1.seek(0)
    image_png1 = buffer1.getvalue()
    buffer1.close()
    image_base64_1 = base64.b64encode(image_png1).decode('utf-8')

    # 创建图表2
    fig, axs = plt.subplots(figsize=(12, 6))
    stock_data['return'] = stock_data['close'].pct_change()
    axs.hist(stock_data['return'].dropna(), bins=50, color='skyblue', edgecolor='black')
    axs.set_xlabel('收益率')
    axs.set_ylabel('频数')
    buffer2 = BytesIO()
    plt.savefig(buffer2, format='png')
    plt.close(fig)
    buffer2.seek(0)
    image_png2 = buffer2.getvalue()
    buffer2.close()
    image_base64_2 = base64.b64encode(image_png2).decode('utf-8')

    # 创建图表3
    fig, axs = plt.subplots(figsize=(12, 6))
    stock_data['ma_50'] = stock_data['close'].rolling(window=50).mean()
    stock_data['ma_200'] = stock_data['close'].rolling(window=200).mean()
    axs.plot(stock_data.index, stock_data['close'], label='收盘价', color='blue')
    axs.plot(stock_data.index, stock_data['ma_50'], label='50日移动平均线', color='red')
    axs.plot(stock_data.index, stock_data['ma_200'], label='200日移动平均线', color='green')
    axs.set_xlabel('日期')
    axs.set_ylabel('价格')
    axs.legend()
    buffer3 = BytesIO()
    plt.savefig(buffer3, format='png')
    plt.close(fig)
    buffer3.seek(0)
    image_png3 = buffer3.getvalue()
    buffer3.close()
    image_base64_3 = base64.b64encode(image_png3).decode('utf-8')

    # 创建图表4
    # 计算额外的图层数据，例如移动平均线
    sma_50 = stock_data['close'].rolling(window=50).mean()
    addplot_sma = mpf.make_addplot(sma_50, type='line', color='red')

    # 绘制图表并包括成交量
    fig, axes = mpf.plot(stock_data, type='candle', addplot=addplot_sma, volume=True,
                         ylabel='Price', ylabel_lower='Volume', figsize=(12, 8), returnfig=True)

    # 保存图形为Base64编码的PNG图像
    buffer = BytesIO()
    fig.savefig(buffer, format='png')  # 直接使用fig对象保存图像
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    image_base64_4 = base64.b64encode(image_png).decode('utf-8')
    plt.close(fig)  # 确保图形在保存后关闭

    return image_base64_1, image_base64_2, image_base64_3, image_base64_4


@user_login_required
def stock_analysis(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = SimpleUser.objects.get(id=user_id)
        username = user.username
    else:
        username = None

    # 构造年份列表，假设从2010年到当前年份
    current_year = datetime.now().year
    years = list(range(2010, current_year + 1))
    months = list(range(1, 13))
    days = list(range(1, 32))

    selected_company = request.GET.get('company', 'AAPL')  # 默认选择AAPL

    # 获取开始日期和结束日期
    start_year = int(request.GET.get('start_year', 2022))
    start_month = int(request.GET.get('start_month', datetime.now().month))
    start_day = int(request.GET.get('start_day', datetime.now().day))
    end_year = int(request.GET.get('end_year', datetime.now().year))
    end_month = int(request.GET.get('end_month', datetime.now().month))
    end_day = int(request.GET.get('end_day', datetime.now().day))

    # 构造开始日期和结束日期字符串
    start_date = f"{start_year}-{start_month:02d}-{start_day:02d}"
    end_date = f"{end_year}-{end_month:02d}-{end_day:02d}"

    # 生成股票分析图
    image_base64_1, image_base64_2, image_base64_3, image_base64_4 = generate_stock_analysis(
        selected_company, start_date, end_date)

    # Pass the base64 image data to the template
    context = {
        'image_base64_1': image_base64_1,
        'image_base64_2': image_base64_2,
        'image_base64_3': image_base64_3,
        'image_base64_4': image_base64_4,

        'selected_company': selected_company,  # 将选择的公司信息添加到context中
        'years': years,
        'months': months,
        'days': days,
        'username': username,

    }
    return render(request, 'stock/analys.html', context)


@user_login_required
def stock_overview(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = SimpleUser.objects.get(id=user_id)
        username = user.username
    else:
        username = None

    config = {
        'api_key': 'f954baf60fd958aa058437a1982e8dad69bbc524',
        'session': True  # 使用 requests session 提高性能
    }
    client = TiingoClient(config)

    # 获取动态的日期范围，往回5天
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        tickers = ['AAPL', 'GOOGL', 'TSLA', 'AMZN', 'MSFT', 'NFLX', 'NVDA', 'BABA', 'FB', 'BRK.A', 'JPM', 'JNJ', 'V',
                   'PG', 'UNH', 'MA', 'INTC', 'VZ']  # 股票代码列表
        stock_data = []
        for ticker in tickers:
            try:
                historical_prices = client.get_ticker_price(ticker, fmt='json', startDate=start_date, endDate=end_date)
                if historical_prices:
                    # 使用最后一个有数据的日期
                    latest_price = historical_prices[-1]
                    change = latest_price['close'] - latest_price['open']
                    change_percent = (change / latest_price['open']) * 100
                    stock_info = {
                        'name': ticker,
                        'price': latest_price['close'],
                        'change': change,
                        'changePercent': f"{change_percent:.2f}%",
                        'date': latest_price['date']
                    }
                    stock_data.append(stock_info)
            except Exception as e:
                print(f"Error fetching data for {ticker}: {e}")
                # 在这里处理错误，例如记录日志或返回一个错误消息
        return JsonResponse(stock_data, safe=False)

    context = {'username': username}
    return render(request, 'stock/stock_change.html', context)


# 访问主页
def index_view(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = SimpleUser.objects.get(id=user_id)
        username = user.username
    else:
        username = None

    context = {
        'username': username,
        # ...其他上下文数据...
    }
    return render(request, 'index/index.html', context)
