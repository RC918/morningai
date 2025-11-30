from setuptools import setup, find_packages

# Find all packages and prefix them with 'orchestrator'
# This ensures imports like 'from orchestrator.persistence import ...' work correctly
packages = find_packages(exclude=['tests', 'tests.*'])
orchestrator_packages = ['orchestrator'] + [f'orchestrator.{pkg}' for pkg in packages if pkg != 'orchestrator']

setup(
    name="morningai-orchestrator",
    version="0.1.0",
    packages=orchestrator_packages,
    package_dir={
        'orchestrator': '.',
    },
    py_modules=['orchestrator.graph'],
    install_requires=[
        "langchain-community>=0.2.16",
        "langchain-openai>=0.1.23",
        "langgraph>=0.2.4",
        "PyGithub==2.4.0",
        "supabase==2.6.0",
        "openai==1.52.2",
        "requests==2.32.3",
        "sentry-sdk==2.19.2",
        "redis",
        "rq",
        "python-dotenv==1.0.1"
    ],
    python_requires=">=3.11",
    author="Morning AI",
    description="Morning AI orchestrator for agent workflows",
)
