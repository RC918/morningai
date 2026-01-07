import os
import subprocess

# Define the path to the file
file_path = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"

try:
    # Stage the file for commit
    subprocess.check_call(["git", "add", file_path])
except subprocess.CalledProcessError as e:
    print(f"An error occurred while staging the file: {e}")

try:
    # Commit the changes
    subprocess.check_call(["git", "commit", "-m", "fix: lint error in probe0_lint_error.py"])
except subprocess.CalledProcessError as e:
    print(f"An error occurred while committing the changes: {e}")

try:
    # Push the changes
    subprocess.check_call(["git", "push", "origin", "HEAD"])
except subprocess.CalledProcessError as e:
    print(f"An error occurred while pushing the changes: {e}")