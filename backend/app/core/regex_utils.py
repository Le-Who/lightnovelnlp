import re
import multiprocessing
import queue  # Required for queue.Empty
from typing import Iterator, List, Dict, Any, Union, Tuple


class SafeMatch:
    """
    A safe version of re.Match that holds data extracted from a separate process.
    Mimics the interface of re.Match.
    """

    def __init__(
        self,
        spans: List[Tuple[int, int]],
        groups: tuple,
        group_dict: Dict[str, Any],
        string: str,
    ):
        self._spans = spans
        self._groups = groups
        self._group_dict = group_dict
        self._string = string

    def start(self, group: Union[int, str] = 0) -> int:
        return self.span(group)[0]

    def end(self, group: Union[int, str] = 0) -> int:
        return self.span(group)[1]

    def span(self, group: Union[int, str] = 0) -> Tuple[int, int]:
        if isinstance(group, str):
            raise NotImplementedError(
                "Named groups not supported in start/end/span yet"
            )
        return self._spans[group]

    def group(self, *args) -> Union[str, Tuple[str, ...], None]:
        if not args:
            return self._string[self._spans[0][0] : self._spans[0][1]]

        results = []
        for arg in args:
            if isinstance(arg, int):
                if arg == 0:
                    results.append(self._string[self._spans[0][0] : self._spans[0][1]])
                elif 0 < arg <= len(self._groups):
                    results.append(self._groups[arg - 1])
                else:
                    results.append(None)
            elif isinstance(arg, str):
                results.append(self._group_dict.get(arg))
            else:
                raise TypeError(f"Invalid group type: {type(arg)}")

        if len(args) == 1:
            return results[0]
        return tuple(results)

    def groups(self, default=None) -> tuple:
        return tuple(g if g is not None else default for g in self._groups)

    def groupdict(self, default=None) -> Dict[str, Any]:
        return {
            k: (v if v is not None else default) for k, v in self._group_dict.items()
        }


def _finditer_worker(
    pattern_str: str, flags: int, text: str, queue: multiprocessing.Queue
):
    """
    Worker function to run regex search in a separate process.
    """
    try:
        pattern = re.compile(pattern_str, flags)
        matches_data = []

        # Find all matches
        # We must iterate fully to ensure no ReDoS happens during iteration
        for match in pattern.finditer(text):
            # Capture spans for all groups (0 to N)
            n_groups = len(match.groups())
            spans = [match.span(i) for i in range(n_groups + 1)]

            matches_data.append((spans, match.groups(), match.groupdict()))

        queue.put(("success", matches_data))
    except Exception as e:
        queue.put(("error", str(e)))


def safe_finditer(
    pattern: Union[str, re.Pattern], text: str, timeout: float = 1.0
) -> Iterator[SafeMatch]:
    """
    Executes re.finditer in a separate process with a timeout to prevent ReDoS.
    Returns an iterator of SafeMatch objects.

    Args:
        pattern: Regex pattern string or re.Pattern object
        text: Text to search
        timeout: Timeout in seconds (default 1.0)

    Raises:
        TimeoutError: If regex execution exceeds timeout
        RuntimeError: If worker process fails
    """
    if isinstance(pattern, re.Pattern):
        pattern_str = pattern.pattern
        flags = pattern.flags
    else:
        pattern_str = pattern
        flags = 0

    # Use 'spawn' context for safety across platforms and threading environments
    ctx = multiprocessing.get_context("spawn")
    result_queue = ctx.Queue()

    process = ctx.Process(
        target=_finditer_worker, args=(pattern_str, flags, text, result_queue)
    )

    process.start()

    try:
        # Wait for result with timeout
        # This avoids deadlock where queue is full and process waits for reader,
        # while reader waits for process join.
        status, result = result_queue.get(timeout=timeout)

        # If we got result, the worker is likely done or finishing.
        process.join(timeout=0.1)
        if process.is_alive():
            process.terminate()
            process.join()

    except queue.Empty:
        process.terminate()
        process.join()
        raise TimeoutError(f"Regex execution timed out after {timeout}s")

    if status == "error":
        raise RuntimeError(f"Regex error: {result}")

    # Reconstruct SafeMatch objects
    for spans, groups, group_dict in result:
        yield SafeMatch(spans, groups, group_dict, text)
