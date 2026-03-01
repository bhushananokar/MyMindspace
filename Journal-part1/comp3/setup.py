from setuptools import setup, find_packages

setup(
    name="component3-ner-temporal",
    version="1.0.0",
    description="Component 3: NER, Temporal Analysis & Event Extraction with Component 8 Integration",
    author="AI Journal Platform Team",
    packages=find_packages(),
    install_requires=[
        "spacy>=3.7.0",
        "sentence-transformers>=2.2.0", 
        "scikit-learn>=1.3.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "python-dateutil>=2.8.0",
        "pyyaml>=6.0",
        "typing-extensions>=4.5.0"
    ],
    extras_require={
        "gpu": [
            "torch>=2.0.0",
            "transformers>=4.30.0"
        ]
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)