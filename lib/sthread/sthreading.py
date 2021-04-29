import threading
import inspect
import ctypes


def _async_raise(tid, exctype):
    if tid is None:
        return None
    """raises the exception, performs cleanup if needed"""
    if not inspect.isclass(exctype):
        raise TypeError("Only types can be raised (not instances)")
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
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
        Override this method to return actual frame at current time.
        """
        if self.target is None:
            pass
        else:
            self.target(*self.args)

        return

    def _get_my_tid(self):
        """determines this (self's) thread id"""
        if not self.is_alive():
            # raise threading.ThreadError("the thread is not active")
            return None
        # do we have it cached?
        if hasattr(self, "_thread_id"):
            return self._thread_id

        # no, look for it in the _active dict
        for tid, tobj in threading._active.items():
            if tobj is self:
                self._thread_id = tid
                return tid

        raise AssertionError("could not determine the thread's id")

    def raise_exc(self, exctype):
        """raises the given exception type in the context of this thread"""
        _async_raise(self._get_my_tid(), exctype)

    def terminate(self):
        """raises SystemExit in the context of the given thread, which should
        cause the thread to exit silently (unless caught)"""
        self.raise_exc(SystemExit)
