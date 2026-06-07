import datetime
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_http_methods, require_POST
from django.db import transaction
from django.db.models import Q, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Book, Author, Reader, BorrowRecord
from .forms import BorrowForm


# ==================== Authentication Views ====================

def first_page(request):
    """首页 - 显示统计信息和快捷操作"""
    total_books = Book.objects.filter(is_active=True).count()
    total_readers = Reader.objects.filter(is_active=True).count()
    today_borrowed = BorrowRecord.objects.filter(
        borrow_date__date=datetime.date.today()
    ).count()
    overdue_count = BorrowRecord.objects.filter(
        status='borrowed',
        due_date__lt=datetime.date.today()
    ).count()

    # 热门图书 TOP 10 (按实际借阅次数排序)
    popular_books = Book.objects.annotate(
        borrow_count=Count('borrow_records')
    ).filter(is_active=True).order_by('-borrow_count')[:10]

    # 最新入库图书
    new_books = Book.objects.filter(is_active=True).order_by('-record_time')[:8]

    context = {
        'total_books': total_books,
        'total_readers': total_readers,
        'today_borrowed': today_borrowed,
        'overdue_count': overdue_count,
        'popular_books': popular_books,
        'new_books': new_books,
    }
    return render(request, 'bookstore/first_page.html', context)


def register(request):
    """用户注册"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        name = request.POST.get('name', '')
        phone = request.POST.get('phone', '')
        id_card = request.POST.get('id_card', '')

        # 验证输入
        if not username or not email or not password:
            messages.error(request, '用户名、邮箱和密码都是必填的')
            return render(request, 'bookstore/register.html')

        if password != password2:
            messages.error(request, '两次密码输入不一致')
            return render(request, 'bookstore/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, '用户名已存在')
            return render(request, 'bookstore/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, '邮箱已被注册')
            return render(request, 'bookstore/register.html')

        # 创建用户
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_active = True
        user.save()

        # 创建读者档案
        if name and phone and id_card:
            Reader.objects.create(
                user=user,
                name=name,
                phone=phone,
                id_card=id_card,
                reader_type='student'
            )

        messages.success(request, '注册成功，请登录')
        return redirect('bookstore:login')

    return render(request, 'bookstore/register.html')


def login_view(request):
    """用户登录"""
    if request.user.is_authenticated:
        return redirect('bookstore:first_page')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            form = AuthenticationForm(request, data=request.POST)
            form.add_error(None, '用户名和密码不能为空！')
            return render(request, 'bookstore/login_view.html', {'form': form})

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '/bookstore/first_page')
            return redirect(next_url)
        else:
            form = AuthenticationForm(request, data=request.POST)
            form.add_error(None, '无效的用户名或密码')
            return render(request, 'bookstore/login_view.html', {'form': form})

    return render(request, 'bookstore/login_view.html')


def logout_view(request):
    """用户登出"""
    logout(request)
    return redirect('bookstore:login')


def password_reset(request):
    """密码重置"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if not username or not password:
            messages.error(request, '用户名和新密码都是必填的')
            return render(request, 'bookstore/password_reset.html')

        if password != password2:
            messages.error(request, '两次密码输入不一致')
            return render(request, 'bookstore/password_reset.html')

        try:
            user = User.objects.get(username=username)
            user.set_password(password)
            user.save()
            messages.success(request, '密码已重置，请登录')
            return redirect('bookstore:login')
        except User.DoesNotExist:
            messages.error(request, '用户不存在')
            return render(request, 'bookstore/password_reset.html')

    return render(request, 'bookstore/password_reset.html')


# ==================== Book Management Views ====================

@login_required
def index(request):
    """书籍列表与搜索"""
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    page = request.GET.get('page', 1)

    books = Book.objects.filter(is_active=True)

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author_name__icontains=query) |
            Q(isbn__icontains=query) |
            Q(publisher__icontains=query) |
            Q(record__icontains=query) |
            Q(shelf_location__icontains=query)
        ).distinct()

    if category:
        books = books.filter(category=category)

    # 分页
    paginator = Paginator(books, 12)  # 每页12本
    try:
        books_page = paginator.page(page)
    except PageNotAnInteger:
        books_page = paginator.page(1)
    except EmptyPage:
        books_page = pag.page(paginator.num_pages)

    # 获取所有分类
    categories = Book.CATEGORY_CHOICES

    return render(request, 'bookstore/index.html', {
        'books': books_page,
        'query': query,
        'category': category,
        'categories': categories,
    })


