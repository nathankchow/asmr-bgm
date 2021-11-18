'''
store operations requested by user, and dequeue them using threading 
'''

import threading 
import queue
import os 

class RequestQueue(queue.Queue):
    def init(self):
        super().__init__()

class ConsumerThread(threading.Thread):
    def init(self):
        super().__init__()


if __name__ == '__main__':
    rq = RequestQueue()
    print(rq.empty())
    