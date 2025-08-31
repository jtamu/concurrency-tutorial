# 協調型ピザサーバーの動作原理解説

## 概要

この文書では、`cooperative_pizza_server.py`の動作原理について詳しく解説します。このサーバーは、非同期プログラミングの基本概念である**協調的マルチタスキング**を実装したピザ注文サーバーです。

## アーキテクチャ概要

協調型ピザサーバーは以下の4つの主要コンポーネントで構成されています：

1. **EventLoop** - イベントループ（イベント駆動実行エンジン）
2. **AsyncSocket** - 非同期ソケットラッパー
3. **Future** - 非同期操作の状態管理
4. **Server** - ピザサーバーメインロジック

## 各コンポーネントの詳細解説

### 1. EventLoop（イベントループ）

```python
class EventLoop:
    def __init__(self) -> None:
        self._numtasks = 0
        self._ready = deque()
        self._read_waiting = {}
        self._write_waiting = {}
```

EventLoopは協調的マルチタスキングの中核となるコンポーネントです。

#### 主要な役割：
- **タスク管理**: アクティブなコルーチンの数を追跡
- **準備完了キュー**: 実行可能なタスクを`_ready`デクで管理
- **I/O待機管理**: 読み取り/書き込み待機中のソケットを辞書で管理

#### 実行フロー：
1. `run_forever()`でメインループを開始
2. 準備完了キューが空の場合、`select.select()`でI/Oイベントを待機
3. I/Oが利用可能になったタスクを準備完了キューに移動
4. 準備完了キューからタスクを取り出して実行
5. タスクが完了するまで1-4を繰り返す

### 2. Future（非同期操作の状態管理）

```python
class Future:
    def __init__(self) -> None:
        self.coroutine = None

    def set_coroutine(self, coroutine: T.Callable):
        self.coroutine = coroutine
```

Futureは非同期操作の**プレースホルダー**として機能します。

#### 動作原理：
- 非同期操作（ソケットI/O）が開始されると、Futureオブジェクトが作成される
- Futureには、操作完了時に実行すべきコルーチンが関連付けられる
- I/Oが準備完了になると、EventLoopがFutureのコルーチンを呼び出す

### 3. AsyncSocket（非同期ソケットラッパー）

AsyncSocketは標準のsocketオブジェクトを非ブロッキング動作にラップします。

#### 重要な設定：
```python
def __init__(self, sock: socket.socket) -> None:
    self._sock = sock
    self._sock.setblocking(False)  # 非ブロッキングモードに設定
```

#### recv()メソッドの動作：
```python
def recv(self, bufsize: int) -> Future:
    future = Future()

    def handle_yield(loop: EventLoop, task: Coroutine) -> None:
        try:
            data = self._sock.recv(bufsize)
            loop.add_ready(task, data)  # データ取得成功 → 即座に実行キューに追加
        except BlockingIOError:
            loop.register_event(self._sock, select.POLLIN, future, task)  # データ待機中 → I/O待機リストに登録

    future.set_coroutine(handle_yield)
    return future
```

#### 協調動作の仕組み：
1. **即座にデータが利用可能**: `add_ready()`で即座に実行キューに追加
2. **データが未準備**: `register_event()`でI/O待機リストに登録し、制御を他のタスクに譲る

### 4. Server（メインサーバーロジック）

#### 接続受付ループ（start()メソッド）：
```python
def start(self) -> Coroutine:
    try:
        while True:
            conn, address = yield self.server_socket.accept()  # 新しい接続を待機
            print(f"Connected to {address}")
            self.event_loop.add_coroutine(self.serve(AsyncSocket(conn)))  # 新しいタスクを作成
```

#### クライアント処理（serve()メソッド）：
```python
def serve(self, conn: AsyncSocket) -> Coroutine:
    while True:
        data = yield conn.recv(BUFFER_SIZE)  # データ受信を待機
        if not data:
            break

        try:
            order = int(data.decode())
            response = f"Thank you for ordering {order} pizzas!\n"
        except ValueError:
            response = "Wrong number of pizzas, please try again.\n"

        yield conn.send(response.encode())  # レスポンス送信
```

## 協調的マルチタスキングの動作原理

### yieldキーワードの役割

`yield`文は協調的マルチタスキングの**協調ポイント**です：

1. **制御の移譲**: `yield`により現在のタスクが一時停止し、制御がEventLoopに戻る
2. **非ブロッキング操作**: I/O操作が完了していない場合、他のタスクに実行機会を与える
3. **再開ポイント**: I/O操作が完了すると、`yield`の次の行から実行を再開

### 実行フローの例

複数クライアントが同時接続した場合の実行フロー：

```
時刻 T1: クライアントA接続 → serve(A)タスク作成
時刻 T2: serve(A)がrecv()で待機 → yield → EventLoopに制御移譲
時刻 T3: クライアントB接続 → serve(B)タスク作成
時刻 T4: serve(B)がrecv()で待機 → yield → EventLoopに制御移譲
時刻 T5: クライアントAからデータ到着 → serve(A)再開
時刻 T6: serve(A)がsend()で待機 → yield → EventLoopに制御移譲
時刻 T7: クライアントBからデータ到着 → serve(B)再開
...
```

## 利点と特徴

### 利点：
1. **軽量**: スレッドに比べてメモリ使用量が少ない
2. **デッドロック耐性**: 協調的スケジューリングによりデッドロックが発生しにくい
3. **制御可能**: タスクの実行タイミングを明示的に制御可能

### 特徴：
1. **単一スレッド**: すべての操作が単一スレッドで実行される
2. **イベント駆動**: I/Oイベントに基づいてタスクをスケジューリング
3. **協調的**: タスクが自発的に制御を譲渡する

## まとめ

協調型ピザサーバーは、Python の generator を使用して協調的マルチタスキングを実装した例です。EventLoop、Future、AsyncSocket が連携することで、複数のクライアントを効率的に処理しながらも、複雑なスレッド管理を避けることができます。

この実装は、現代の async/await パターンの基礎となる概念を示しており、非同期プログラミングの理解に非常に有用です。
