# Assuming the lint error was an unused variable

# Before
def example():
    unused_var = 5
    print("Hello, World!")

# After
def example():
    print("Hello, World!")