@login_required
def update_book(request, book_id):
    """更新书籍信息"""
    book = get_object_or_404(Book, id=book_id)
    authors = Author.objects.all()

    if request.method == 'POST':
        book.isbn = request.POST.get('isbn', '')
        book.title = request.POST.get('title', '')
        book.publisher = request.POST.get('publisher', '')
        book.price = request.POST.get('price', '')
        book.market_price = request.POST.get('market_price', '')
        book.record = request.POST.get('record', '')
        book.total_copies = request.POST.get('total_copies', 1)
        book.available_copies = request.POST.get('available_copies', 1)
        book.shelf_location = request.POST.get('shelf_location', '')
        book.category = request.POST.get('category', 'other')

        author_id = request.POST.get('author')
        if author_id:
            book.author = get_object_or_404(Author, id=author_id)

        book.save()
        messages.success(request, '书籍更新成功')
        return redirect('bookstore:index')

    return render(request, 'bookstore/update_book.html', {
        'book': book,
        'authors': authors
    })


@login_required
def delete_book(request, book_id):
    """删除书籍（软删除）"""
    book = get_object_or_404(Book, id=book_id)
    book.is_active = False
    book.save()
    messages.success(request, f'《{book.title}》已删除')
    return redirect('bookstore:index')


@login_required
@require_http_methods(["GET", "POST"])
def batch_delete(request):
    """批量删除书籍（仅POST）"""
    if request.method == 'GET':
        return redirect('bookstore:index')

    selected_ids = request.POST.getlist('selected_books')
    if not selected_ids:
        messages.error(request, '请选择要删除的书籍')
        return redirect('bookstore:index')

    # 软删除
    Book.objects.filter(id__in=selected_ids).update(is_active=False)
    messages.success(request, f'已删除 {len(selected_ids)} 本书籍')
    return redirect('bookstore:index')


@login_required
def add_book(request):
    """添加书籍"""
    authors = Author.objects.all()

    if request.method == 'POST':
        isbn = request.POST.get('isbn', '').strip()
        title = request.POST.get('title', '').strip()
        publisher = request.POST.get('publisher', '').strip()
        price = request.POST.get('price', '').strip()
        market_price = request.POST.get('market_price', '').strip()
        record = request.POST.get('record', '').strip()
        author_name = request.POST.get('author_name', '').strip()
        total_copies = request.POST.get('total_copies', '1').strip()
        shelf_location = request.POST.get('shelf_location', '').strip()
        category = request.POST.get('category', 'other')
        author_id = request.POST.get('author')

        # 验证必需字段
        if not title:
            messages.error(request, '书名不能为空')
            return render(request, 'bookstore/add_book.html', {'authors': authors})

        if not publisher:
            messages.error(request, '出版社不能为空')
            return render(request, 'bookstore/add_book.html', {'authors': authors})

        if not price:
            messages.error(request, '价格不能为空')
            return render(request, 'bookstore/add_book.html', {'authors': authors})

        # 获取作者
        author = None
        if author_id:
            author = get_object_or_404(Author, id=author_id)

        # 检查书籍是否已存在
        if Book.objects.filter(title=title, publisher=publisher, is_active=True).exists():
            messages.error(request, '该书籍已存在')
            return render(request, 'bookstore/add_book.html', {'authors': authors})

        # 创建新书籍
        Book.objects.create(
            isbn=isbn,
            title=title,
            author=author,
            author_name=author_name or (author.name if author else ''),
            publisher=publisher,
            price=price,
            market_price=market_price or price,
            record=record,
            total_copies=total_copies or 1,
            available_copies=total_copies or 1,
            shelf_location=shelf_location or 'A-1-1',
            category=category
        )

        messages.success(request, '书籍添加成功')
        return redirect('bookstore:index')

    return render(request, 'bookstore/add_book.html', {'authors': authors})


# ==================== Borrow/Return Views ====================

