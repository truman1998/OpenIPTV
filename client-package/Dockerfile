# 使用一个精简的Python基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制客户端代理的Python代码
COPY client_proxy.py .

# 声明容器内部的服务端口
EXPOSE 8000

# 设置容器启动时执行的命令
# 客户端比较轻量，2个工作进程足矣
CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "client_proxy:app", "--bind", "0.0.0.0:8000"]
