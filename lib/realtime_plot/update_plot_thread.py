import threading
import time
from sthread import sthreading


class UpdatePlotThread(sthreading.sThread):
    def __init__(self, var, operation_mode, interval, queue, plot_queue):
        super().__init__(name="UpdatePlotThread")

        self.queue = queue
        self.plot_queue = plot_queue

        self.var = var
        self.operation_mode = operation_mode
        self.interval = interval

    # start in Thread class
    def run(self):
        while self._flag:
            time.sleep(self.interval)
            if self.plot_queue.qsize() <= 0:
                self.queue.put((0,), "No Data")
                pass
            else:
                frame = self.plot_queue.get_nowait()
                self.queue.put(frame, "Data")
        else:
            print("No Run")
            args = (None, "Stop")
            self.queue.put(args)
