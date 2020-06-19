import asyncio
import chess
import collections
import shlex

from chess.engine import EngineProtocol, BaseCommand, ConfigMapping, INFO_NONE, Limit
from chess.engine import Info, PlayResult, INFO_ALL
from chess.engine import Option, ConfigValue, EngineError, AnalysisResult
from chess.engine import LOGGER, XBOARD_ERROR_REGEX, MANAGED_OPTIONS
from chess.engine import _parse_xboard_option, _parse_xboard_post
from chess.engine import SimpleEngine

from typing import Any, Awaitable, Callable, Coroutine, Deque, Dict, Generator, Generic
from typing import Iterable, Iterator, List, Mapping, MutableMapping, NamedTuple
from typing import Optional, Text, Tuple, Type, TypeVar, Union

CECPV1_TIMEOUT = 3.0


class CECPv1Protocol(EngineProtocol):
    """
    Chess Engine Communication Protocol version 1
    """

    def __init__(self) -> None:
        super().__init__()
        self.id = {}
        self.config: Dict[str, ConfigValue] = {}
        self.target_config: Dict[str, ConfigValue] = {}
        self.board = chess.Board()
        self.game: object = None
        self.first_game = True

    async def initialize(self) -> None:
        class CECPv1InitializeCommand(BaseCommand[CECPv1Protocol, None]):
            def check_initialized(self, engine: CECPv1Protocol) -> None:
                if engine.initialized:
                    raise EngineError("engine already initialized")

            def start(self, engine: CECPv1Protocol) -> None:
                self.firstline = True
                engine.send_line("xboard")
                self.timeout_handle = engine.loop.call_later(CECPV1_TIMEOUT, lambda: 
                                                             self.timeout(engine))

            def timeout(self, engine: CECPv1Protocol) -> None:
                LOGGER.error("%s: Timeout during initialization", engine)
                self.end(engine)

            def line_received(self, engine: CECPv1Protocol, line: str) -> None:
                print(f'line = {line}')
                if self.firstline and line:
                    engine.id["name"] = line
                    self.firstline = False
                elif line.startswith("#"):
                    pass
                elif line.startswith("feature "):
                    self._feature(engine, line.split(" ", 1)[1])
                elif XBOARD_ERROR_REGEX.match(line):
                    raise EngineError(line)

            def _feature(self, engine: CECPv1Protocol, arg: str) -> None:
                pass

            def end(self, engine: CECPv1Protocol) -> None:

                engine.initialized = True
                self.result.set_result(None)
                self.set_finished()

        return await self.communicate(CECPv1InitializeCommand)

    def _new(self, board: chess.Board, game: object, options: ConfigMapping) -> None:
        self._configure(options)

        # Set up starting position.
        root = board.root()
        new_options = "random" in options or "computer" in options
        new_game = (self.first_game or self.game != game or new_options or
                    root != self.board.root())
        self.game = game
        self.first_game = False
        if new_game:
            self.board = root
            self.send_line("new")

            if self.config.get("random"):
                self.send_line("random")
            if self.config.get("computer"):
                self.send_line("computer")

        self.send_line("force")

        # Undo moves until common position.
        common_stack_len = 0
        if not new_game:
            for left, right in zip(self.board.move_stack, board.move_stack):
                if left == right:
                    common_stack_len += 1
                else:
                    break

            while len(self.board.move_stack) > common_stack_len + 1:
                self.send_line("remove")
                self.board.pop()
                self.board.pop()

            while len(self.board.move_stack) > common_stack_len:
                self.send_line("undo")
                self.board.pop()

        # Play moves from board stack.
        for move in board.move_stack[common_stack_len:]:
            self.send_line(self.board.xboard(move))
            self.board.push(move)

    async def ping(self) -> None:
        pass

    async def play(self, board: chess.Board, limit: Limit, *, game: object = None,
                   info: Info = INFO_NONE, ponder: bool = False,
                   root_moves: Optional[Iterable[chess.Move]] = None,
                   options: ConfigMapping = {}) -> PlayResult:
        if root_moves is not None:
            raise EngineError("""play with root_moves, but xboard supports 
                              'include' only in analysis mode""")

        class CECPv1PlayCommand(BaseCommand[CECPv1Protocol, PlayResult]):
            def start(self, engine: CECPv1Protocol) -> None:
                self.play_result = PlayResult(None, None)
                self.stopped = False
                self.pong_after_move: Optional[str] = None
                self.pong_after_ponder: Optional[str] = None

                # Set game, position and configure.
                engine._new(board, game, options)

                # Limit or time control.
                increment = limit.white_inc if board.turn else limit.black_inc
                if limit.remaining_moves or increment:
                    base_mins, base_secs = divmod(int((limit.white_clock if board.turn
                                                  else limit.black_clock) or 0), 60)
                    engine.send_line(f"level {limit.remaining_moves or 0} {base_mins}:"
                                     f"{base_secs:02d} {increment}")

                if limit.nodes is not None:
                    if (limit.time is not None or limit.white_clock is not None
                            or limit.black_clock is not None or increment is not None):
                        raise EngineError("xboard does not support mixing node limits "
                                          "with time limits")

                    # engine.send_line("nps 1")
                    # engine.send_line(f"st {int(limit.nodes)}")
                if limit.depth is not None:
                    engine.send_line(f"sd {limit.depth}")
                if limit.time is not None:
                    engine.send_line(f"st {limit.time}")
                if limit.white_clock is not None:
                    engine.send_line("{} {}".format("time" if board.turn else "otim",
                                     int(limit.white_clock * 100)))
                if limit.black_clock is not None:
                    engine.send_line("{} {}".format("otim" if board.turn else "time",
                                     int(limit.black_clock * 100)))

                # Start thinking.
                engine.send_line("post" if info else "nopost")
                engine.send_line("hard" if ponder else "easy")
                engine.send_line("go")

            def line_received(self, engine: CECPv1Protocol, line: str) -> None:
                print(f"Line: {line}")
                if line.startswith("move "):
                    self._move(engine, line.split(" ", 1)[1])
                elif line.startswith("Hint: "):
                    self._hint(engine, line.split(" ", 1)[1])
                elif line == self.pong_after_move:
                    if not self.result.done():
                        self.result.set_result(self.play_result)
                    if not ponder:
                        self.set_finished()
                elif line == self.pong_after_ponder:
                    if not self.result.done():
                        self.result.set_result(self.play_result)
                    self.set_finished()
                elif line == "offer draw":
                    if not self.result.done():
                        self.play_result.draw_offered = True
                    self._ping_after_move(engine)
                elif line == "resign":
                    if not self.result.done():
                        self.play_result.resigned = True
                    self._ping_after_move(engine)
                elif (line.startswith("1-0") or line.startswith("0-1")
                        or line.startswith("1/2-1/2")):
                    self._ping_after_move(engine)
                elif line.startswith("#"):
                    pass
                elif XBOARD_ERROR_REGEX.match(line):
                    engine.first_game = True  # Board state might no longer be in sync
                    raise EngineError(line)
                elif len(line.split()) >= 4 and line.lstrip()[0].isdigit():
                    self._post(engine, line)
                else:
                    LOGGER.warning("%s: Unexpected engine output: %s", engine, line)

            def _post(self, engine: CECPv1Protocol, line: str) -> None:
                if not self.result.done():
                    self.play_result.info = _parse_xboard_post(line, engine.board, info)

            def _move(self, engine: CECPv1Protocol, arg: str) -> None:
                print(f"Line: {arg}")
                if not self.result.done() and self.play_result.move is None:
                    try:
                        self.play_result.move = engine.board.push_xboard(arg)
                    except ValueError as err:
                        self.result.set_exception(EngineError(err))
                    else:
                        self._ping_after_move(engine)
                else:
                    try:
                        engine.board.push_xboard(arg)
                    except ValueError:
                        LOGGER.exception("exception playing unexpected move")

            def _hint(self, engine: CECPv1Protocol, arg: str) -> None:
                if (not self.result.done() and self.play_result.move is not None
                        and self.play_result.ponder is None):
                    try:
                        self.play_result.ponder = engine.board.parse_xboard(arg)
                    except ValueError:
                        LOGGER.exception("exception parsing hint")
                else:
                    LOGGER.warning("unexpected hint: %r", arg)

            def _ping_after_move(self, engine: CECPv1Protocol) -> None:
                pass

            def cancel(self, engine: CECPv1Protocol) -> None:
                if self.stopped:
                    return
                self.stopped = True

                if self.result.cancelled():
                    engine.send_line("?")

                if ponder:
                    engine.send_line("easy")

            def engine_terminated(self, engine: CECPv1Protocol, exc: Exception) -> None:
                # Allow terminating engine while pondering.
                if not self.result.done():
                    super().engine_terminated(engine, exc)

        return await self.communicate(CECPv1PlayCommand)

    async def analysis(self, board: chess.Board, limit: Optional[Limit] = None, *,
                       multipv: Optional[int] = None, game: object = None,
                       info: Info = INFO_ALL,
                       root_moves: Optional[Iterable[chess.Move]] = None,
                       options: ConfigMapping = {}) -> "AnalysisResult":
        pass

    def _setoption(self, name: str, value: ConfigValue) -> None:
        pass

    def _configure(self, options: ConfigMapping) -> None:
        for name, value in collections.ChainMap(options, self.target_config).items():
            if name.lower() in MANAGED_OPTIONS:
                raise EngineError(f"cannot set {name} which is automatically managed")
            self._setoption(name, value)

    async def configure(self, options: ConfigMapping) -> None:
        class CECPv1ConfigureCommand(BaseCommand[CECPv1Protocol, None]):
            def start(self, engine: CECPv1Protocol) -> None:
                engine._configure(options)
                engine.target_config.update({name: value for name, value in 
                                            options.items() if value is not None})
                self.result.set_result(None)
                self.set_finished()

        return await self.communicate(CECPv1ConfigureCommand)

    async def quit(self) -> None:
        self.send_line("quit")
        await asyncio.shield(self.returncode)


