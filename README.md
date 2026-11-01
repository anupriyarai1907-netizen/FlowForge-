# FlowForge – AI-Powered Data Flow Diagram Generator

FlowForge is an AI-powered application designed to generate Data Flow Diagrams (DFDs) from source code and database files using code analysis, Retrieval-Augmented Generation (RAG), and Large Language Models (LLMs).

## Project Overview

The system analyzes source code, extracts meaningful information, retrieves relevant context, and generates structured Data Flow Diagrams with visual representations.

## Key Features

- Source code analysis and parsing
- Code chunking and semantic embeddings
- Vector storage using ChromaDB
- Retrieval-Augmented Generation (RAG)
- Gemini API integration for AI-assisted DFD generation
- DFD structure validation
- Graph-based diagram visualization
- React-based frontend
- Flask-based backend
- Multi-language source code support (under development)

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React.js, Vite |
| Backend | Python, Flask |
| AI Integration | Gemini API |
| Embeddings | Sentence Transformers |
| Vector Database | ChromaDB |
| Visualization | Graphviz |
| Database Parsing | SQLGlot |

## System Architecture

```text
Source Code / SQL Files
          |
          v
   Code Analysis
          |
          v
    Code Chunking
          |
          v
     Embeddings
          |
          v
   ChromaDB Vector Store
          |
          v
    Context Retrieval
          |
          v
      Gemini LLM
          |
          v
   Structured DFD Output
          |
          v
   Validation & Visualization
          |
          v
     Generated DFD
```

## Project Structure

```text
FlowForge/
├── backend/
│   ├── app.py
│   ├── analyzer.py
│   ├── chunking.py
│   ├── embeddings.py
│   ├── retrieval.py
│   ├── vector_store.py
│   ├── llm_generator.py
│   ├── validator.py
│   └── visualizer.py
│
├── frontend/
│   └── React application files
│
├── .gitignore
└── README.md
```

## Current Development Status

FlowForge is currently under active development.

Implemented:
- Flask backend setup
- React frontend setup
- Backend and frontend integration
- Code chunking and embedding pipeline
- ChromaDB vector storage
- RAG-based context retrieval
- AI-assisted DFD generation
- Initial DFD validation and visualization

In Progress:
- Improving function and class-level analysis
- Improving control-flow representation
- Improving relationships and labeled data flows
- Expanding multi-language and SQL analysis

## Getting Started

### Backend Setup

```bash
cd backend
python -m venv venv
```

Activate the virtual environment on Windows:

```powershell
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the backend:

```bash
python app.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

Create a `.env` file inside the backend directory and configure your Gemini API key:

```env
GEMINI_API_KEY=your_api_key_here
```

Never commit API keys or other sensitive credentials.

## Project Status

Work in Progress

This project is being developed as an academic minor project with a focus on AI-assisted software analysis and automated DFD generation.
