"""

To Update the plot Windows

"""

# --------------------------------------------------------------------------------------------------------------------------------------

# Library
import time
from sthread import sthreading


# --------------------------------------------------------------------------------------------------------------------------------------

class UpdatePlotThread(sthreading.sThread):
    def __init__(self, var, operation_mode, interval, queue_plot, queue_shared):
        super().__init__(name="UpdatePlotThread")

        self.queue_plot = queue_plot
        self.queue_shared = queue_shared

        self.var = var
        self.operation_mode = operation_mode
        self.interval = interval

    # start in Thread class
    def run(self):
        while self._flag:
            time.sleep(self.interval)
            if self.queue_shared.qsize() <= 0:
                self.queue_plot.put((0,), "No Data")
                pass
            else:
                frame = self.queue_shared.get_nowait()
                self.queue_plot.put(frame, "Data")
        else:
            print("No Run")
            args = (None, "Stop")
            self.queue_plot.put(args)
