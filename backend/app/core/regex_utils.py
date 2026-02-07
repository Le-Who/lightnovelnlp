import multiprocessing
import re
import queue
import logging
from typing import List, Any, Dict, Optional

logger = logging.getLogger(__name__)

class SafeMatch:
    """
    A mimic of re.Match that is safe to pass between processes
    and only exposes necessary methods.
    """
    def __init__(self, start: int, end: int, groups: tuple, group_0: str):
        self._start = start
        self._end = end
        self._groups = groups
        self._group_0 = group_0

    def start(self) -> int:
        return self._start

    def end(self) -> int:
        return self._end

    def group(self, index: int = 0) -> str | Any:
        if index == 0:
            return self._group_0
        if index > len(self._groups):
            raise IndexError("no such group")
        return self._groups[index - 1]

    def groups(self) -> tuple:
        return self._groups

def _finditer_worker(pattern_str: str, text: str, flags: int, output_queue: multiprocessing.Queue):
    """
    Worker function to run regex search in a separate process.
    """
    try:
        matches_data = []
        # Use finditer to find all matches
        for match in re.finditer(pattern_str, text, flags):
            matches_data.append({
                'start': match.start(),
                'end': match.end(),
                'groups': match.groups(),
                'group_0': match.group(0)
            })
        output_queue.put({'success': True, 'result': matches_data})
    except Exception as e:
        output_queue.put({'success': False, 'error': str(e)})

def safe_finditer(pattern: str, text: str, flags: int = 0, timeout: float = 2.0) -> List[SafeMatch]:
    """
    Executes re.finditer in a separate process with a timeout to prevent ReDoS.
    Returns a list of SafeMatch objects.
    """
    # Use spawn context to avoid issues with forked processes inheriting incompatible state (like DB connections)
    ctx = multiprocessing.get_context('spawn')
    output_queue = ctx.Queue()

    process = ctx.Process(
        target=_finditer_worker,
        args=(pattern, text, flags, output_queue)
    )

    process.start()

    try:
        result = output_queue.get(timeout=timeout)
        process.join()
    except queue.Empty:
        process.terminate()
        process.join()
        logger.error(f"Regex processing timed out after {timeout}s")
        raise TimeoutError("Regex processing timed out")

    if not result.get('success'):
        # Re-raise the error from the worker
        error_msg = result.get('error', 'Unknown regex error')
        logger.error(f"Regex processing failed: {error_msg}")
        raise re.error(error_msg)

    safe_matches = []
    for m_data in result['result']:
        safe_matches.append(SafeMatch(
            start=m_data['start'],
            end=m_data['end'],
            groups=m_data['groups'],
            group_0=m_data['group_0']
        ))

    return safe_matches
