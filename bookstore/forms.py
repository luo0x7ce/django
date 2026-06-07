from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from .models import Book, Author, Reader, BorrowRecord


class RegisterForm(UserCreationForm):
    """用户注册表单"""
    email = forms.EmailField(required=True, label='电子邮箱')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = '必填，150个字符以内'
        self.fields['password1'].help_text = '密码不能太简单'
        self.fields['password2'].help_text = '请再次输入密码'


class LoginForm(AuthenticationForm):
    """登录表单"""
    username = forms.CharField(label='用户名', widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(label='密码', widget=forms.PasswordInput)

    error_messages = {
        'invalid_login': '用户名或密码错误',
        'inactive': '账户已被禁用',
    }


class BookForm(forms.ModelForm):
    """图书表单"""
    phone_regex = RegexValidator(regex=r'^1[3-9]\d{9}$', message='手机号格式不正确')

    title = forms.CharField(label='书名', max_length=200, widget=forms.TextInput(attrs={'autofocus': True}))
    author_name = forms.CharField(label='作者名称', max_length=100, required=False)
    publisher = forms.CharField(label='出版社', max_length=200)
    price = forms.DecimalField(label='价格', max_digits=10, decimal_places=2)
    market_price = forms.DecimalField(label='零售价', max_digits=10, decimal_places=2, required=False)
    total_copies = forms.IntegerField(label='总库存', min_value=0)
    shelf_location = forms.CharField(label='书架位置', max_length=50, required=False)
    category = forms.ChoiceField(label='分类', choices=Book.CATEGORY_CHOICES)

    class Meta:
        model = Book
        fields = ['isbn', 'title', 'author', 'publisher', 'publish_date', 'price',
                  'market_price', 'category', 'shelf_location', 'total_copies',
                  'available_copies', 'description', 'record']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['author'].queryset = Author.objects.all()
        self.fields['author'].required = False
        self.fields['publish_date'].required = False
        self.fields['available_copies'].required = False
        self.fields['description'].required = False
        self.fields['record'].required = False


class BorrowForm(forms.Form):
    """借阅表单"""
    book_id = forms.IntegerField(widget=forms.HiddenInput(), required=True)
    reader_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)


class ReaderForm(forms.ModelForm):
    """读者表单"""
    phone_regex = RegexValidator(regex=r'^1[3-9]\d{9}$', message='手机号格式不正确')
    id_card_regex = RegexValidator(regex=r'^\d{17}[\dXx]$', message='身份证号格式不正确')

    name = forms.CharField(label='姓名', max_length=100)
    phone = forms.CharField(label='手机号', max_length=11, validators=[phone_regex])
    id_card = forms.CharField(label='身份证号', max_length=18, validators=[id_card_regex])
    reader_type = forms.ChoiceField(label='读者类型', choices=Reader.READER_TYPE_CHOICES)

    class Meta:
        model = Reader
        fields = ['name', 'phone', 'id_card', 'reader_type', 'max_borrow_count']


class AuthorForm(forms.ModelForm):
    """作者表单"""
    email_regex = RegexValidator(regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', message='邮箱格式不正确')

    name = forms.CharField(label='姓名', max_length=100)
    email = forms.EmailField(label='邮箱', required=False, validators=[email_regex])
    age = forms.IntegerField(label='年龄', min_value=1, max_value=150, required=False)
    country = forms.CharField(label='国家', max_length=50, required=False)
    bio = forms.CharField(label='简介', widget=forms.Textarea, required=False)

    class Meta:
        model = Author
        fields = ['name', 'email', 'age', 'country', 'bio']


class BorrowRecordFilterForm(forms.Form):
    """借阅记录筛选表单"""
    STATUS_CHOICES = [('', '全部状态')] + list(BorrowRecord.STATUS_CHOICES)

    query = forms.CharField(label='搜索', required=False)
    status = forms.ChoiceField(label='状态', choices=STATUS_CHOICES, required=False)
    start_date = forms.DateField(label='开始日期', required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(label='结束日期', required=False, widget=forms.DateInput(attrs={'type': 'date'}))


class BookSearchForm(forms.Form):
    """图书搜索表单"""
    CATEGORY_CHOICES = [('', '全部分类')] + list(Book.CATEGORY_CHOICES)

    query = forms.CharField(label='关键词', required=False, max_length=200)
    category = forms.ChoiceField(label='分类', choices=CATEGORY_CHOICES, required=False)
    available_only = forms.BooleanField(label='仅显示可借', required=False)
