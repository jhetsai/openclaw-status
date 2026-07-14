FROM python:3.11-slim

# 安裝系統工具 + cron
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Python 套件
RUN pip install --no-cache-dir \
    boto3 \
    requests \
    pandas \
    lxml \
    beautifulsoup4 \
    fake-useragent \
    ujson

# 時區
ENV TZ=Asia/Taipei
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# 複製 entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# 複製 cron 排程（在 build 時寫入，container start 時已存在）
COPY cron.d/ /etc/cron.d/
RUN chmod 0644 /etc/cron.d/*

ENTRYPOINT ["/app/entrypoint.sh"]