@login_required
@transaction.atomic
def borrow_book(request):
    """借书"""
    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        reader_id = request.POST.get('reader_id')

        if not book_id:
            messages.error(request, '请选择要借阅的书籍')
            return redirect('bookstore:borrow_book')

        try:
            # 使用 select_for_update 锁定行，防止并发问题
            book = Book.objects.select_for_update().get(id=book_id, is_active=True)

            # 检查库存
            if book.available_copies <= 0:
                messages.error(request, '该书库存不足或已全部借出')
                return redirect('bookstore:borrow_book')

            # 获取读者信息
            reader = None
            if reader_id:
                reader = get_object_or_404(Reader, id=reader_id)
            elif request.user.is_authenticated and hasattr(request.user, 'reader_profile'):
                reader = request.user.reader_profile
            else:
                messages.error(request, '请先完善读者信息')
                return redirect('bookstore:borrow_book')

            # 检查借书数量限制
            if not reader.can_borrow:
                messages.error(request, f'您已达到最大借书数量（{reader.max_borrow_count}本）')
                return redirect('bookstore:borrow_book')

            # 检查是否已借阅此书
            if BorrowRecord.objects.filter(reader=reader, book=book, return_date__isnull=True).exists():
                messages.error(request, '您已借阅此书')
                return redirect('bookstore:borrow_book')

            # 计算借阅日期
            borrow_date = timezone.now()
            due_date = borrow_date.date() + datetime.timedelta(days=30)

            # 创建借阅记录
            borrow_record = BorrowRecord.objects.create(
                reader=reader,
                book=book,
                due_date=due_date,
                operator=request.user
            )

            # 更新库存
            book.available_copies -= 1
            book.save()

            messages.success(request, f'借书成功！应还日期：{due_date}')
            return redirect('bookstore:borrow_record_list')

        except Book.DoesNotExist:
            messages.error(request, '图书不存在')
            return redirect('bookstore:borrow_book')

    # GET 请求 - 显示借书表单
    books = Book.objects.filter(is_active=True, available_copies__gt=0).order_by('-record_time')
    readers = Reader.objects.filter(is_active=True)

    # 搜索过滤
    query = request.GET.get('q', '')
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author_name__icontains=query) |
            Q(isbn__icontains=query)
        )

    # 分页
    paginator = Paginator(books, 10)
    page = request.GET.get('page', 1)
    try:
        books_page = paginator.page(page)
    except PageNotAnInteger:
        books_page = paginator.page(1)
    except EmptyPage:
        books_page = paginator.page(paginator.num_pages)

    return render(request, 'bookstore/borrow_book.html', {
        'books': books_page,
        'readers': readers,
        'query': query
    })


@login_required
def borrow_record_list(request):
    """借阅记录列表"""
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    page = request.GET.get('page', 1)

    records = BorrowRecord.objects.select_related('reader', 'book').all()

    if query:
        records = records.filter(
            Q(reader__name__icontains=query) |
            Q(reader__id_card__icontains=query) |
            Q(book__title__icontains=query) |
            Q(book__isbn__icontains=query)
        ).distinct()

    if status:
        records = records.filter(status=status)

    # 分页
    paginator = Paginator(records, 15)
    try:
        records_page = paginator.page(page)
    except PageNotAnInteger:
        records_page = paginator.page(1)
    except EmptyPage:
        records_page = paginator.page(paginator.num_pages)

    return render(request, 'bookstore/borrow_record_list.html', {
        'records': records_page,
        'query': query,
        'status': status,
    })


@login_required
@transaction.atomic
def return_book(request, record_id):
    """归还书籍"""
    borrow_record = get_object_or_404(BorrowRecord, id=record_id)

    if borrow_record.return_date is not None:
        messages.info(request, '该书已归还')
        return redirect('bookstore:borrow_record_list')

    # 使用事务保证数据一致性
    # 锁定图书记录
    book = Book.objects.select_for_update().get(id=borrow_record.book_id)

    # 更新借阅记录
    borrow_record.return_date = timezone.now()
    borrow_record.status = 'returned'
    borrow_record.save()

    # 更新库存
    book.available_copies += 1
    book.save()

    messages.success(request, f'《{book.title}》归还成功')
    return redirect('bookstore:borrow_record_list')


@login_required
def book_search(request):
    """书籍搜索"""
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')

    books = Book.objects.filter(is_active=True)

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author_name__icontains=query) |
            Q(isbn__icontains=query) |
            Q(publisher__icontains=query)
        ).distinct()

    if category:
        books = books.filter(category=category)

    categories = Book.CATEGORY_CHOICES

    return render(request, 'bookstore/book_search.html', {
        'books': books,
        'query': query,
        'category': category,
        'categories': categories,
    })


# ==================== User Management Views ====================

@login_required
def admin_info_view(request):
    """管理员视图 - 用户管理"""
    if not request.user.is_superuser:
        messages.error(request, '您没有权限访问此页面')
        return redirect('bookstore:first_page')

    page = request.GET.get('page', 1)
    query = request.GET.get('q', '')

    users = User.objects.all().order_by('-date_joined')

    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query)
        ).distinct()

    # 分页
    paginator = Paginator(users, 20)
    try:
        users_page = paginator.page(page)
    except PageNotAnInteger:
        users_page = paginator.page(1)
    except EmptyPage:
        users_page = paginator.page(paginator.num_pages)

    return render(request, 'bookstore/admin_info.html', {'users': users_page, 'query': query})


