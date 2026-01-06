# Python 3.7
import sys

def main(filename: str) -> None:
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()

        # Fix common PEP8 issues
        fixed_lines = []
        for line in lines:
            line = line.rstrip()  # remove trailing whitespace
            if not line.endswith(':'):  # ensure two blank lines before function definition
                line = '\n\n' + line
            fixed_lines.append(line)

        with open(filename, 'w') as file:
            file.write('\n'.join(fixed_lines))

        print(f'Successfully fixed linting issues in {filename}')

    except FileNotFoundError:
        print(f'Error: {filename} not found')
        sys.exit(1)

    except PermissionError:
        print(f'Error: Permission denied to read/write {filename}')
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python fix_lint.py <filename>')
        sys.exit(1)

    main(sys.argv[1])