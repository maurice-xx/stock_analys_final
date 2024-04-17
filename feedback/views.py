# Create your views here.
import requests
from django.contrib import messages
from django.shortcuts import render, redirect

from user.models import SimpleUser
from user.views import user_login_required
from .models import Feedback


@user_login_required
def submit_feedback(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        if user_id:
            user = SimpleUser.objects.get(id=user_id)
            username = user.username
        else:
            username = "匿名"  # 或者重定向到登录页面

        content = request.POST.get('content')
        contact = request.POST.get('contact')

        Feedback.objects.create(username=username, content=content, contact=contact)
        messages.success(request, '提交成功')
        return redirect('/index')  # 重定向到其他页面

    return render(request, 'newsandfeedback/feedback.html')


def get_stock_news():
    api_key = 'f365a9df3286424ea66e8aa70d61af58'  # 替换为您的 NewsAPI 密钥
    url = f'https://newsapi.org/v2/everything?q=stocks&apiKey={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('articles')
    else:
        return []  # 或者处理错误情况


@user_login_required
def stock_news_view(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = SimpleUser.objects.get(id=user_id)
        username = user.username
    else:
        username = None

    news_data = get_stock_news()
    return render(request, 'newsandfeedback/news.html', {'news_data': news_data, 'username': username})
