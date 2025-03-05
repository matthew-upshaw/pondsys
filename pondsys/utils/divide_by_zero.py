def divide_by_zero(a, b):
    """
    Returns x/y if y is not zero, otherwise returns inf.

    Parameters
    ----------
    a : int or float
        The numerator.
    b : int or float
        The denominator.
    """
    try:
        return a / b
    except ZeroDivisionError:
        return float('inf')