@login_required
def reader_profile(request):
    """读者个人信息"""
    if not request.user.is_authenticated:
        return redirect('bookstore:login')

    try:
        reader = request.user.reader_profile
    except Reader.DoesNotExist:
        messages.error(request, '请先完善读者信息')
        return redirect('bookstore:first_page')

    # 获取该读者的借阅记录
    records = BorrowRecord.objects.filter(reader=reader).order_by('-borrow_date')[:10]

    return render(request, 'bookstore/reader_profile.html', {
        'reader': reader,
        'records': records
    })


@login_required
def update_reader_profile(request):
    """更新读者信息"""
    if not request.user.is_authenticated:
        return redirect('bookstore:login')

    try:
        reader = request.user.reader_profile
    except Reader.DoesNotExist:
        reader = None

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        id_card = request.POST.get('id_card', '').strip()
        reader_type = request.POST.get('reader_type', 'student')

        if not name or not phone or not id_card:
            messages.error(request, '姓名、手机号和身份证号都是必填的')
            return redirect('bookstore:reader_profile')

        if reader:
            reader.name = name
            reader.phone = phone
            reader.id_card = id_card
            reader.reader_type = reader_type
            reader.save()
        else:
            Reader.objects.create(
                user=request.user,
                name=name,
                phone=phone,
                id_card=id_card,
                reader_type=reader_type
            )

        messages.success(request, '信息更新成功')
        return redirect('bookstore:reader_profile')

    return redirect('bookstore:reader_profile')


@login_required
@require_POST
def user_delete(request):
    """删除用户"""
    if not request.user.is_superuser:
        messages.error(request, '您没有权限操作')
        return redirect('bookstore:first_page')

    user_id = request.POST.get('user_id')
    if not user_id:
        messages.error(request, '请求异常')
        return redirect('bookstore:admin_info_view')

    try:
        user = User.objects.get(id=user_id)
        if user.is_superuser:
            messages.error(request, '不能删除管理员账户')
            return redirect('bookstore:admin_info_view')
        user.delete()
        messages.success(request, '用户已删除')
    except User.DoesNotExist:
        messages.error(request, '用户不存在')

    return redirect('bookstore:admin_info_view')


# ==================== Statistics & Overdue Views ====================

@login_required
def overdue_management(request):
    """逾期管理"""
    if not request.user.is_superuser:
        messages.error(request, '您没有权限访问此页面')
        return redirect('bookstore:first_page')

    page = request.GET.get('page', 1)
    overdue_records = BorrowRecord.objects.filter(
        status='borrowed',
        due_date__lt=datetime.date.today()
    ).select_related('reader', 'book')

    # 计算罚款
    for record in overdue_records:
        record.calculated_fine = record.days_overdue * 0.5

    # 分页
    paginator = Paginator(overdue_records, 15)
    try:
        records_page = paginator.page(page)
    except PageNotAnInteger:
        records_page = paginator.page(1)
    except EmptyPage:
        records_page = paginator.page(paginator.num_pages)

    return render(request, 'bookstore/overdue_management.html', {
        'overdue_records': records_page
    })


@login_required
def statistics(request):
    """统计报表"""
    if not request.user.is_superuser:
        messages.error(request, '您没有权限访问此页面')
        return redirect('bookstore:first_page')

    # 总体统计
    total_books = Book.objects.filter(is_active=True).count()
    total_borrowed = BorrowRecord.objects.count()
    total_readers = Reader.objects.filter(is_active=True).count()

    # 今日统计
    today = datetime.date.today()
    today_borrowed = BorrowRecord.objects.filter(borrow_date__date=today).count()
    today_returned = BorrowRecord.objects.filter(return_date__date=today).count()

    # 逾期统计
    overdue_count = BorrowRecord.objects.filter(
        status='borrowed',
        due_date__lt=today
    ).count()

    # 热门图书 TOP 10
    popular_books = Book.objects.annotate(
        borrow_count=Count('borrow_records')
    ).filter(is_active=True).order_by('-borrow_count')[:10]

    # 分类统计
    category_stats = Book.objects.filter(is_active=True).values('category').annotate(
        count=Count('id')
    ).order_by('-count')

    # 出版社统计 TOP 5
    publisher_stats = Book.objects.filter(is_active=True).values('publisher').annotate(
        count=Count('id')
    ).order_by('-count')[:5]

    return render(request, 'bookstore/statistics.html', {
        'total_books': total_books,
        'total_borrowed': total_borrowed,
        'total_readers': total_readers,
        'today_borrowed': today_borrowed,
        'today_returned': today_returned,
        'overdue_count': overdue_count,
        'popular_books': popular_books,
        'category_stats': category_stats,
        'publisher_stats': publisher_stats,
    })


