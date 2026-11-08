FROM python:3.12-slim

WORKDIR /code

COPY requirements-api.txt .
RUN pip install --no-cache-dir --default-timeout=120 --retries 10 -r requirements-api.txt

COPY api ./api
COPY data ./data

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]