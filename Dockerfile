FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py services.py registrations.py giving.py calendar_events.py .

EXPOSE 8000

CMD ["python", "server.py"]
