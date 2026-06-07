# myapp/decorators.py
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from functools import wraps
def login_required_decorator(view_func):
    """
    确保只有登录用户可以访问视图的装饰器
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # 重定向未认证用户到登录页面
            return HttpResponseRedirect(reverse('bookstore/login_view'))
        return view_func(request, *args, **kwargs)
    return _wrapped_view