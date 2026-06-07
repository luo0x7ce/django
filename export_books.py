#!/usr/bin/env python
"""导出书籍列表到Excel"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite3.settings')
django.setup()

import pandas as pd
from bookstore.models import Book

# 获取所有书籍数据
books = Book.objects.all().values(
    'isbn',
    'title',
    'author__name',
    'author_name',
    'publisher',
    'publish_date',
    'price',
    'market_price',
    'category',
    'shelf_location',
    'total_copies',
    'available_copies',
    'description',
    'record',
    'record_time',
    'is_active'
)

# 转换为DataFrame
df = pd.DataFrame(list(books))

# 重命名列
df.columns = ['ISBN', '书名', '作者(关联)', '作者名称', '出版社', '出版日期',
              '价格', '零售价', '分类', '书架位置', '总库存', '可借数量',
              '简介', '登记人', '登记时间', '是否可借']

# 合并作者信息
df['作者'] = df['作者(关联)'].fillna(df['作者名称'])
df = df.drop(['作者(关联)', '作者名称'], axis=1)

# 分类转换
category_map = dict(Book.CATEGORY_CHOICES)
df['分类'] = df['分类'].map(category_map).fillna(df['分类'])

# 是否可借转换
df['是否可借'] = df['是否可借'].map({True: '是', False: '否'})

# 格式化日期
df['出版日期'] = pd.to_datetime(df['出版日期'], errors='coerce').dt.strftime('%Y-%m-%d')
df['登记时间'] = pd.to_datetime(df['登记时间'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')

# 调整列顺序
df = df[['ISBN', '书名', '作者', '出版社', '出版日期', '价格', '零售价',
         '分类', '书架位置', '总库存', '可借数量', '简介', '登记人', '登记时间', '是否可借']]

# 保存到Excel
output_path = os.path.join(os.path.dirname(__file__), 'books_export.xlsx')
df.to_excel(output_path, index=False, engine='openpyxl')

print(f"成功导出 {len(df)} 条书籍记录到: {output_path}")