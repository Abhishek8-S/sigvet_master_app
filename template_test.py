import time
from core.benchmark_base import BenchmarkTest

# 1. Class must inherit from BenchmarkTest
class MyNewTest(BenchmarkTest):

    # 2. Define the Display Name
    @property
    def name(self):
        return "Name Appearing in UI"

    # 3. Define the Description (Tooltip)
    @property
    def description(self):
        return "Description of what this test actually does."

    # 4. The Logic
    def run(self, progress_callback):
        """
        Input: progress_callback(int) -> Call this with 0-100 to update UI bar.
        Output: Dictionary with results.
        """
        
        # --- YOUR SETUP CODE HERE ---
        results = {}
        iterations = 100
        
        # --- THE LOOP ---
        for i in range(iterations):
            # A. Check if user clicked cancel/stop
            if self._stop_requested:
                break
            
            # B. Do the work
            time.sleep(0.05) # Replace with actual math/logic
            
            # C. Update Progress Bar
            # Calculation: (Current / Total) * 100
            current_progress = int(((i + 1) / iterations) * 100)
            progress_callback(current_progress)

        # --- RETURN RESULTS ---
        return {
            "score": 9000,
            "fps": 60,
            "status": "Success"
        }