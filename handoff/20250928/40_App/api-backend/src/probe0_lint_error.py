# Before linting

import math, os # multiple imports on one line
from utils import * # wildcard import

def Calc(d): # function name is not snake_case
  return math.sqrt(d) # no docstring, missing whitespace around operator

# After linting

import math
import os
from utils import specific_function  # import only necessary functions

def calculate_square_root(distance: float) -> float:
  """Calculate the square root of a number.

  Args:
    distance: The number to find the square root of.

  Returns:
    The square root of the number.
  """
  return math.sqrt(distance)