import queue


def put_queue(shared_data):
    count = 0
    while count < 100000000:
        shared_data.put(count)
        count += 1
        import time
        time.sleep(0.2)
