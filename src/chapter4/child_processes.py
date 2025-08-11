"""Forking child processes in Python"""

import os
from multiprocessing import Process


def run_child() -> None:
    """Running some logic inside child process"""
    print("Child: I am the child process")
    print(f"Child: My PID is {os.getpid()}")
    print(f"Child: My parent PID is {os.getppid()}")


def start_parent(num_children: int):
    print("Parent: I am the parent process")
    print(f"Parent: My PID is {os.getpid()}")
    # spawning/forking new processes
    for i in range(num_children):
        print(f"Starting child process {i}")
        Process(target=run_child).start()


if __name__ == "__main__":
    num_children = 3
    start_parent(num_children)
