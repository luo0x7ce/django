FROM python:3.8

RUN mkdir /usr/src/app
COPY . /usr/src/app/bookstore
WORKDIR /usr/src/app/bookstore

RUN python -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/
RUN pip install numpy -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 仅收集静态文件（如果不需要数据库的话）
RUN python manage.py collectstatic --noinput

EXPOSE 8881

# 拷贝并设置启动脚本
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python","manage.py","runserver","0.0.0.0:8881"]

