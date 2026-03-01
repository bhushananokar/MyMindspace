"""
Model storage and caching for Component 3
This directory contains downloaded ML models (spaCy, sentence-transformers)
"""

# Model download helpers
MODEL_URLS = {
    'spacy_lg': 'https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.7.1/en_core_web_lg-3.7.1-py3-none-any.whl',
    'mpnet': 'sentence-transformers/all-mpnet-base-v2',
    'minilm': 'sentence-transformers/all-MiniLM-L6-v2'
}

def download_required_models():
    """Download all required models if not present"""
    print("Model downloads handled by respective libraries (spaCy, sentence-transformers)")
    print("Run: python -m spacy download en_core_web_lg")

__all__ = ['MODEL_URLS', 'download_required_models']