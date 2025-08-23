from collections import deque
import typing as T

Coroutine = T.Generator[None, None, int]


class EventLoop:
    def __init__(self) -> None:
        self.tasks: T.Deque[Coroutine] = deque()

    def add_coroutine(self, task: Coroutine) -> None:
        self.tasks.append(task)

    def run_coroutine(self, task: Coroutine) -> None:
        try:
            task.send(None)
            self.add_coroutine(task)
        except StopIteration:
            print("Task completed")

    def run_forever(self) -> None:
        while self.tasks:
            print("Event loop cycle.")
            self.run_coroutine(self.tasks.popleft())


def fibonacci(n: int) -> Coroutine:
    a, b = 0, 1
    for i in range(n):
        a, b = b, a + b
        print(f"Fibonacci {i}: {a}")
        yield
    return a


if __name__ == "__main__":
    event_loop = EventLoop()
    event_loop.add_coroutine(fibonacci(5))
    event_loop.run_forever()
