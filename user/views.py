from functools import wraps

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from feedback.models import Feedback
from .models import SimpleUser


# Create your views here.

# 在 views.py 或单独的 decorators.py 中


def admin_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('logged_in') or request.session.get('user_type') != 1:
            return redirect('/login')  # 未登录或非管理员，重定向到登录页面
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def user_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('logged_in') or request.session.get('user_type') != 0:
            return redirect('/login')  # 未登录或非普通用户，重定向到登录页面
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def logout_user(request):
    request.session.flush()  # 清除会话
    return redirect('/index')


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        is_admin = request.POST.get('is_admin', '') == 'on'

        try:
            user = SimpleUser.objects.get(username=username)

            if user.password == password:
                request.session['logged_in'] = True  # 设置登录标记
                request.session['user_id'] = user.id  # 保存用户ID
                request.session['user_type'] = user.user_type  # 保存用户类型
                if is_admin and user.user_type == 1:
                    # 重定向到管理员界面
                    return redirect('/admin_panel')
                elif not is_admin and user.user_type == 0:
                    # 重定向到普通用户界面
                    return redirect('/index')
                else:
                    messages.error(request, '登录失败：权限不足')
            else:
                messages.error(request, '登录失败：密码错误')

        except SimpleUser.DoesNotExist:
            messages.error(request, '登录失败：用户不存在')

    return render(request, 'login/login.html')


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if SimpleUser.objects.filter(username=username).exists():
            messages.error(request, '用户名已被占用')
            return redirect('/register')
        elif SimpleUser.objects.filter(email=email).exists():
            messages.error(request, '电子邮件已被使用')
            return redirect('/register')
        else:
            SimpleUser.objects.create(username=username, email=email, password=password)  # 创建新用户
            messages.success(request, '注册成功！')
            return redirect('/login')  # 重定向到登录页面
    return render(request, 'login/register.html')  # 显示注册表单


# 管理员面板
@admin_login_required
def admin_panel(request):
    users = SimpleUser.objects.filter(user_type=0)  # 获取所有普通用户
    feedbacks = Feedback.objects.all()  # 获取所有反馈意见
    return render(request, 'login/admin_panel.html', {'users': users, 'feedbacks': feedbacks})


# 编辑用户
@admin_login_required
def edit_user(request, user_id):
    user = get_object_or_404(SimpleUser, pk=user_id)
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        password = request.POST.get('password')
        if password:  # 只有在提供新密码时才更新
            user.password = password
        user.save()
        return redirect('admin_panel')
    return render(request, 'login/edit_user.html', {'user': user})


# 删除用户
@admin_login_required
def delete_user(request, user_id):
    user = get_object_or_404(SimpleUser, pk=user_id)
    user.delete()
    return redirect('admin_panel')


@user_login_required
def modify_user(request):
    user_id = request.session.get('user_id')
    user = get_object_or_404(SimpleUser, pk=user_id)

    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        # 使用Django的密码验证器来检查旧密码是否正确
        if not (old_password == user.password):
            # 如果密码不匹配，向用户显示错误消息
            messages.error(request, '旧密码不正确。')
            return render(request, 'login/modify_user.html', {'user': user})

        # 如果旧密码正确，则继续处理表单提交
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        user.username = username
        user.email = email
        if password:  # 如果提供了新密码
            user.password = password
        user.save()

        messages.success(request, '您的信息已成功更新。')
        return redirect(reverse('index'))

    return render(request, 'login/modify_user.html', {'user': user})
