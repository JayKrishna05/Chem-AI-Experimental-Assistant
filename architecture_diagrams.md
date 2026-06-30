# System Architecture Diagrams

This document visualizes the architecture of the AI Chemistry Engine V1 following the completion of Phase 5.

## 1. Overall System Architecture

```mermaid
graph TD
    UI[Next.js Frontend Chat UI]
    API[FastAPI Backend]
    
    subgraph AI Engine
        P[LLM Planner]
        F[LLM Formatter]
    end
    
    subgraph Core Logic
        T[Tool Layer]
        E[Experiment Upload Pipeline]
        S[Comparison Service]
    end
    
    subgraph Data Access Layer
        R[Repositories]
    end
    
    DB[(DuckDB)]
    
    UI <-->|HTTP / SSE| API
    API --> P
    API --> E
    
    P --> T
    E --> S
    
    T --> R
    S --> R
    
    R <--> DB
    T --> F
    F --> UI
```

## 2. Chat Request Pipeline

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant FastAPI
    participant Planner
    participant ToolLayer
    participant Repositories
    participant Formatter

    User->>Frontend: Sends text query
    Frontend->>FastAPI: POST /api/chat
    FastAPI->>Planner: Execute Planner Prompt
    Planner-->>FastAPI: Returns JSON (Tool + Filters)
    FastAPI->>ToolLayer: Dispatches selected tool
    ToolLayer->>Repositories: Calls repository method
    Repositories->>Database: Executes SQL
    Database-->>Repositories: Raw JSON rows
    Repositories-->>ToolLayer: Domain DTOs / Dictionary
    ToolLayer-->>FastAPI: Standardized Response Contract
    FastAPI->>Formatter: Streams Context + Raw JSON
    Formatter-->>Frontend: SSE Markdown Stream
    Frontend-->>User: Renders formatted response
```

## 3. Upload & Comparison Pipeline (Phase 5)

```mermaid
graph LR
    U[Upload JSON/CSV/Text] --> P(Parser)
    P -->|CanonicalExperiment| N(Normalizer)
    N -->|Standardized Fields| V(Validator)
    V -->|ValidationResult| S(Comparison Service)
    
    subgraph Data Access Layer
        S --> R1(ReactionRepository)
        S --> R2(StatisticsRepository)
    end
    
    R1 -.-> C(ComparisonResult)
    R2 -.-> C
    
    C --> F(Formatter / UI rendering)
```

## 4. Planner → Tool → Database Flow

```mermaid
flowchart TD
    Request[User Query] --> Planner{LLM Planner}
    Planner -->|Selects Tool| Schema[backend/planner/schema.py]
    Schema -->|Validates arguments| Tools[backend/tools/]
    
    subgraph Data Access Layer
        Tools --> Repo[backend/database/repositories/]
        Repo -->|Safe Read-Only Query| DB[(DuckDB)]
    end
    
    DB --> Repo
    Repo --> Output[Standardized JSON Return]
```

## 5. Future PostgreSQL Migration Architecture

```mermaid
graph TD
    subgraph API Layer
        Router[FastAPI Routes]
    end
    
    subgraph Service Layer
        Business[Business Logic / Comparison]
        LLM[AI Orchestration]
    end
    
    subgraph Data Access Layer
        Repo[SQLAlchemy Repositories]
    end
    
    subgraph Storage
        PG[(PostgreSQL)]
        S3[(Blob Storage for PDFs)]
    end
    
    Router --> Service
    Service --> Repo
    Repo <--> PG
    Repo <--> S3
```
