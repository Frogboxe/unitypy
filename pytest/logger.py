
import sys
import threading
from datetime import datetime

now = lambda: str(datetime.now()).replace("-", "").replace(":", "").replace(" ", "").replace(".", "")[2:-7:]
md = lambda: f"[{str(datetime.now())[14:19:]}]"
none = lambda: ""

class _Logger:
    def __init__(self, target: str=None, tsf: lambda: 0=none, flushingInterval: int=1, fileMode: str="a",
                 lock: threading.Lock=None, **kwargs):
        self.flushingInterval, self.flushingCounter = flushingInterval, 0
        self.kwargs = kwargs
        if hasattr(tsf, "__call__"):
            self.tsf = tsf
        else:
            raise Exception(f"Given timestamp method {tsf} is not callable!")
        if lock is None:
            self.lock = threading.Lock()
        elif type(lock) is threading.Lock:
            self.lock = lock
        else:
            raise Exception(f"Lock given {lock} is not a valid lock!")
        if target is None:
            self.target = sys.stdout
        elif type(target) is str:
            self.target = open(target, fileMode)
        else:
            raise Exception(f"Target {target} is not valid!")

    def __call__(self, *args, **kwargs):
        kwargs |= self.kwargs
        with self.lock:
            print(self.tsf(), *args, file=self.target, **kwargs)
        self.flushingCounter += 1
        if (self.flushingCounter % self.flushingInterval) == 0:
            self.flush()
            
    def write(self, text: str):
        with self.lock:
            self.target.write(text)

    def flush(self):
        with self.lock:
            self.target.flush()

class Logger:
    def __init__(self, targets: tuple[str]=(None,), tsf: lambda: 0=none, flushingInterval: int=1,
                 fileMode: str="a", **kwargs):
        loggers = []
        for target in targets:
            loggers.append(_Logger(target, tsf, flushingInterval, fileMode, **kwargs))
        self.loggers = loggers

    def __iter__(self) -> list[_Logger]:
        yield from self.loggers

    def __call__(self, *args, **kwargs):
        for logger in self.loggers:
            logger(*args, **kwargs)

    def write(self, text: str):
        for logger in self.loggers:
            logger.write(text)

    def flush(self):
        for logger in self.loggers:
            logger.flush()

    def __del__(self):
        for logger in self.loggers:
            try:
                logger.flush()
            except ValueError:
                pass

def get_logger(route: str) -> Logger:
    "gets a simple logger that prints to stdout and the given route"
    return Logger((route, None), md)

def get_mass_Logger(route: str, flushTimer: int=32) -> Logger:
    "gets a logger with a gap between flushes for performance"
    return Logger((route, None), md, flushingInterval=flushTimer)

def main():
    test = Logger((None, "hello.txt"), md, flushingInterval=32)
    for i in range(1000):
        test(i)


if __name__ == "__main__":
    main()





