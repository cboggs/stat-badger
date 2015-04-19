from multiprocessing import Pool
import time
from random import randint

def f((x, y)):
    time.sleep(x) 
    print "{0} + {1}".format(x, y)

if __name__ == '__main__':
    i = 0
    pool = Pool(processes=3)              # start 4 worker processes
#    pool.map(f, ((randint(1,10), randint(15,20)) for i in range(10)))
    tasks = [((randint(1,30), randint(15,20))) for i in range(20)]
#    print tasks
    pool.map(f, ((randint(1,30), randint(15,20)) for i in range(20)))
