import asyncio
import chess
from chess.engine import UciProtocol, XBoardProtocol
from chess.engine import EngineProtocol, BaseCommand, ConfigMapping, INFO_NONE, Limit
from chess.engine import Info, PlayResult, INFO_ALL

from typing import Any, Awaitable, Callable, Coroutine, Deque, Dict, Generator, Generic, Iterable, Iterator, List, Mapping, MutableMapping, NamedTuple, Optional, Text, Tuple, Type, TypeVar, Union

MAX_TIMEOUT = 2.0

class ProbingProtocol(EngineProtocol):
    """
    A protocol for probing the actual protocol supported by an engine.
    """

    protocol = None

    def __init__(self) -> None:
        super().__init__()

    async def probe(self):
        class ProbingCommand(BaseCommand[ProbingProtocol, None]):

            def check_initialized(self, engine: ProbingProtocol):
                pass

            def start(self, engine: ProbingProtocol) -> None:
                engine.send_line("uci")
                engine.send_line("xboard")
                engine.send_line("protover 2")
                self.timeout_handle = engine.loop.call_later(MAX_TIMEOUT, lambda: self.timeout(engine))

            def timeout(self, engine: ProbingProtocol) -> None:
                print("%s: Timeout during probing", engine)
                self.result.set_result(None)
                self.set_finished()
                ProbingProtocol.protocol = None

            def line_received(self, engine: ProbingProtocol, line: str) -> None:
                if not self.result.done():
                    if line == "uciok":
                        self.timeout_handle.cancel()
                        self.result.set_result(None)
                        self.set_finished()
                        ProbingProtocol.protocol = UciProtocol
                    elif line.startswith("feature done"):
                        self.timeout_handle.cancel()
                        self.result.set_result(None)
                        self.set_finished()
                        ProbingProtocol.protocol = XBoardProtocol

        return await self.communicate(ProbingCommand)

    async def initialize(self):
        pass

    async def ping(self) -> None:
        pass

    async def configure(self, options: ConfigMapping) -> None:
        pass

    async def play(self, board: chess.Board, limit: Limit, *, game: object = None, info: Info = INFO_NONE, ponder: bool = False, root_moves: Optional[Iterable[chess.Move]] = None, options: ConfigMapping = {}) -> PlayResult:
        pass

    async def analysis(self, board: chess.Board, limit: Optional[Limit] = None, *, multipv: Optional[int] = None, game: object = None, info: Info = INFO_ALL, root_moves: Optional[Iterable[chess.Move]] = None, options: ConfigMapping = {}) -> "AnalysisResult":
        pass

    async def quit(self) -> None:
        self.send_line("quit")
        await asyncio.shield(self.returncode)


async def popen_probe(command: Union[str, List[str]], *, setpgrp: bool = False, **popen_args: Any):
    """
    Spawns and probes an engine for its protocol.

    :param command: Path of the engine executable, or a list including the
        path and arguments.
    :param setpgrp: Open the engine process in a new process group. This will
        stop signals (such as keyboard interrupts) from propagating from the
        parent process. Defaults to ``False``.
    :param popen_args: Additional arguments for
        `popen <https://docs.python.org/3/library/subprocess.html#popen-constructor>`_.
        Do not set ``stdin``, ``stdout``, ``bufsize`` or
        ``universal_newlines``.
    """
    transport, protocol = await ProbingProtocol.popen(command, setpgrp=setpgrp, **popen_args)
    try:
        await protocol.probe()
        await protocol.quit()
    except:
        raise "Exception occurred during popen_probe, probing for protocol."
    finally:
        transport.close()
    return ProbingProtocol.protocol
