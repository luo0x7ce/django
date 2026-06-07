from django.urls import path
from . import views

app_name = 'bookstore'

urlpatterns = [
    # Authentication
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('register', views.register, name='register'),
    path('password_reset', views.password_reset, name='password_reset'),

    # Main pages
    path('first_page', views.first_page, name='first_page'),
    path('', views.index, name='home'),

    # Book management
    path('index', views.index, name='index'),
    path('books/add', views.add_book, name='add_book'),
    path('books/<int:book_id>/edit', views.update_book, name='update_book'),
    path('books/<int:book_id>/delete', views.delete_book, name='delete_book'),
    path('books/batch_delete', views.batch_delete, name='batch_delete'),
    path('books/search', views.book_search, name='book_search'),
    path('api/publishers', views.get_publishers, name='get_publishers'),
    path('api/authors', views.get_authors, name='get_authors'),

    # Borrow/Return
    path('borrow', views.borrow_book, name='borrow_book'),
    path('records', views.borrow_record_list, name='borrow_record_list'),
    path('records/<int:record_id>/return', views.return_book, name='return_book'),

    # Reader profile
    path('profile', views.reader_profile, name='reader_profile'),
    path('profile/update', views.update_reader_profile, name='update_reader_profile'),

    # User management
    path('admin/users', views.admin_info_view, name='admin_info_view'),
    path('admin/users/<int:user_id>/edit', views.update_admin1_view, name='update_admin1_view'),
    path('admin/users/delete', views.user_delete, name='user_delete'),

    # Author management
    path('authors', views.author_list, name='author_list'),
    path('authors/create', views.author_create, name='author_create'),

    # Statistics and overdue
    path('overdue', views.overdue_management, name='overdue_management'),
    path('statistics', views.statistics, name='statistics'),

    # Error page
    path('error', views.error_page, name='error_page'),

    # Test
    path('test_static', views.test_static, name='test_static'),
]
