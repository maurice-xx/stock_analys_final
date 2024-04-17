import base64
from datetime import datetime, timedelta
from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from django.shortcuts import render
from keras.layers import LSTM, Dense, Dropout
from keras.models import Sequential
from sklearn.preprocessing import MinMaxScaler
from tiingo import TiingoClient

from user.models import SimpleUser
from user.views import user_login_required


# Create your views here.


# 步骤 1: 数据预处理


# 清洗数据，移除或替换异常值
def replace_outliers(df, window_size=20, z_score_threshold=2):
    df['close_price_mean'] = df['close'].rolling(window=window_size).mean()
    df['close_price_std'] = df['close'].rolling(window=window_size).std()

    df['z_score'] = (df['close'] - df['close_price_mean']) / df['close_price_std']
    outliers = abs(df['z_score']) > z_score_threshold

    # 标记被替换的数据
    df['replaced'] = outliers

    # 替换异常值
    for i in outliers[outliers].index:
        valid_indices = [x for x in [i - 1, i + 1] if x in df.index]
        if valid_indices:
            replacement_value = df.loc[valid_indices, 'close'].mean()
            df.at[i, 'close'] = replacement_value

    return df.drop(columns=['close_price_mean', 'close_price_std', 'z_score'])


# 生成训练集
def create_dataset(df, history_size=360, prediction_size=1):
    close_prices = df['close'].values
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(close_prices.reshape(-1, 1))

    X, y = [], []
    for i in range(history_size, len(scaled_data) - prediction_size):
        X.append(scaled_data[i - history_size:i, 0])
        y.append(scaled_data[i + prediction_size - 1, 0])
    return np.array(X), np.array(y), scaler


# 步骤 2: 模型训练
def train_model(X_train, y_train):
    model = Sequential()
    # 第一个 LSTM 层，返回完整的输出序列
    model.add(LSTM(units=100, return_sequences=True, input_shape=(X_train.shape[1], 1)))
    model.add(Dropout(0.2))

    # 第二个 LSTM 层
    model.add(LSTM(units=100, return_sequences=True))
    model.add(Dropout(0.2))

    # 第三个 LSTM 层
    model.add(LSTM(units=100))
    model.add(Dropout(0.2))

    # 全连接层
    model.add(Dense(units=1))

    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(X_train, y_train, epochs=100, batch_size=32)

    return model


# 步骤 3: 进行预测
def predict_future_prices(model, df, scaler, days_to_predict=60, history_size=360):
    last_data = df['close'].values[-history_size:]  # 使用 'close'
    scaled_data = scaler.transform(last_data.reshape(-1, 1))
    future_prices = []

    for _ in range(days_to_predict):
        predicted_price = model.predict(scaled_data.reshape(1, -1, 1))
        future_prices.append(scaler.inverse_transform(predicted_price)[0][0])
        scaled_data = np.append(scaled_data, predicted_price)[1:].reshape(-1, 1)

    return future_prices


# 步骤 4: 结果可视化
def visualize_predictions(actual_dates, actual_prices, predicted_prices, start_predict_date):
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 指定默认字体
    plt.figure(figsize=(15, 6))
    plt.plot(actual_dates, actual_prices, label='实际价格', color='blue')  # 使用 'actual_prices'

    # 生成预测日期范围
    prediction_dates = pd.date_range(start=start_predict_date, periods=len(predicted_prices))
    plt.plot(prediction_dates, predicted_prices, label='预测价格', color='red')

    plt.xlabel('日期')
    plt.ylabel('收盘价')
    plt.title('股票未来两个月收盘价预测')
    plt.legend()
    plt.tight_layout()

    # 返回图表的图像数据而非直接显示
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    graph = base64.b64encode(image_png)
    graph = graph.decode('utf-8')
    buffer.close()

    return graph


# Django视图函数
@user_login_required
def stock_view(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = SimpleUser.objects.get(id=user_id)
        username = user.username
    else:
        username = None

    # Tiingo API 配置
    config = {
        'api_key': 'd026500853ccbdcafbe636dcd9e9d905cab63b54',
        'session': True  # 使用会话来保持连接
    }

    # 在函数内部创建 TiingoClient 实例
    client = TiingoClient(config)

    # 获取用户选择的公司
    selected_company = request.GET.get('company', 'AAPL')
    # 使用 Tiingo API 获取股票数据
    ticker_symbol = selected_company  # 例子中使用苹果公司的股票代码
    end_date = datetime.now()
    start_date = end_date - timedelta(days=2 * 365)  # 2 年前的日期
    historical_prices = client.get_ticker_price(ticker_symbol,
                                                fmt='json',
                                                startDate=start_date.strftime('%Y-%m-%d'),
                                                endDate=end_date.strftime('%Y-%m-%d'))

    # 转换数据为 DataFrame
    df = pd.DataFrame(historical_prices)
    df['date'] = pd.to_datetime(df['date'])
    df['close'] = pd.to_numeric(df['close'])

    # 数据预处理
    df = replace_outliers(df)

    # 创建训练集
    X, y, scaler = create_dataset(df)
    X_train, y_train = X[:len(X) * 80 // 100], y[:len(y) * 80 // 100]
    X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))

    model = train_model(X_train, y_train)

    # 预测未来60天的价格
    predicted_prices = predict_future_prices(model, df, scaler)

    # 正确设置预测开始日期
    start_predict_date = df['date'].iloc[-1] + pd.Timedelta(days=1)

    # 生成并获取图像数据
    graph = visualize_predictions(df['date'], df['close'], predicted_prices, start_predict_date)

    # 将图表字符串添加到上下文
    context = {'graph': graph,
               'selected_company': selected_company,
               'username': username}
    return render(request, 'stock/forecast.html', context)

# views.py
