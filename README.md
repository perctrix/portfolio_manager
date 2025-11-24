# Portfolio Manager

A lightweight, privacy-focused portfolio management tool.

## Architecture

- **Backend**: Python (FastAPI)
- **Frontend**: Next.js (React)
- **Storage**: Local CSV/JSON files (no database required)

## Setup

### Backend

1. Navigate to `backend/`
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the server:
   ```bash
   uvicorn main:app --reload
   ```
   API will be available at `http://localhost:8000`.

### Frontend

1. Navigate to `frontend/`
2. Install dependencies (if not already done):
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   App will be available at `http://localhost:3000`.

## Data

All data is stored in the `data/` directory in the project root.
