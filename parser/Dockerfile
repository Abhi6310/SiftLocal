FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
#keep alive for networking; invoke via: docker exec -i parser python -m worker
CMD ["sleep", "infinity"]
