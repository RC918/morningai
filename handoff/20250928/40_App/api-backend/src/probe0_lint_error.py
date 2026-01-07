# probe0_lint_error.py
def problematic_func(x, y):
  z = x+y # might cause a lint error because of no spaces around operator
  if z>10: # might cause a lint error because of no spaces around operator
    print('z is greater than 10')
  return z