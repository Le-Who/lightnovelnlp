import re
import multiprocessing
from typing import List, Tuple, Any, Sequence

class SafeMatch:
    """Mimics re.Match object for the subset of methods used."""
    def __init__(self, start: int, end: int, group0: str, groups: Sequence[str]):
        self._start = start
        self._end = end
        self._group0 = group0
        self._groups = groups

    def start(self) -> int:
        return self._start

    def end(self) -> int:
        return self._end

    def group(self, i: int = 0) -> str:
        if i == 0:
            return self._group0
        if 1 <= i <= len(self._groups):
            return self._groups[i-1]
        raise IndexError("no such group")

    def groups(self) -> Sequence[str]:
        return self._groups

def _worker(pattern_str: str, flags: int, text: str, result_queue: multiprocessing.Queue):
    try:
        pattern = re.compile(pattern_str, flags)
        # Extract necessary data: start, end, group(0), and groups()
        matches_data = []
        for m in pattern.finditer(text):
            matches_data.append((m.start(), m.end(), m.group(0), m.groups()))
        result_queue.put(matches_data)
    except Exception as e:
        result_queue.put(e)

def safe_finditer(pattern_str: str, text: str, flags: int = 0, timeout: float = 2.0) -> List[SafeMatch]:
    """
    Safely runs re.finditer in a separate process with a timeout to prevent ReDoS.
    Returns a list of SafeMatch objects.
    """
    result_queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=_worker, args=(pattern_str, flags, text, result_queue))
    process.start()

    process.join(timeout)

    if process.is_alive():
        process.terminate()
        process.join()
        raise TimeoutError(f"Regex execution timed out after {timeout}s")

    if result_queue.empty():
        return []

    result = result_queue.get()

    if isinstance(result, Exception):
        raise result

    return [SafeMatch(start, end, g0, grps) for (start, end, g0, grps) in result]
