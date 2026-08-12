# Hybrid PageIndex RAG

A document intelligence and Retrieval-Augmented Generation (RAG) system that processes PDF documents, builds a hierarchical page-based index, and uses the indexed structure to retrieve relevant information for question answering.

The project combines PageIndex-style hierarchical document indexing with a RAG pipeline and supports local LLM inference through Ollama and Qwen.

## Overview

Traditional RAG systems usually split documents into chunks and retrieve them based mainly on semantic similarity.

This project takes a different approach by first understanding the structure of a document and creating a hierarchical index based on sections, subsections, and their physical page locations.

The indexed document can then be used to retrieve relevant sections before generating an answer.

### Current Pipeline

PDF
↓
PDF Parsing
↓
Document Structure / PageIndex
↓
Hierarchical Index
↓
Relevant Section Retrieval
↓
LLM
↓
Answer / Structured Output

## Key Features

- PDF document processing
- Hierarchical document indexing
- Page-level section tracking
- Structured document representation
- Retrieval of relevant document sections
- RAG-based question answering
- Local LLM inference using Ollama
- Qwen model integration
- FastAPI backend
- Streamlit-based interface
- Modular document processing pipeline

## Technology Stack

- **Python**
- **FastAPI**
- **Streamlit**
- **Ollama**
- **Qwen**
- **PageIndex**
- **PDFium / PDF parsing**
- **Retrieval-Augmented Generation (RAG)**

## Project Architecture

```text
hybrid-pageindex-rag/
│
├── app/
│   ├── api/
│   │   └── routes.py
│   ├── config/
│   │   └── settings.py
│   ├── indexer/
│   │   └── page_index.py
│   ├── llm/
│   │   └── gemini_client.py
│   ├── models/
│   │   └── page.py
│   ├── okf/
│   │   └── okf_generator.py
│   ├── parser/
│   │   └── pdf_parser.py
│   ├── retriever/
│   │   └── hybrid_retriever.py
│   └── utils/
│       └── helpers.py
│
├── data/
│   ├── okf/
│   ├── pageindex/
│   └── uploads/
│
├── docs/
│   └── architecture.md
│
├── frontend/
│   └── app.py
│
├── tests/
│
├── main.py
├── requirements.txt
└── README.md