async def popen_cecpv1(command: Union[str, List[str]], *, setpgrp: bool = False,
                       **popen_args: Any) -> Tuple[asyncio.SubprocessTransport,
                                                   CECPv1Protocol]:
    """
    Spawns and initializes an CECPv1 engine.

    :param command: Path of the engine executable, or a list including the
        path and arguments.
    :param setpgrp: Open the engine process in a new process group. This will
        stop signals (such as keyboard interrupts) from propagating from the
        parent process. Defaults to ``False``.
    :param popen_args: Additional arguments for
        `popen <https://docs.python.org/3/library/subprocess.html#popen-constructor>`_.
        Do not set ``stdin``, ``stdout``, ``bufsize`` or
        ``universal_newlines``.

    Returns a subprocess transport and engine protocol pair.
    """
    transport, protocol = await CECPv1Protocol.popen(command, setpgrp=setpgrp,
                                                     **popen_args)
    try:
        await protocol.initialize()
    except:
        transport.close()
        raise
    return transport, protocol


class CECPv1Engine(SimpleEngine):
    def __init__(self, transport: asyncio.SubprocessTransport, protocol: EngineProtocol,
                 *, timeout: Optional[float] = 10.0) -> None:
        super().__init__(transport, protocol, timeout=timeout)

    @classmethod
    def popen_cecpv1(cls, command: Union[str, List[str]], *,
                     timeout: Optional[float] = 10.0, debug: bool = False,
                     setpgrp: bool = False, **popen_args: Any) -> "SimpleEngine":
        """
        Spawns and initializes a CECPv1 engine.
        Returns a :class:`~chess.engine.SimpleEngine` instance.
        """
        return cls.popen(CECPv1Protocol, command, timeout=timeout, debug=debug, 
                         setpgrp=setpgrp, **popen_args)

