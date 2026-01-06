# Before fix
def calculateInterest(P, r, n, t):
    A = P * (1 + r/n) ** (n*t)
    return A

# After fix
def calculate_interest(principal: float, rate: float, num_times_compounded: int, time: float) -> float:
    amount = principal * (1 + rate / num_times_compounded) ** (num_times_compounded * time)
    return amount