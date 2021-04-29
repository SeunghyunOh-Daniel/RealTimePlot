import queue


def get_queue(shared_data):
    x = shared_data
    while True:
        if x.qsize() > 0:
            try:
                print(f"get data {x.get_nowait()}")
            except queue.Empty:
                print("No data")
        else:
            print("No data")
        import time
        time.sleep(0.1)
