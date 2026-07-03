import subprocess
import os
import re
import shutil
import time
from core.benchmark_base import BenchmarkTest

class Memtest(BenchmarkTest):
    @property
    def name(self):
        return "Memory Stability Test"

    @property
    def description(self):
        return "Runs memtester to check RAM stability."

    def run_memtester(self, memory="256M", loops=1, log_path=None, progress_callback=None):
        """
        Runs memtester for the specified memory and loops.
        """
        if log_path is None:
            log_path = os.path.join(os.getcwd(), "memtest_log.txt")

        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        cmd = ["memtester", str(memory), str(loops)]

        try:
            # Using Popen to capture output in real-time
            with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc, \
                 open(log_path, "w") as f_log:

                success = True
                
                # We can't know exact progress of memtester easily without complex parsing,
                # so we might just pulse or estimate if needed. 
                # For now, we rely on the caller to handle generic progress or just wait.
                
                for line in proc.stdout:
                    if self._stop_requested:
                        proc.terminate()
                        return "Cancelled"

                    f_log.write(line)
                    f_log.flush()
                    
                    # Check if line indicates failure
                    if re.search(r":\s*(FAIL|fail)", line):
                        success = False
                    
                    # Basic progress feedback (optional)
                    if progress_callback:
                        # Just a heartbeat to show it's alive
                        progress_callback(50) 

                proc.wait()

                if proc.returncode != 0 and self._stop_requested is False:
                    # Non-zero exit usually means error or failure found
                    # But memtester return codes: 0 = success, x01 = error, x02 = fail
                    success = False

            if self._stop_requested:
                return "Cancelled"

            return "Success" if success else "Failure"

        except Exception as e:
            return f"Error: {str(e)}"

    def run(self, progress_callback):
        # 1. Dependency Check
        if not shutil.which("memtester"):
            return {
                "status": "Failed",
                "error": "'memtester' not found. Run 'sudo apt install memtester'"
            }

        # 2. Setup (use /tmp to avoid permission issues after install)
        report_dir = os.path.join("/tmp", "sigvet-reports", "memtest")
        report_path = os.path.join(report_dir, "memtest_log.txt")
        
        # Test Parameters (Configurable or Defaults)
        # Testing a small amount (e.g. 256M) for 1 loop is a quick check.
        # For a full test, this should be higher, but that takes a long time.
        memory_to_test = "256M" 
        loops = 1

        progress_callback(10)
        
        # 3. Run
        result_status = self.run_memtester(
            memory=memory_to_test, 
            loops=loops, 
            log_path=report_path,
            progress_callback=lambda x: progress_callback(50) # Keep UI alive
        )
        
        progress_callback(100)

        # 4. Return
        status = "Success"
        if result_status == "Failure" or result_status.startswith("Error"):
            status = "Failed"
        elif result_status == "Cancelled":
            status = "Cancelled"

        return {
            "memory_check": "Pass" if result_status == "Success" else "Fail",
            "log_file": report_path,
            "status": status,
            "info": result_status 
        }