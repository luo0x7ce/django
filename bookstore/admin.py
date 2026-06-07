from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Author, Book, Reader, BorrowRecord


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    """作者模型管理"""
    list_display = ('name', 'age', 'email', 'country', 'bio', 'created_at')
    list_filter = ('country', 'created_at')
    search_fields = ('name', 'email')
    ordering = ('name',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """图书模型管理"""
    list_display = (
        'isbn', 'title', 'author_name', 'publisher', 'price',
        'market_price', 'category', 'shelf_location',
        'total_copies', 'available_copies', 'is_active', 'record'
    )
    list_filter = ('category', 'publisher', 'record', 'is_active')
    search_fields = ('isbn', 'title', 'author_name', 'publisher', 'record')
    date_hierarchy = 'record_time'
    ordering = ('-record_time',)
    list_editable = ('available_copies', 'is_active')

    fieldsets = (
        ('基本信息', {
            'fields': ('isbn', 'title', 'author', 'author_name', 'publisher', 'publish_date')
        }),
        ('库存与价格', {
            'fields': ('price', 'market_price', 'total_copies', 'available_copies', 'shelf_location')
        }),
        ('分类与状态', {
            'fields': ('category', 'is_active', 'record')
        }),
        ('详细信息', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('record_time', 'updated_time')


@admin.register(Reader)
class ReaderAdmin(admin.ModelAdmin):
    """读者模型管理"""
    list_display = (
        'name', 'user', 'phone', 'id_card',
        'reader_type', 'max_borrow_count', 'current_borrow_count',
        'is_active', 'created_at'
    )
    list_filter = ('reader_type', 'is_active', 'created_at')
    search_fields = ('name', 'phone', 'id_card', 'user__username')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_editable = ('is_active', 'max_borrow_count')

    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'name', 'phone', 'id_card')
        }),
        ('读者信息', {
            'fields': ('reader_type', 'max_borrow_count', 'is_active')
        }),
    )

    readonly_fields = ('created_at',)


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    """借阅记录模型管理"""
    list_display = (
        'reader', 'book', 'borrow_date', 'due_date',
        'return_date', 'status', 'fine_amount', 'fine_paid', 'operator'
    )
    list_filter = ('status', 'fine_paid', 'borrow_date', 'due_date', 'return_date')
    search_fields = ('reader__name', 'reader__id_card', 'book__title', 'book__isbn')
    date_hierarchy = 'borrow_date'
    ordering = ('-borrow_date',)
    list_editable = ('status', 'fine_paid', 'fine_amount')
    raw_id_fields = ('reader', 'book', 'operator')

    fieldsets = (
        ('借阅信息', {
            'fields': ('reader', 'book', 'borrow_date', 'due_date')
        }),
        ('归还信息', {
            'fields': ('return_date', 'status')
        }),
        ('罚款信息', {
            'fields': ('fine_amount', 'fine_paid', 'remarks')
        }),
        ('操作信息', {
            'fields': ('operator',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('borrow_date',)


# 自定义Admin站点标题
admin.site.site_header = '图书馆管理系统'
admin.site.site_title = '图书馆管理'
admin.site.index_title = '管理后台'
