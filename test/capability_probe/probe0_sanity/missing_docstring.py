def add_docstring(file_path: str, docstring: str) -> None:
    """
    Add a docstring to the given python file.

    :param file_path: str: The path to the python file.
    :param docstring: str: The docstring to add.
    :return: None
    """
    try:
        with open(file_path, 'r') as file:
            content = file.read()
    except FileNotFoundError:
        print(f"No such file or directory: '{file_path}'")
        return

    updated_content = f"\"\"\"{docstring}\"\"\"\n\n{content}"

    try:
        with open(file_path, 'w') as file:
            file.write(updated_content)
    except Exception as e:
        print(f"Error occurred while writing to file: {e}")


# Adding a docstring to the python file
add_docstring('test/capability_probe/probe0_sanity/missing_docstring.py', 'This is a sample docstring.')