import time
import os
import tempfile
from core.benchmark_base import BenchmarkTest

class DiskWriteTest(BenchmarkTest):
    @property
    def name(self):
        return "Disk Write Speed"

    @property
    def description(self):
        return "Writes 500MB of data to temporary storage."

    def run(self, progress_callback):
        chunk_size = 1024 * 1024  # 1 MB
        total_chunks = 50 
        
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            start_time = time.time()
            data = os.urandom(chunk_size)
            
            for i in range(total_chunks):
                if self._stop_requested:
                    break
                
                tmp.write(data)
                
                # Update progress
                progress = int(((i + 1) / total_chunks) * 100)
                progress_callback(progress)
                time.sleep(0.02) # Artificial slow down to see UI update
                
            end_time = time.time()
            
        duration = end_time - start_time
        mb_per_sec = (total_chunks) / duration

        return {
            "speed_mb_s": round(mb_per_sec, 2),
            "status": "Success"
        }