FROM python:3.11

WORKDIR /app
ADD ./app /app
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]