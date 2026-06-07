from django.core.management.base import BaseCommand
from bookstore.models import Author, Book
from decimal import Decimal


class Command(BaseCommand):
    help = '导入示例图书数据到数据库'

    def handle(self, *args, **options):
        # 经典文学
        classics = [
            {"title": "红楼梦", "Author": "曹雪芹", "Publisher": "人民文学出版社", "Price": 68.00, "Category": "fiction", "ISBN": "9787020002207"},
            {"Title": "西游记", "Author": "吴承恩", "Publisher": "人民文学出版社", "Price": 45.00, "Category": "fiction", "ISBN": "9787020008736"},
            {"Title": "水浒传", "Author": "施耐庵", "Publisher": "人民文学出版社", "Price": 55.00, "Category": "fiction", "ISBN": "9787020008729"},
            {"Title": "三国演义", "Author": "罗贯中", "Publisher": "人民文学出版社", "Price": 52.00, "Category": "fiction", "ISBN": "9787020008743"},
            {"Title": "活着", "Author": "余华", "Publisher": "作家出版社", "Price": 28.00, "Category": "fiction", "ISBN": "9787506365437"},
            {"Title": "围城", "Author": "钱钟书", "Publisher": "人民文学出版社", "Price": 32.00, "Category": "fiction", "ISBN": "9787020024758"},
        ]

        # 外国文学
        foreign_literature = [
            {"Title": "百年孤独", "Author": "加西亚·马尔克斯", "Publisher": "南海出版公司", "Price": 39.50, "Category": "fiction", "ISBN": "9787544253994"},
            {"Title": "追风筝的人", "Author": "卡勒德·胡赛尼", "Publisher": "上海人民出版社", "Price": 29.00, "Category": "fiction", "ISBN": "9787208061644"},
            {"Title": "解忧杂货店", "Author": "东野圭吾", "Publisher": "南海出版公司", "Price": 39.00, "Category": "fiction", "ISBN": "9787544270878"},
            {"Title": "挪威的森林", "Author": "村上春树", "Publisher": "上海译文出版社", "Price": 35.00, "Category": "fiction", "ISBN": "9787532743729"},
            {"Title": "小王子", "Author": "安托万·德·圣-埃克苏佩里", "Publisher": "人民文学出版社", "Price": 22.00, "Category": "fiction", "ISBN": "9787020048440"},
        ]

        # 科技技术
        tech_books = [
            {"Title": "Python编程：从入门到实践", "Author": "埃里克·马瑟斯", "Publisher": "人民邮电出版社", "Price": 89.00, "Category": "technology", "ISBN": "9787115428028"},
            {"Title": "算法导论", "Author": "Thomas H.Cormen", "Publisher": "机械工业出版社", "Price": 128.00, "Category": "technology", "ISBN": "9787111407013"},
            {"Title": "深入理解计算机系统", "Author": "Randal E.Bryant", "Publisher": "机械工业出版社", "Price": 139.00, "Category": "technology", "ISBN": "9787111541359"},
            {"Title": "JavaScript高级程序设计", "Author": "Nicholas C.Zakas", "Publisher": "人民邮电出版社", "Price": 99.00, "Category": "technology", "ISBN": "9787115271464"},
            {"Title": "Django企业开发实战", "Author": "黄雷", "Publisher": "人民邮电出版社", "Price": 79.00, "Category": "technology", "ISBN": "9787115511560"},
            {"Title": "Effective Java", "Author": "Joshua Bloch", "Publisher": "电子工业出版社", "Price": 89.00, "Category": "technology", "ISBN": "9787111251210"},
        ]

        # 历史文化
        history_books = [
            {"Title": "万历十五年", "Author": "黄仁宇", "Publisher": "中华书局", "Price": 18.00, "Category": "history", "ISBN": "9787101054288"},
            {"Title": "人类简史", "Author": "尤瓦尔·赫拉利", "Publisher": "中信出版社", "Price": 68.00, "Category": "history", "ISBN": "9787508647357"},
            {"Title": "明朝那些事儿", "Author": "当年明月", "Publisher": "北京联合出版公司", "Price": 358.00, "Category": "history", "ISBN": "9787559603109"},
            {"Title": "全球通史", "Author": "斯塔夫里阿诺斯", "Publisher": "北京大学出版社", "Price": 88.00, "Category": "history", "ISBN": "9787301173540"},
        ]

        # 科普
        science_books = [
            {"Title": "时间简史", "Author": "史蒂芬·霍金", "Publisher": "湖南科学技术出版社", "Price": 45.00, "Category": "science", "ISBN": "9787535732309"},
            {"Title": "从一到无穷大", "Author": "乔治·伽莫夫", "Publisher": "天津人民出版社", "Price": 38.00, "Category": "science", "ISBN": "9787201088541"},
            {"Title": "自私的基因", "Author": "理查德·道金斯", "Publisher": "中信出版社", "Price": 68.00, "Category": "science", "ISBN": "9787508634159"},
        ]

        # 教育
        education_books = [
            {"Title": "窗边的小豆豆", "Author": "黑柳彻子", "Publisher": "南海出版公司", "Price": 35.00, "Category": "education", "ISBN": "9787544248730"},
            {"Title": "自卑与超越", "Author": "阿尔弗雷德·阿德勒", "Publisher": "商务印书馆", "Price": 29.00, "Category": "education", "ISBN": "9787100011144"},
        ]

        all_books = classics + foreign_literature + tech_books + history_books + science_books + education_books

        created_count = 0
        skipped_count = 0

        for book_data in all_books:
            title = book_data.get('Title', book_data.get('title', ''))
            author_name = book_data.get('Author', book_data.get('author', ''))

            # 检查是否已存在
            if Book.objects.filter(title=title).exists():
                skipped_count += 1
                self.stdout.write(f"跳过(已存在): {title}")
                continue

            # 获取或创建作者
            author, _ = Author.objects.get_or_create(
                name=author_name,
                defaults={'country': '未知'}
            )

            # 创建图书
            Book.objects.create(
                isbn=book_data.get('ISBN', ''),
                title=title,
                author=author,
                author_name=author_name,
                publisher=book_data.get('Publisher', ''),
                price=Decimal(str(book_data.get('Price', 0))),
                market_price=Decimal(str(book_data.get('Price', 0))),
                category=book_data.get('Category', 'other'),
                total_copies=3,
                available_copies=3,
                shelf_location='A-1-1',
                record='system'
            )
            created_count += 1
            self.stdout.write(f"创建: {title}")

        self.stdout.write(self.style.SUCCESS(f"\n导入完成! 新增: {created_count} 本, 跳过: {skipped_count} 本"))
