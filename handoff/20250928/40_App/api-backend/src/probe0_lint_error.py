# Before: This code will raise a linting error because it doesn't follow PEP 8 naming conventions
def myFunction():
    myVariable = "Hello, World!"
    print(myVariable)

# After: This code follows PEP 8 naming conventions
def my_function():
    my_variable = "Hello, World!"
    print(my_variable)