import subprocess
import os
import json
import time
import shutil
from core.benchmark_base import BenchmarkTest

class FioSsdTest(BenchmarkTest):
    @property
    def name(self):
        return "FIO SSD Speed"

    @property
    def description(self):
        return "Measures IOPS and Bandwidth using FIO (Random R/W)."

    def run(self, progress_callback):
        # 1. Check for FIO
        if not shutil.which("fio"):
            return {
                "status": "Failed",
                "error": "fio not installed. Run 'sudo apt install fio'"
            }

        # 2. Setup Paths (use /tmp to avoid permission issues after install)
        filename = "/tmp/sigvet-fio_test_file"
        report_dir = os.path.join("/tmp", "sigvet-reports", "fio")
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, "fio_report.json")

        # 3. FIO Command (User specified parameters + json output)
        cmd = [
            "fio",
            "--name=mixed_r_w_test",
            "--ioengine=libaio",
            "--rw=randrw",
            "--rwmixread=70",
            "--bs=4k",
            "--size=2G",
            "--numjobs=4",
            "--iodepth=32",
            f"--filename={filename}",
            "--direct=1",
            "--group_reporting",
            "--time_based",
            "--runtime=60",
            "--output-format=json" # Essential for parsing logic below
        ]

        try:
            start_time = time.time()
            duration = 60 # Matches runtime=60
            
            # 4. Execute
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            while process.poll() is None:
                elapsed = time.time() - start_time
                pct = int((elapsed / duration) * 100)
                if pct > 99: pct = 99
                progress_callback(pct)
                
                if self._stop_requested:
                    process.terminate()
                    if os.path.exists(filename): os.remove(filename)
                    return {"status": "Cancelled"}
                time.sleep(0.5)

            stdout, stderr = process.communicate()
            progress_callback(100)

            # 5. Cleanup Test File
            if os.path.exists(filename):
                os.remove(filename)

            # 6. Save Raw Output
            with open(report_path, "w") as f:
                f.write(stdout)

            # 7. Robust JSON Parsing
            try:
                # Find start '{' and end '}' to ignore any preceding warning text
                json_start = stdout.find('{')
                json_end = stdout.rfind('}') + 1
                
                if json_start == -1 or json_end == 0:
                    return {"status": "Failed", "error": "No JSON found in FIO output"}
                
                clean_json = stdout[json_start:json_end]
                data = json.loads(clean_json)
                
            except json.JSONDecodeError as e:
                return {"status": "Failed", "error": f"JSON Decode Error: {str(e)}"}

            job = data["jobs"][0]
            read_iops = job["read"]["iops"]
            write_iops = job["write"]["iops"]
            
            # Convert KiB/s (default fio json unit) to MiB/s
            read_bw_mib = job["read"]["bw"] / 1024.0 
            write_bw_mib = job["write"]["bw"] / 1024.0

            # Formatting to match requested style '129k', '505MiB/s'
            def fmt_iops(val):
                if val >= 1000:
                    return f"{round(val/1000, 1)}k"
                return f"{round(val, 1)}"

            return {
                # Keys match YAML exactly for evaluator
                "read_IOPS": fmt_iops(read_iops),
                "write_IOPS": fmt_iops(write_iops),
                "read_BW": f"{int(read_bw_mib)}MiB/s",
                "write_BW": f"{int(write_bw_mib)}MiB/s",
                "status": "Success",
                "report": report_path
            }

        except Exception as e:
            if os.path.exists(filename): os.remove(filename)
            return {"status": "Failed", "error": str(e)}