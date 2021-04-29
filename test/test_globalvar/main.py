import queue, threading

import get
import put

shared_data = queue.Queue()

thread_put = threading.Thread(target=put.put_queue, args=(shared_data,), daemon=True)
thread_get = threading.Thread(target=get.get_queue, args=(shared_data,), daemon=True)

thread_get.start()
thread_put.start()

thread_put.join()
thread_get.join()
