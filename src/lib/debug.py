"""
Print Error location, contexts
"""


def print_debug():
    import sys, traceback
    exc_type, exc_obj, exc_tb = sys.exc_info()
    tb = traceback.extract_tb(exc_tb)[-1]
    print(f"{exc_type}:{tb[0]}:line {tb[1]}")
