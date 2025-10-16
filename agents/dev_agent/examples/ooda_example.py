#!/usr/bin/env python3
"""
Example usage of Dev_Agent OODA Loop
"""
import asyncio
import os
from agents.dev_agent.dev_agent_ooda import create_dev_agent_ooda


async def main():
    """Run example OODA tasks"""

    sandbox_endpoint = os.getenv('DEV_AGENT_ENDPOINT', 'http://localhost:8080')
    github_token = os.getenv('GITHUB_TOKEN')

    ooda = create_dev_agent_ooda(sandbox_endpoint, github_token)

    print("\n=== Example 1: Code Exploration ===")
    result1 = await ooda.execute_task(
        "Explore the agents/dev_agent directory and identify key components",
        priority="medium",
        max_iterations=1
    )
    print(f"Result: {result1.get('result', {})}")

    print("\n=== Example 2: File Operations ===")
    result2 = await ooda.execute_task(
        "Create a test file and check if it exists",
        priority="low",
        max_iterations=2
    )
    print(f"Result: {result2.get('result', {})}")

    print("\n=== OODA Examples Completed ===")


if __name__ == '__main__':
    asyncio.run(main())
