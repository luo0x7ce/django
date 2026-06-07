from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import datetime
import secrets


class APIToken(models.Model):
    """API Token 模型 - 用于 MCP Server 认证"""
    key = models.CharField('Token', max_length=64, unique=True, db_index=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='api_tokens',
        verbose_name='用户'
    )
    name = models.CharField('Token名称', max_length=100, default='MCP Token')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    last_used_at = models.DateTimeField('最后使用时间', null=True, blank=True)
    is_active = models.BooleanField('是否激活', default=True)

    class Meta:
        db_table = 'api_token'
        verbose_name = 'API Token'
        verbose_name_plural = 'API Token'

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    @classmethod
    def generate_token(cls, user: User, name: str = 'MCP Token') -> tuple:
        """
        为用户生成一个新的 API Token。
        返回 (token对象, token字符串) - token字符串只在创建时返回一次，需要妥善保存
        """
        # 生成安全的随机 token
        token_key = secrets.token_urlsafe(32)
        token = cls.objects.create(
            key=token_key,
            user=user,
            name=name
        )
        return token, token_key

    def rotate_key(self) -> str:
        """轮换 token key，返回新 key"""
        self.key = secrets.token_urlsafe(32)
        self.save(update_fields=['key'])
        return self.key


class Author(models.Model):
    """作者模型"""
    name = models.CharField('姓名', max_length=100)
    age = models.IntegerField('年龄', default=1)
    email = models.EmailField('邮箱', max_length=254, unique=True, null=True, blank=True)
    country = models.CharField('国家', max_length=50, default='中国')
    bio = models.TextField('简介', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'author'
        ordering = ['name']
        verbose_name = '作者'
        verbose_name_plural = '作者'

    def __str__(self):
        return self.name


class Book(models.Model):
    """图书模型"""
    CATEGORY_CHOICES = [
        ('fiction', '小说'),
        ('science', '科学'),
        ('technology', '技术'),
        ('history', '历史'),
        ('art', '艺术'),
        ('education', '教育'),
        ('other', '其他'),
    ]

    isbn = models.CharField('ISBN', max_length=13, unique=True, null=True, blank=True)
    title = models.CharField('书名', max_length=200)
    author = models.ForeignKey(
        Author,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='books',
        verbose_name='作者'
    )
    author_name = models.CharField('作者名称', max_length=100, default='', help_text='如果未选择作者，可直接填写作者名')
    publisher = models.CharField('出版社', max_length=200)
    publish_date = models.DateField('出版日期', null=True, blank=True)
    price = models.DecimalField('价格', max_digits=10, decimal_places=2)
    market_price = models.DecimalField('零售价', max_digits=10, decimal_places=2)
    category = models.CharField('分类', max_length=20, choices=CATEGORY_CHOICES, default='other')
    shelf_location = models.CharField('书架位置', max_length=50, default='A-1-1')
    total_copies = models.PositiveIntegerField('总库存', default=1)
    available_copies = models.PositiveIntegerField('可借数量', default=1)
    description = models.TextField('简介', blank=True)
    record = models.CharField('登记人', max_length=100, default='')
    record_time = models.DateTimeField(auto_now=True)
    updated_time = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField('是否可借', default=True)

    class Meta:
        db_table = 'book'
        ordering = ['-record_time']
        verbose_name = '图书'
        verbose_name_plural = '图书'

    def __str__(self):
        author_str = self.author.name if self.author else self.author_name
        return f"{self.title} - {author_str}"

    def save(self, *args, **kwargs):
        # 如果没有提供作者名但选择了作者对象，使用作者对象的名字
        if self.author and not self.author_name:
            self.author_name = self.author.name
        # 确保可借数量不超过总库存
        if self.available_copies > self.total_copies:
            self.available_copies = self.total_copies
        super().save(*args, **kwargs)


class Reader(models.Model):
    """读者模型 - 关联 Django User"""
    READER_TYPE_CHOICES = [
        ('student', '学生'),
        ('teacher', '教师'),
        ('staff', '职工'),
        ('guest', '访客'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='reader_profile',
        null=True,
        blank=True
    )
    name = models.CharField('姓名', max_length=100)
    phone = models.CharField('手机号', max_length=11)
    id_card = models.CharField('身份证号', max_length=18)
    reader_type = models.CharField('读者类型', max_length=20, choices=READER_TYPE_CHOICES, default='student')
    max_borrow_count = models.PositiveIntegerField('最大借书数', default=5)
    is_active = models.BooleanField('是否激活', default=True)
    created_at = models.DateTimeField('注册时间', auto_now_add=True)

    class Meta:
        db_table = 'reader'
        ordering = ['-created_at']
        verbose_name = '读者'
        verbose_name_plural = '读者'

    def __str__(self):
        user_str = f"({self.user.username})" if self.user else ""
        return f"{self.name}{user_str}"

    @property
    def current_borrow_count(self):
        """当前借阅数量"""
        return self.borrow_records.filter(return_date__isnull=True).count()

    @property
    def can_borrow(self):
        """是否可以继续借书"""
        return self.current_borrow_count < self.max_borrow_count


class BorrowRecord(models.Model):
    """借阅记录模型"""
    STATUS_CHOICES = [
        ('borrowed', '借阅中'),
        ('returned', '已归还'),
        ('overdue', '已逾期'),
        ('lost', '已遗失'),
    ]

    reader = models.ForeignKey(
        Reader,
        on_delete=models.CASCADE,
        related_name='borrow_records',
        verbose_name='读者'
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='borrow_records',
        verbose_name='图书'
    )
    borrow_date = models.DateTimeField('借书时间', auto_now_add=True)
    due_date = models.DateField('应还书时间')
    return_date = models.DateTimeField('归还时间', null=True, blank=True)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='borrowed')
    fine_amount = models.DecimalField('罚款金额', max_digits=10, decimal_places=2, default=0)
    fine_paid = models.BooleanField('罚款已付', default=False)
    operator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_borrows',
        verbose_name='操作员'
    )
    remarks = models.TextField('备注', blank=True)

    class Meta:
        db_table = 'borrow_record'
        ordering = ['-borrow_date']
        verbose_name = '借阅记录'
        verbose_name_plural = '借阅记录'

    def __str__(self):
        return f"{self.reader.name} 借阅 {self.book.title}"

    @property
    def is_overdue(self):
        """是否逾期"""
        if self.status == 'borrowed' and self.due_date:
            return timezone.now().date() > self.due_date
        return False

    @property
    def days_overdue(self):
        """逾期天数"""
        if self.is_overdue:
            return (timezone.now().date() - self.due_date).days
        return 0

    def save(self, *args, **kwargs):
        # 自动更新状态
        if self.return_date and self.status == 'borrowed':
            self.status = 'returned'
        elif self.is_overdue and self.status == 'borrowed':
            self.status = 'overdue'
        super().save(*args, **kwargs)


