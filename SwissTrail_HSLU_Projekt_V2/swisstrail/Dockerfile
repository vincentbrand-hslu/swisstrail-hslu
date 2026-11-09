FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py trail_data.py ./
COPY static/ ./static/
ENV SWISSTRAIL_DB=/data/swisstrail.db
EXPOSE 8000
CMD ["sh","-c","exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
