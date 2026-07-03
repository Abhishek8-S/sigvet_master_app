import subprocess
import time
import shutil
import re
from core.benchmark_base import BenchmarkTest

class WifiReliabilityTest(BenchmarkTest):
    @property
    def name(self):
        return "Wi-Fi Module Reliability"

    @property
    def description(self):
        return "Checks Wi-Fi radio toggle, scanning, and connection stability."

    def run(self, progress_callback):
        # 1. Dependency Check
        if not shutil.which("nmcli"):
            return {
                "status": "Failed",
                "error": "'nmcli' not found. Is NetworkManager installed?"
            }

        # Load Config
        wifi_conf = self.config.get("wifi_reliability", {})
        duration = wifi_conf.get("duration_seconds", 180) # Default 3 mins
        target = wifi_conf.get("ping_target", "8.8.8.8")

        try:
            # 2. Check Radio Status
            progress_callback(5)
            status_cmd = ["nmcli", "radio", "wifi"]
            result = subprocess.run(status_cmd, capture_output=True, text=True)
            initial_state = result.stdout.strip()
            
            if initial_state != "enabled":
                subprocess.run(["nmcli", "radio", "wifi", "on"], check=True)
                time.sleep(2) 

            # 3. Toggle Test (Off -> On)
            progress_callback(10)
            if self._stop_requested: return {"status": "Cancelled"}
            
            subprocess.run(["nmcli", "radio", "wifi", "off"], check=True)
            time.sleep(1)
            res_off = subprocess.run(status_cmd, capture_output=True, text=True).stdout.strip()
            if res_off != "disabled":
                return {"status": "Failed", "error": "Hardware failed to turn off Wi-Fi radio."}
            
            subprocess.run(["nmcli", "radio", "wifi", "on"], check=True)
            time.sleep(5) # Wait longer for reconnection before pinging
            
            # 4. Scan Test
            progress_callback(20)
            if self._stop_requested: return {"status": "Cancelled"}
            
            scan_cmd = ["nmcli", "dev", "wifi", "list"]
            scan_res = subprocess.run(scan_cmd, capture_output=True, text=True)
            if scan_res.returncode != 0:
                 return {"status": "Failed", "error": "Failed to scan for networks."}
            
            network_count = len(scan_res.stdout.splitlines()) - 1 
            if network_count < 0: network_count = 0

            # 5. Stability Ping Test (Duration based)
            # We will stream the ping output or run chunks to update progress
            start_ping = time.time()
            interval = 0.2
            # Total packets needed = duration / interval
            count = int(duration / interval)
            
            # We use a subprocess Popen to allow cancelling mid-way easily
            ping_cmd = ["ping", "-c", str(count), "-i", str(interval), target]
            
            process = subprocess.Popen(
                ping_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            
            # Monitor progress
            while process.poll() is None:
                elapsed = time.time() - start_ping
                # Map elapsed time (0 to duration) to progress (20 to 95)
                # progress = 20 + (elapsed/duration * 75)
                prog = 20 + int((elapsed / duration) * 75)
                if prog > 95: prog = 95
                progress_callback(prog)
                
                if self._stop_requested:
                    process.terminate()
                    return {"status": "Cancelled"}
                time.sleep(0.5)
            
            stdout, stderr = process.communicate()
            
            packet_loss = 100.0
            avg_latency = 0.0
            
            if process.returncode == 0:
                loss_match = re.search(r"(\d+)% packet loss", stdout)
                if loss_match:
                    packet_loss = float(loss_match.group(1))
                
                lat_match = re.search(r"min/avg/max/mdev = [\d\.]+/([\d\.]+)/", stdout)
                if lat_match:
                    avg_latency = float(lat_match.group(1))
            else:
                # Ping command failed (network unreachable?)
                pass

            progress_callback(100)
            
            # Grading Logic
            raw_score = 10
            # Strict penalty: -1 per 1% loss? Or -1 per 10%?
            # User wants a score out of 10.
            # Let's say >0% loss is bad.
            if packet_loss > 0:
                # 1% loss = 9/10
                # 5% loss = 5/10
                # >10% loss = 1/10
                penalty = int(packet_loss)
                raw_score -= penalty
            
            if raw_score < 1: raw_score = 1
            if packet_loss == 100: raw_score = 0 # Or 1

            reliability = "Excellent"
            if packet_loss > 0: reliability = "Unstable"
            if packet_loss > 5: reliability = "Poor"
            if packet_loss == 100: reliability = "Disconnected"

            return {
                "wifi_score": f"{raw_score}/10",
                "radio_toggle": "Passed",
                "networks_found": network_count,
                "packet_loss": f"{packet_loss}%",
                "avg_latency": f"{avg_latency}ms",
                "test_duration": f"{duration}s",
                "status": "Success"
            }

        except Exception as e:
            subprocess.run(["nmcli", "radio", "wifi", "on"], stderr=subprocess.DEVNULL)
            return {"status": "Failed", "error": str(e)}