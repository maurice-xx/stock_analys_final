"""
URL configuration for djangoProject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from feedback.views import submit_feedback, stock_news_view
from forecast.views import stock_view
from stock.views import save_stock_data_to_db, stock_analysis, index_view, stock_overview
from user.views import user_login, register, admin_panel, edit_user, delete_user, logout_user, modify_user

urlpatterns = [
    path('save', save_stock_data_to_db, name='save_stock_data_to_db'),
    path('plot', stock_analysis),
    path('forecast', stock_view),
    path('index', index_view, name="index"),
    path('login', user_login, name='user_login'),
    path('logout', logout_user, name='logout_user'),
    path('register', register, name='register'),  # 注册页面的路径
    path('admin_panel', admin_panel, name='admin_panel'),
    path('edit_user/<int:user_id>/', edit_user, name='edit_user'),
    path('delete_user/<int:user_id>/', delete_user, name='delete_user'),
    path('feedback', submit_feedback, name='submit_feedback'),
    path('news', stock_news_view, name=''),
    path('overtime', stock_overview, name='overtime'),
    path('modify_user', modify_user, name='modify_user')
]