# ==================== Author Management Views ====================

@login_required
def author_list(request):
    """作者列表"""
    query = request.GET.get('q', '')
    page = request.GET.get('page', 1)

    authors = Author.objects.all()

    if query:
        authors = authors.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(country__icontains=query)
        ).distinct()

    paginator = Paginator(authors, 20)
    try:
        authors_page = paginator.page(page)
    except PageNotAnInteger:
        authors_page = paginator.page(1)
    except EmptyPage:
        authors_page = paginator.page(paginator.num_pages)

    return render(request, 'bookstore/author_list.html', {
        'authors': authors_page,
        'query': query
    })


@login_required
@transaction.atomic
def author_create(request):
    """创建作者"""
    if not request.user.is_superuser:
        messages.error(request, '您没有权限操作')
        return redirect('bookstore:first_page')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        age = request.POST.get('age', 1)
        email = request.POST.get('email', '').strip()
        country = request.POST.get('country', '中国').strip()
        bio = request.POST.get('bio', '').strip()

        if not name:
            messages.error(request, '作者姓名不能为空')
            return redirect('bookstore:author_list')

        if email and Author.objects.filter(email=email).exists():
            messages.error(request, '该邮箱已被使用')
            return redirect('bookstore:author_list')

        Author.objects.create(
            name=name,
            age=age,
            email=email or None,
            country=country,
            bio=bio
        )

        messages.success(request, '作者创建成功')
        return redirect('bookstore:author_list')

    return redirect('bookstore:author_list')


# ==================== Helper Views ====================

def get_publishers(request):
    """获取出版社列表（用于下拉框）"""
    publishers = Book.objects.values_list('publisher', flat=True).distinct()
    publishers_list = list(publishers)
    return JsonResponse(publishers_list, safe=False)


def get_authors(request):
    """获取作者列表"""
    authors = Author.objects.values_list('id', 'name')
    authors_list = [{'id': a[0], 'name': a[1]} for a in authors]
    return JsonResponse(authors_list, safe=False)


def test_static(request):
    """测试静态文件"""
    return render(request, 'test_static.html')


def error_page(request, message="操作失败"):
    """通用错误页面"""
    return render(request, 'bookstore/error_page.html', {'message': message})


# ==================== Legacy Compatibility Views ====================

@login_required
def cussotom_user_info(request):
    """读者信息管理（兼容旧版）"""
    if not request.user.is_superuser:
        # 非管理员用户查看自己的信息
        user = request.user
        user_info = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '',
            'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S')
        }
        return render(request, 'bookstore/my_template.html', {'user': user_info})

    # 管理员查看所有读者信息
    readers = Reader.objects.all()
    return render(request, 'bookstore/cussotom_user_info.html', {'readers': readers})


@login_required
def user_update(request, user_id):
    """更新读者信息（兼容旧版）"""
    if not request.user.is_superuser:
        messages.error(request, '您没有权限操作')
        return redirect('bookstore:first_page')

    try:
        reader_obj = Reader.objects.get(id=user_id)
    except Reader.DoesNotExist:
        messages.error(request, '读者不存在')
        return redirect('bookstore:cussotom_user_info')

    if request.method == 'POST':
        reader_obj.name = request.POST.get('name', '')
        reader_obj.phone = request.POST.get('phone', '')
        reader_obj.id_card = request.POST.get('id_card', '')
        reader_obj.reader_type = request.POST.get('reader_type', 'student')
        reader_obj.save()
        messages.success(request, '更新成功')
        return redirect('bookstore:cussotom_user_info')

    return render(request, 'bookstore/user_update.html', {'reader': reader_obj})


@login_required
def update_admin1_view(request, user_id):
    """更新管理员信息"""
    if not request.user.is_superuser:
        messages.error(request, '您没有权限操作')
        return redirect('bookstore:first_page')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, '用户不存在')
        return redirect('bookstore:admin_info_view')

    if request.method == 'POST':
        is_superuser = request.POST.get('is_superuser', '').lower()
        user.is_superuser = is_superuser in ('true', '1', 'yes')
        user.save()
        messages.success(request, '更新成功')
        return redirect('bookstore:admin_info_view')

    return render(request, 'bookstore/admin_update.html', {'user_id': user_id, 'user': user})
