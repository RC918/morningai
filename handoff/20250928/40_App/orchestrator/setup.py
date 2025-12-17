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
        "PyGithub==2.4.0",
        "supabase==2.6.0",
        "openai>=1.55.0,<2.0.0",  # httpx 0.28+ compatibility
        "requests==2.32.5",
        "sentry-sdk==2.48.0",
        "redis",
        "rq",
        "python-dotenv==1.2.1"
    ],
    python_requires=">=3.11",
    author="Morning AI",
    description="Morning AI orchestrator for agent workflows",
)
