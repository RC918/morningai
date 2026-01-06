# Before
def greet(name):
    return 'Hello, ' + name

# After (fixing missing whitespace around operator)
def greet(name: str) -> str:
    return 'Hello, ' + name