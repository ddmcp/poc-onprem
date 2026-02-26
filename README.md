# poc-onprem
**On-Premises Conversational Query System (chatbot)**
A pipeline that ingests a static PDF corpus into a vector database (Qdrant) via Airflow-orchestrated ETL, enabling semantic search and retrieval-augmented generation using locally hosted LLMs.


## Technology Stack

| Layer | Component |
| :--- | :--- |
| **Orchestration** | Apache Airflow |
| **Backend & APIs** | Python, FastAPI, REST, Swagger |
| **Storage** | MinIO (Object), PostgreSQL (Structured) |
| **Vector Search** | Qdrant (Embeddings & Semantic Retrieval) |
| **AI Layer** | LangChain + Ollama with Private LLM models |
| **Capabilities** | Embeddings, RAG, AI Agents |

---

## Key Advantages

- 🛡️ **Security-first architecture** – Data never leaves your perimeter.
- ☁️ **Cloud agnostic** – Deploy on AWS, Azure, GCP, or on-prem.
- 🔒 **Private GenAI** – Uses your own LLM models by default.
- 📄 **Document intelligence** – Built specifically for PDF-heavy environments.
- 🧩 **Scalable & modular** – Extend with new agents, models, and pipelines.


## The Result
A private, enterprise-grade AI knowledge system that turns your documents into a **secure, searchable, and intelligent decision-support layer**.


## 🚀 Getting Started

Follow these steps to get PDF pipeline up and running.

### 1. Launch Infrastructure
Spin up all services (Postgres, MinIO, Airflow, Qdrant, and Microservices):
```bash
docker-compose up -d
```

### 2. wait for ollama download model and to be ready
```bash
docker logs -f ollama-llm-chat
```
```bash
✅ Ollama is ready and model 'tinyllama' is active.
```

### 3. Configure Airflow
Create admin credentials to access the dashboard:
```bash
docker exec -it airflow-api-server airflow users create \
  --username admin --password admin \
  --firstname Admin --lastname Admin \
  --role Admin \
  --email admin@example.com
```

### 4. Upload Documents
1.  Open **[MinIO Console](http://localhost:9001)** (Login: `minioadmin` / `minioadmin`).
2.  Create a bucket named **`bucket_name`**.
3.  Upload PDF files into this bucket.

### 5. Process the PDFs
1.  Open the **[Airflow UI](http://localhost:8080/dags)** (Login: `admin` / `admin`).
2.  Locate the **`minio_pdf_processor_dag`**.
3.  **Unpause** it and click **Trigger** to start extracting data and generating embeddings.

### 6. Chat with Data
Once processing is complete, test RAG pipeline via the GUI **[Chat UI](http://localhost:8081)**.

The backend documentation:
- **[Search API Swagger](http://localhost:8003/docs)**

---

## 📖 Project Overview

This project implements a complete **Retrieval-Augmented Generation (RAG)** pipeline. It automates the ingestion of PDF documents, extracts semantic information, and enables natural language querying.

- **Orchestration**: Managed by **Apache Airflow 3.x**.
- **Storage**: Files in **MinIO**, Metadata in **Postgres**, Vectors in **Qdrant**.
- **AI Engine**: Local LLM and Embeddings via **Ollama** (`tinyllama` for chat, `nomic-embed-text` for vectors).

### 🏗 Architecture At a Glance

The system is composed of the Airflow ecosystem and specialized microservices:
- **Chat UI Service**: `./services/chat-docs-ui` (Frontend using Nginx)
- **Chat Docs Service**: `./services/chat-docs-service` (FastAPI + RAG Logic)
- **Extraction Service**: `./services/typing-pdf-extractor-service` (FastAPI + OCR/Extraction)
- **Vector DB**: `qdrant-vector-db` (Qdrant)
- **Metadata DB**: `pg-typing-pdf-extractor-db` (Postgres)
- **Airflow DB**: `pg-airflow-db` (Postgres)
- **Object Storage**: `minio` (MinIO)
- **Embedding/LLM Chat**: Ollama services (`ollama-llm-embedding`, `ollama-llm-chat`)

---

## Airflow Orchestration

Airflow is the heart of the project, coordinating data movement and processing.

### 📋 DAG Catalog

- **`minio_pdf_processor_dag`**: The primary pipeline. It monitors MinIO buckets for new PDF uploads and triggers the extraction microservice to process them in real-time.
- **`hello_world_dag`**: A simple diagnostic DAG to verify scheduler health.
- **`debug_test_dag`**: Used for testing internal API connections and core Airflow variables.

### 🛠 Working with DAGs

#### Adding New Logic
1.  Place your `.py` files in the `./dags` folder.
2.  The **DAG Processor** will automatically detect and serialize them within seconds.
3.  Check the status via CLI:
    ```bash
    docker exec -it airflow-api-server airflow dags list
    ```

#### Monitoring & Logs
Tracking task execution is critical. Use these commands to inspect the scheduler's behavior:
```bash
# Check if the scheduler sees your file
docker logs airflow-scheduler | grep your_dag_name.py

# Get logs for a specific task instance
docker exec -it airflow-scheduler airflow tasks logs <dag_id> <task_id> <run_id>
```

#### Manual Triggering & Testing
To bypass the sensor and run a DAG immediately:
```bash
# Test a specific task without running the whole DAG
docker exec -it airflow-api-server airflow tasks test <dag_id> <task_id> 2024-01-01

# Trigger a full DAG run
docker exec -it airflow-scheduler airflow dags trigger <dag_id>
```

---

## 📁 Project Organization

This project follows a **Microservice Architecture** and **12-Factor App** principles, ensuring that each component is independent, containerized, and easily configurable.

### 📌 Architecture Principles
- **Separation of Concerns**: Parsing, Embedding, and Chat logic are split into independent services.
- **Data Persistence**: All critical data is stored in the `/volumes` directory and ignored by Git.
- **Environment Driven**: Configuration is managed via environment variables in the `docker-compose.yml` and `.env` files.
- **Local AI**: All LLM processing happens on your machine via private Ollama instances.



## 🐞 Developer Experience (DX)

#### Debugging DAGs in VS Code
The environment is pre-configured for remote debugging using `debugpy`.

1.  Add this to your `.vscode/launch.json`:
    ```json
    {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Airflow: Attach to Docker",
                "type": "debugpy",
                "request": "attach",
                "connect": { "host": "localhost", "port": 5678 },
                "pathMappings": [
                    { "localRoot": "${workspaceFolder}/dags", "remoteRoot": "/opt/airflow/dags" }
                ]
            }
        ]
    }
    ```
2.  Run the task with the debug flag:
    ```bash
    docker exec -it -e AIRFLOW_DEBUG=true airflow-scheduler airflow tasks test <dag_id> <task_id> 2026-01-01
    ```

#### Debug the Fast API application:
    ```bash
    {
    "version": "0.2.0",
    "configurations": [        
        {
            "name": "Python: Attach to Airflow in Docker",
            "type": "debugpy",
            "request": "attach",
            "connect": {
                "host": "localhost",
                "port": 5678
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}/dags",
                    "remoteRoot": "/opt/airflow/dags"
                }
            ],
            "justMyCode": true
        }    
    ]
}
    ```

---

## 🏷 Tags
`Airflow 3.x` • `MinIO` • `Qdrant` • `PostgreSQL` • `RAG` • `Docker` • `Python` • `FastAPI` • `Ollama` • `LLM` • `GenAI`
