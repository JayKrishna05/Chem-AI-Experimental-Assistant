# AI Chemistry Engine

This repository contains the AI Chemistry Engine platform, consisting of a FastAPI backend and a Next.js frontend.

## How to Run the Application

To run the full application locally, you will need to start both the backend server and the frontend development server in separate terminal windows.

### 1. Start the Backend (FastAPI)

Open a terminal in the root directory of the project (`AI chemistry engine V1`) and run the following command to start the FastAPI server with hot-reloading:

```bash
uvicorn backend.api.main:app --reload
```
*(Note: Ensure you have activated your Python virtual environment if you are using one, and that all dependencies from `requirements.txt` are installed.)*

The backend API will be available at: http://localhost:8000

### 2. Start the Frontend (Next.js)

Open a **second** terminal window, navigate to the `frontend` directory, and start the development server:

```bash
cd frontend
npm install   # Only needed the first time to install dependencies
npm run dev
```

The frontend UI will be available at: http://localhost:3000

---

## Architecture Overview

- **Backend (`/backend`)**: A robust Python/FastAPI backend utilizing DuckDB for rapid analytical chemistry queries and LLM coordination (the Planner/Formatter architecture).
- **Frontend (`/frontend`)**: A React/Next.js application providing the conversational UI and dashboard components.
- **Documentation**: 
  - Consult `PROJECT_STATE.md` and `PROJECT_STRUCTURE.md` for current project context.
  - Review the `adr/` directory for detailed Architecture Decision Records.
