#!/bin/bash
# One-time setup script to download the local embedding model

echo "Downloading all-MiniLM-L6-v2 embedding model..."
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
echo "Download complete! Model is cached locally."
