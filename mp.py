from multiprocessing import Pool
import time
from random import randint
import concurrent.futures

def f(x, y):
    time.sleep(x) 
    return "{0} + {1}".format(x, y)

def cb(stuff):
    print stuff.result()

if __name__ == '__main__':
    with concurrent.futures.ProcessPoolExecutor(max_workers=5) as executor:
        for i in range(10):
            e = executor.submit(f, randint(5,15), randint(16,20))
            e.add_done_callback(cb)
            i += 1
    print "running!"
