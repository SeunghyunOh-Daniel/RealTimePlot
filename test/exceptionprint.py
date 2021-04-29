import sys, os, traceback
import time
try:
    raise NotImplementedError("No error")

except Exception as e:
    tic = time.perf_counter()

    exc_type, exc_obj, exc_tb = sys.exc_info()
    tb = traceback.extract_tb(exc_tb)[-1]
    for index, value in enumerate(tb):
        print(index, value)
    print(f"{exc_type}:{tb[0]}:line {tb[1]}")

    print(f"process time: {time.perf_counter() - tic}")


def debug():
    import sys, traceback
    exc_type, exc_obj, exc_tb = sys.exc_info()
    tb = traceback.extract_tb(exc_tb)[-1]
    print(f"{exc_type}:{tb[0]}:line {tb[1]}")