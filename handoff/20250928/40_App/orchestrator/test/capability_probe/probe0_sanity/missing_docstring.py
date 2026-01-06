def add_docstring(filename: str, docstring: str) -> None:
    """Add a docstring to the given file.

    Args:
        filename (str): The path to the file.
        docstring (str): The docstring to be added.
    """
    try:
        with open(filename, 'r+') as file:
            content = file.read()
            file.seek(0, 0)
            file.write(f'"""{docstring}"""\n' + content)
    except FileNotFoundError:
        print(f"{filename} not found.")
    except IOError:
        print("An error occurred trying to read the file.")
    except:
        print("An unexpected error occurred.")

def main():
    filename = "test/capability_probe/probe0_sanity/missing_docstring.py"
    docstring = "This is a test file for capability probe. This file is used for testing the sanity of the system."
    add_docstring(filename, docstring)

if __name__ == "__main__":
    main()