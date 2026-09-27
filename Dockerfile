FROM python:3.12-slim

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY tests ./tests
COPY conftest.py pytest.ini ./

ENV PORT=8080
EXPOSE 8080

# 服务挂在固定端口 8080；容器内执行测试：docker run --rm <image> pytest
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
