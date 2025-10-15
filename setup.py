"""
Setup configuration for Agent Monitor
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agent-monitor",
    version="0.1.0",
    author="Cognio AI Lab",
    author_email="dev@cogniolab.com",
    description="Open-source observability and monitoring platform for AI agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cogniolab/agent-monitor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "openai": ["openai>=1.0.0"],
        "anthropic": ["anthropic>=0.18.0"],
        "langchain": ["langchain>=0.1.0"],
        "dashboard": [
            "flask>=3.0.0",
            "flask-cors>=4.0.0",
        ],
        "exporters": [
            "prometheus-client>=0.19.0",
            "opentelemetry-api>=1.20.0",
            "opentelemetry-sdk>=1.20.0",
        ],
        "postgres": [
            "psycopg2-binary>=2.9.0",
            "sqlalchemy>=2.0.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "ruff>=0.1.0",
        ],
        "all": [
            "openai>=1.0.0",
            "anthropic>=0.18.0",
            "langchain>=0.1.0",
            "flask>=3.0.0",
            "flask-cors>=4.0.0",
            "prometheus-client>=0.19.0",
            "opentelemetry-api>=1.20.0",
            "opentelemetry-sdk>=1.20.0",
            "psycopg2-binary>=2.9.0",
            "sqlalchemy>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "agent-monitor=agent_monitor.cli:main",
        ],
    },
    keywords="ai agents monitoring observability llm openai claude langchain tracing metrics cost-tracking",
    project_urls={
        "Bug Reports": "https://github.com/cogniolab/agent-monitor/issues",
        "Source": "https://github.com/cogniolab/agent-monitor",
        "Documentation": "https://github.com/cogniolab/agent-monitor#readme",
    },
)
