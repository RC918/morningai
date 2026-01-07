# Before fixing lint
def myfunc(n):
    if(n>0):
     return n*2
    else:
     return None

# After fixing lint
def myfunc(n: int) -> Union[int, None]:
    if n > 0:
        return n * 2
    else:
        return None