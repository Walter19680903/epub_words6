# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安裝必要套件
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 確保 `book_list/books.json`,  `cache/` 及 `data/` 被包含
COPY html html
COPY words6_json words6_json
COPY app.py .
COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
