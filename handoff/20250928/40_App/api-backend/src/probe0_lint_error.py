# before
def some_function(value):
  return value+1

# after
def some_function(value: int) -> int:
  return value + 1