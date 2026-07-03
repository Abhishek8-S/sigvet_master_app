import time
try:
    import speedtest
except ImportError:
    speedtest = None

from core.benchmark_base import BenchmarkTest

class NetworkSpeedTest(BenchmarkTest):
    @property
    def name(self):
        return "Network Performance"

    @property
    def description(self):
        return "Measures Ping, Download, and Upload speeds using Speedtest.net."

    def run(self, progress_callback):
        if speedtest is None:
            return {
                "status": "Failed",
                "error": "Module 'speedtest-cli' not found. Run: pip install speedtest-cli"
            }

        try:
            st = speedtest.Speedtest()
            
            # 1. Get Best Server
            progress_callback(10)
            if self._stop_requested: return {"status": "Cancelled"}
            st.get_best_server()
            
            # 2. Download Test
            progress_callback(30)
            if self._stop_requested: return {"status": "Cancelled"}
            download_speed = st.download() / 1_000_000 # Convert to Mbps
            
            # 3. Upload Test
            progress_callback(70)
            if self._stop_requested: return {"status": "Cancelled"}
            upload_speed = st.upload() / 1_000_000 # Convert to Mbps
            
            # 4. Results
            progress_callback(100)
            ping = st.results.ping
            
            # Grading Logic (Simple Example)
            # Base grade on Download speed (e.g., 100Mbps = 9/10)
            # You can adjust this logic or rely on the YAML comparator
            grade = min(10, int(download_speed / 10)) 
            if grade < 1: grade = 1
            
            return {
                "download_mbps": round(download_speed, 2),
                "upload_mbps": round(upload_speed, 2),
                "ping_ms": round(ping, 1),
                "network_grade": f"{grade}/10",
                "status": "Success"
            }

        except Exception as e:
            return {"status": "Failed", "error": str(e)}