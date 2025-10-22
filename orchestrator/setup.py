from setuptools import setup, find_packages

setup(
    name="orchestrator",
    version="1.0.0",
    description="MorningAI Orchestrator - Unified Task Orchestration System",
    author="MorningAI Team",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.12",
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "redis>=5.0.0",
        "pydantic>=2.4.0",
        "PyJWT>=2.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "httpx>=0.25.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "orchestrator=orchestrator.api.main:main",
        ],
    },
)
