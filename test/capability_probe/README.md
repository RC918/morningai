import os

def check_readme(file_path: str) -> None:
    if os.path.exists(file_path):
        if os.access(file_path, os.R_OK):
            print(f"The file '{file_path}' is accessible. Please review it for outdated information or inconsistencies.")
        else:
            print(f"The file '{file_path}' exists but is not readable. Please check the file permissions.")
    else:
        print(f"The file '{file_path}' does not exist. Please check the file path.")

if __name__ == "__main__":
    check_readme("test/capability_probe/README.md")