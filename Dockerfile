# 使用官方的 Python 镜像作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制 requirements.txt 并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 运行 Streamlit 应用
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
