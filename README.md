# Data Assistant

Streamlit app for synthetic data generation and natural language SQL queries using Gemini.

## Setup

### 1. Prerequisites
```bash
docker --version
python --version
gcloud --version
```

### 2. GCP Auth
```bash
gcloud auth login
gcloud config set project gd-gcp-gridu-genai
gcloud auth application-default login
```

### 3. Start Infrastructure
```bash
docker compose up -d
```

### 4. Langfuse Setup
1. Open http://localhost:3000
2. Create account
3. Settings → API Keys → Generate
4. Copy keys to `.env`

### 5. Environment Variables
```bash
cp .env.example .env
# Edit .env with your keys
```

### 6. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 7. Run
```bash
streamlit run app.py
```

## Structure
```
Data_Assistant/
├── app.py
├── requirements.txt
├── docker-compose.yml
├── .env.example
├── README.md
├── generator/
│   ├── __init__.py
│   ├── ddl_parser.py
│   ├── data_generator.py
│   └── gemini_client.py
├── chat/
│   ├── __init__.py
│   ├── chat_engine.py
│   ├── sql_generator.py
│   ├── db_executor.py
│   └── guardrails.py
├── database/
│   ├── __init__.py
│   └── db_setup.py
└── utils/
    ├── __init__.py
    ├── file_utils.py
    └── visualization.py
```

## Usage

### Phase 1: Data Generation
1. Upload DDL file
2. Add optional instructions
3. Click Generate
4. Preview and download

### Phase 2: Talk to Data
1. Ask questions in natural language
2. View SQL and results
3. Request charts with "plot" or "chart"

## Cleanup
```bash
docker compose down
docker volume prune
gcloud projects delete gd-gcp-gridu-genai
```
# Prompt-Engineering-AI-application
