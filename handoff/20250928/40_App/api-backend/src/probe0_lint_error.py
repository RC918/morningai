# Before
def foo():
  print(bar)

# After
def foo():
  bar = 'Hello, World!'
  print(bar)