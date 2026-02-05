import multiprocessing
import re
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class SafeMatch:
    start_pos: int
    end_pos: int
    group1: Optional[str]

    def start(self): return self.start_pos
    def end(self): return self.end_pos
    def group(self, n=0):
        # Existing code uses match.group(1).
        # We only captured the first group.
        if n == 1: return self.group1
        if n == 0: return None # Not implemented/needed for now
        return None

def _worker(pattern: str, content: str, queue: multiprocessing.Queue):
    """
    Worker function that runs in a separate process.
    """
    try:
        # Strict compilation
        regex = re.compile(pattern, re.IGNORECASE)
        results = []
        for match in regex.finditer(content):
            # We capture start, end, and group(1)
            # If group(1) doesn't exist (e.g. pattern has no groups), it returns None or error?
            # The vulnerable code constructs pattern as f"\\n({user_pattern})", so group 1 always exists if it matches.

            # However, if user_pattern has nested groups, group(1) is the OUTER group.
            # Example: user_pattern = "(a)" -> regex = "\n((a))". group(1) is "(a)".

            g1 = None
            try:
                g1 = match.group(1)
            except IndexError:
                pass

            results.append((match.start(), match.end(), g1))

        queue.put({"success": True, "data": results})
    except Exception as e:
        queue.put({"success": False, "error": str(e)})

def safe_finditer(pattern: str, content: str, timeout: float = 2.0) -> List[SafeMatch]:
    """
    Executes regex finditer in a separate process with a timeout.
    Returns a list of SafeMatch objects.
    """
    # Use 'spawn' to be safe with multithreading (FastAPI)
    ctx = multiprocessing.get_context("spawn")
    queue = ctx.Queue()

    # Start the worker process
    p = ctx.Process(target=_worker, args=(pattern, content, queue))
    p.start()

    # Wait for completion or timeout
    p.join(timeout)

    if p.is_alive():
        p.terminate()
        p.join()
        raise TimeoutError("Regex processing timed out (potential ReDoS attempt)")

    if queue.empty():
         # This happens if process crashed (e.g. OOM) or didn't write to queue
         if p.exitcode != 0:
             raise RuntimeError(f"Regex worker process crashed with exit code {p.exitcode}")
         raise RuntimeError("Regex worker process returned no result")

    result = queue.get()
    if not result["success"]:
        # Re-raise the error from the worker (e.g. invalid regex syntax)
        # We wrap it in ValueError to act like re.error (which is a subclass of Exception)
        raise ValueError(f"Regex error: {result['error']}")

    return [SafeMatch(start, end, g1) for start, end, g1 in result["data"]]