# ============== 旧模型兼容层（用于数据迁移） ==============
# 以下模型仅用于兼容旧数据迁移，过渡期后可删除

class LegacyShu(models.Model):
    """旧图书模型 - 仅用于数据迁移"""
    isbn = models.CharField(max_length=13, unique=True, null=True, blank=True)
    title = models.CharField('书名', max_length=50, default='')
    pub = models.CharField('出版社', max_length=100, default='')
    price = models.DecimalField('价格', max_digits=7, decimal_places=2)
    market_price = models.DecimalField('零售价', max_digits=7, decimal_places=2, default=0.0)
    record = models.CharField('登记人', max_length=100, default='')
    record_time = models.DateTimeField(auto_now=True)
    updated_time = models.DateTimeField(auto_now=True)
    shu_nub = models.IntegerField('数量', default=1)
    author11_name = models.CharField('作者', max_length=11, default='')
    shu_jia = models.CharField('书架', max_length=20, default="杂学书架")

    class Meta:
        db_table = 'shu'

    def __str__(self):
        return '%s_%s' % (self.id, self.title)


class LegacyCustomer(models.Model):
    """旧读者模型 - 仅用于数据迁移"""
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    identity_info = models.CharField(max_length=255)
    contact_info = models.CharField(max_length=100)

    class Meta:
        db_table = 'customer'


class LegacyCusstom(models.Model):
    """旧借阅记录 - 仅用于数据迁移"""
    name = models.CharField(max_length=1111)
    age = models.IntegerField('年龄', default=1)
    iden_type = models.CharField('证件类型', max_length=1111)
    iden = models.CharField('身份证信息', max_length=18)
    contact_details = models.CharField('联系方式', max_length=11, null=True)
    book = models.ForeignKey(
        LegacyShu,
        on_delete=models.CASCADE,
        related_name='legacy_borrow_records'
    )
    reader_type = models.CharField('读者类型', max_length=1111)
    jie_num = models.PositiveIntegerField('借书数量', default=1)
    borrow_date = models.DateTimeField('借书时间', default=timezone.now)
    due_date = models.DateField('应还书时间')
    return_date = models.DateTimeField("归还时间", null=True, blank=True)
    returned = models.BooleanField(default=False)

    class Meta:
        db_table = 'Cusstom'

    def __str__(self):
        return f"{self.book.title} borrowed by {self.name}"
