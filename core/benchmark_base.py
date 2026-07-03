from abc import ABC, abstractmethod
import time

class BenchmarkTest(ABC):
    """
    Abstract Base Class for all benchmark tests.
    Every test in the 'tests' folder must inherit from this.
    """
    
    def __init__(self, config):
        self.config = config
        self._stop_requested = False

    @property
    @abstractmethod
    def name(self) -> str:
        """The display name of the test."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description for the UI."""
        pass

    @abstractmethod
    def run(self, progress_callback) -> dict:
        """
        Execute the benchmark.
        
        Args:
            progress_callback (function): A function to call with (int) percent 0-100.
            
        Returns:
            dict: Results (e.g., {"score": 120, "time": 4.5})
        """
        pass

    def stop(self):
        """Signal the test to stop gracefully."""
        self._stop_requested = True