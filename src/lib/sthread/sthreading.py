"""

Thread to get Property
1. To Terminate
2. To Stop
3. To Get Priority

"""

# --------------------------------------------------------------------------------------------------------------------------------------

# Library
import threading
import inspect
import ctypes


# --------------------------------------------------------------------------------------------------------------------------------------

def _async_raise(tid, exctype):
    if tid is None:
        # Thread is not alive, Pass
        return None

    """raises the exception, performs cleanup if needed"""
    if not inspect.isclass(exctype):
        raise TypeError("Only types can be raised (not instances)")

    # Terminate the Thread
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))

    # Exceptional Case
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
        raise SystemError("PyThreadState_SetAsyncExc failed")


class sThread(threading.Thread):
    def __init__(self, name=None, target=None, args=None):
        threading.Thread.__init__(self, name=name, daemon=True)
        self._flag = True

        self.target = target
        self.args = args
        self.priority = 0

    def stop(self):
        self._flag = False
        print("STOP")

    def run(self):
        """
        Override this method to run the thread
        """
        if self.target is None:
            pass
        else:
            self.target(*self.args)

        return

    def _get_my_tid(self):
        """determines this (self's) thread id"""
        if not self.is_alive():
            # Thread is not alive, Pass
            return None
            # raise threading.ThreadError("the thread is not active")

        # If it has cached,
        if hasattr(self, "_thread_id"):
            return self._thread_id

        # If not, looking for it in the _active dict
        for tid, tobj in threading._active.items():
            if tobj is self:
                self._thread_id = tid
                return tid

        # If there is no thread id i need to find,
        raise AssertionError("could not determine the thread's id")

    def raise_exc(self, exctype):
        """raises the given exception type in the context of this thread"""
        _async_raise(self._get_my_tid(), exctype)

    def terminate(self):
        """raises SystemExit in the context of the given thread, which should
        cause the thread to exit silently (unless caught)"""
        self.raise_exc(SystemExit)
