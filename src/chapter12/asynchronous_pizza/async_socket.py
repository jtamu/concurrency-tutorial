"""Asynchronous socket implementation - same functionality but with asynchronous flavour!"""

# Allow forward references in type hints (Python 3.7+)
from __future__ import annotations

import select
import typing as T
import socket

from future import Future
from event_loop import EventLoop, Coroutine

Data = bytes


class AsyncSocket:
    def __init__(self, sock: socket.socket) -> None:
        self._sock = sock
        self._sock.setblocking(False)

    def recv(self, bufsize: int) -> Future:
        future = Future()

        def handle_yield(loop: EventLoop, task: Coroutine) -> None:
            try:
                data = self._sock.recv(bufsize)
                loop.add_ready(task, data)
            except BlockingIOError:
                loop.register_event(self._sock, select.POLLIN, future, task)

        future.set_coroutine(handle_yield)
        return future

    def send(self, data: Data) -> Future:
        future = Future()

        def handle_yield(loop: EventLoop, task: Coroutine) -> None:
            try:
                nsent = self._sock.send(data)
                loop.add_ready(task, nsent)
            except BlockingIOError:
                loop.register_event(self._sock, select.POLLOUT, future, task)

        future.set_coroutine(handle_yield)
        return future

    def accept(self) -> Future:
        future = Future()

        def handle_yield(loop: EventLoop, task: Coroutine) -> None:
            try:
                r = self._sock.accept()
                loop.add_ready(task, r)
            except BlockingIOError:
                loop.register_event(self._sock, select.POLLIN, future, task)

        future.set_coroutine(handle_yield)
        return future

    def close(self) -> Future:
        future = Future()

        def handle_yield(*args) -> None:
            self._sock.close()

        future.set_coroutine(handle_yield)
        return future

    def __getattr__(self, name: str) -> T.Any:
        return getattr(self._sock, name)
