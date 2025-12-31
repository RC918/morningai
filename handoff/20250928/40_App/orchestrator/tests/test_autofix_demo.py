"""Test file to demonstrate GeneralCoder/SimpleCoder auto-fix behavior.

This file intentionally contains lint errors to trigger the auto-fix flow.
DO NOT manually fix these errors - let GeneralCoder/SimpleCoder handle them.

Test PR for Issue #3360 investigation.
"""
import os
import sys
import json


def calculate_sum(a,b,c):
    """Calculate sum of three numbers.
    
    Missing spaces after commas in function signature (E231).
    """
    result=a+b+c
    return result


def format_message(name,age):
    """Format a greeting message.
    
    Missing spaces after commas (E231).
    Missing spaces around operator (E225).
    """
    message="Hello, "+name+"! You are "+str(age)+" years old."
    return message


class DataProcessor:
    """Simple data processor class."""
    
    def __init__(self,data):
        """Initialize with data.
        
        Missing space after comma (E231).
        """
        self.data=data
    
    def process(self):
        """Process the data."""
        if self.data==None:
            return []
        return [x*2 for x in self.data]


if __name__ == "__main__":
    # Test the functions
    result = calculate_sum(1,2,3)
    print(f"Sum: {result}")
    
    msg = format_message("Test",25)
    print(msg)
    
    processor = DataProcessor([1,2,3])
    print(processor.process())
