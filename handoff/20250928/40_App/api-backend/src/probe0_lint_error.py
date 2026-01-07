# Original code with lint error (unused import, missing whitespace around operators, etc.)
import os, sys

def add(a,b):
    return a+b

# Fixed code
def add(a: int, b: int) -> int:
    return a + b