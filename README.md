# All Back-end Services

This repository contains multiple services that work together to process and analyze Apache logs.

## Middleware

The middleware service handles log ingestion and Kafka message production.

### Setup & Installation

1. Navigate to the middleware directory:
```sh
cd middleware
```

2. Install dependencies:
```sh
npm install
```

3. Run the service:
```sh
node sendLog.js
```

The middleware service will run on http://localhost:5000.

## Docker (Kafka + Zookeeper + ELK)

The ELK stack (Elasticsearch, Logstash, Kibana) and Kafka infrastructure.

### Prerequisites
- Docker
- Docker Compose

### Setup & Running

1. Start all services:
```sh
docker-compose up -d
```

2. Verify services are running:
```sh
docker-compose ps
```

### Service URLs
- Kafka: localhost:9092, localhost:9093
- Elasticsearch: http://localhost:9200
- Kibana: http://localhost:5601
- Logstash: localhost:5044

### Stopping Services
```sh
docker-compose down
```

## LLM API

The LLM API service provides log analysis using OpenAI and Google's Gemini models.

### Setup & Installation

1. Navigate to the LLM API directory:
```sh
cd llm_api
```

2. Create and activate virtual environment:
```sh
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```sh
pip install -r requirements.txt
```

4. Set up environment variables:
- Copy .env.example to .env (if exists)
- Add your API keys:
  - OPENAI_API_KEY
  - GEMINI_API_KEY
  - MONGODB_URI
  - NOTIFICATION_URL

5. Run the service:
```sh
python main.py
```

The LLM API service will run on http://localhost:5000 by default.

### Available Endpoints
- POST /analyze - OpenAI analysis
- POST /gemini - Gemini analysis
- GET /ping - Health check
