from setuptools import setup, find_packages

setup(
    name="morningai-orchestrator",
    version="0.1.0",
    packages=find_packages(),
    py_modules=['graph'],
    install_requires=[
        # NOTE: With --no-deps in render.yaml, dependencies are managed by requirements.txt
        # setup.py install_requires is only used for pip check validation
        # Removed langchain-community and langchain-openai (not imported in orchestrator code)
        "langgraph>=0.2.4",
        "langchain-core>=0.3.0",  # Added - actually imported in orchestrator
        "PyGithub==2.4.0",
        "supabase==2.11.0",
        "openai>=1.55.0,<3.0.0",
        "google-genai==1.52.0",
        "requests==2.32.5",
        "sentry-sdk==2.48.0",
        "redis>=5.2.0,<6.0.0",
        "rq==1.16.2",
        "python-dotenv==1.2.1",
        "httpx>=0.28.1,<0.29",
        "websockets>=13.0.0,<15.1.0",
        # Additional deps from requirements.txt for pip check validation
        "pydantic-settings>=2.0.0",
        "tiktoken>=0.5.0",
        "langgraph-checkpoint-redis>=0.2.1",
        "langgraph-checkpoint-postgres>=2.0.0",
        "psycopg[pool]>=3.2.0",
        "aiohttp>=3.12.14",
    ],
    python_requires=">=3.11",
    author="Morning AI",
    description="Morning AI orchestrator for agent workflows",
)
