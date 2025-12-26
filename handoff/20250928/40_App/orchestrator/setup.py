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
        "supabase==2.11.0",  # Synced with requirements.txt (was 2.6.0)
        "openai>=1.55.0,<3.0.0",  # httpx 0.28+ compatibility
        "google-genai==1.52.0",  # Added to match requirements.txt
        "requests==2.32.5",
        "sentry-sdk==2.48.0",
        "redis>=5.2.0,<6.0.0",  # Synced with requirements.txt
        "rq==1.16.2",  # Synced with requirements.txt
        "python-dotenv==1.2.1",
        # Explicit pins for deterministic builds (Issue: Render dependency conflict)
        "httpx>=0.28.1,<0.29",
        "websockets>=13.0.0,<15.1.0",
    ],
    python_requires=">=3.11",
    author="Morning AI",
    description="Morning AI orchestrator for agent workflows",
)
