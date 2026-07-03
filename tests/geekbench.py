import subprocess
import os
import re
import time
import requests
from core.benchmark_base import BenchmarkTest

class GeekbenchTest(BenchmarkTest):
    @property
    def name(self):
        return "Geekbench CPU"

    @property
    def description(self):
        return "Runs Geekbench 6 from utils/ folder."

    def run(self, progress_callback):
        # 1. Locate Executable — use script location, not cwd, so it works when installed
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        base_dir = script_dir
        exe_path = os.path.join(base_dir, "utils", "geekbench", "geekbench6")
        
        if not os.path.exists(exe_path):
            return {
                "status": "Failed", 
                "error": f"Binary not found at: {exe_path}"
            }

        # 2. Setup Reporting (use /tmp to avoid permission issues after install)
        report_dir = os.path.join("/tmp", "sigvet-reports", "geekbench")
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, "geekbench_report.txt")

        # 3. Execution
        cmd = [exe_path]
        
        try:
            start_time = time.time()
            estimated_duration = 180 
            
            with open(report_path, "w") as out_file:
                process = subprocess.Popen(
                    cmd, 
                    stdout=out_file, 
                    stderr=out_file, 
                    text=True
                )

                while process.poll() is None:
                    elapsed = time.time() - start_time
                    pct = int((elapsed / estimated_duration) * 100)
                    if pct > 95: pct = 95
                    progress_callback(pct)
                    
                    if self._stop_requested:
                        process.terminate()
                        process.wait()
                        return {"status": "Cancelled"}
                    time.sleep(1)
                
                process.wait()

            progress_callback(100)

            # 4. Read Output
            with open(report_path, "r") as f:
                stdout = f.read()

            # 5. Parse Output
            single_score = 0
            multi_score = 0
            url = "N/A"
            fetch_error = None

            # Attempt A: Local Parse (Pro version outputs this directly)
            s_match = re.search(r"Single-Core Score\s+(\d+)", stdout)
            if s_match: single_score = int(s_match.group(1))
            
            m_match = re.search(r"Multi-Core Score\s+(\d+)", stdout)
            if m_match: multi_score = int(m_match.group(1))

            # Attempt B: Web Parse (Free version provides URL)
            # Look for: https://browser.geekbench.com/v6/cpu/15606570
            u_match = re.search(r"https://browser\.geekbench\.com/v\d+/\w+/\d+", stdout)
            
            if u_match:
                url = u_match.group(0)
                # Only fetch if we didn't find scores locally
                if single_score == 0:
                    try:
                        # Fetch HTML
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                        }
                        response = requests.get(url, headers=headers, timeout=15)
                        response.raise_for_status()
                        html_content = response.text
                        
                        # Save HTML for debugging if needed
                        with open(os.path.join(report_dir, "last_result.html"), "w") as hf:
                            hf.write(html_content)

                        # Parse Scores from HTML using Regex
                        # Structure: <div class='score'>1575</div> ... <div class='score'>4862</div>
                        # The first occurrence is usually Single Core, second is Multi Core in the 'cpu' wrapper
                        
                        scores = re.findall(r"<div class=['\"]score['\"]>(\d+)</div>", html_content)
                        
                        if len(scores) >= 2:
                            single_score = int(scores[0])
                            multi_score = int(scores[1])
                        else:
                            fetch_error = "Could not find score divs in HTML"

                    except Exception as e:
                        fetch_error = str(e)
            else:
                if single_score == 0:
                    fetch_error = "No Geekbench URL found in output"

            if single_score == 0 and multi_score == 0:
                 error_msg = "Could not parse scores."
                 if fetch_error:
                     error_msg += f" Web fetch failed: {fetch_error}"
                 
                 return {
                    "status": "Failed",
                    "error": error_msg,
                    "report_saved": report_path
                }

            return {
                "single_core_score": single_score,
                "multi_core_score": multi_score,
                "result_url": url,
                "status": "Success"
            }

        except Exception as e:
            return {"status": "Failed", "error": str(e)}