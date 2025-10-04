from setuptools import setup, find_packages

setup(
    name="morningai-orchestrator",
    version="0.1.0",
    packages=find_packages(),
    py_modules=['graph'],
    install_requires=[
        "langchain-community>=0.2.16",
        "langchain-openai>=0.1.23",
        "langgraph>=0.2.4",
        "supabase==2.6.0",
        "openai==1.52.2",
        "requests==2.32.3",
        "sentry-sdk==2.19.2",
        "redis",
        "rq",
        "python-dotenv==1.0.1"
    ],
    python_requires=">=3.12",
    author="Morning AI",
    description="Morning AI orchestrator for agent workflows",
)
