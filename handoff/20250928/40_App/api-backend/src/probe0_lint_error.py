import pylint.lint

def lint_file(file_path: str) -> None:
    """
    Run the pylint linter on the specified python file.
    
    Args:
        file_path (str): Python file path.
    """
    pylint_opts = [file_path]
    linter = pylint.lint.Run(pylint_opts)