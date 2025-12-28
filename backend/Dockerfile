FROM python:3.11-slim
WORKDIR /app

#SQLCipher dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libsqlcipher-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

#copy backend requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#install spaCy model at build time
RUN python -m spacy download en_core_web_lg
RUN python -c "import spacy; spacy.load('en_core_web_lg')"

#copy parser requirements and install
COPY parser/requirements.txt parser-requirements.txt
RUN pip install --no-cache-dir -r parser-requirements.txt

#copy parser source
COPY parser /parser

#copy backend source
COPY backend .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
