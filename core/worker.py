from PyQt6.QtCore import QThread, pyqtSignal

class BenchmarkWorker(QThread):
    """
    Runs the list of tests in a background thread.
    Emits signals to update the UI.
    """
    progress_current = pyqtSignal(int)
    progress_total = pyqtSignal(int)
    test_finished = pyqtSignal(str, dict)
    all_finished = pyqtSignal()
    
    def __init__(self, tests_to_run):
        super().__init__()
        self.tests = tests_to_run
        self.is_running = True

    def run(self):
        total_tests = len(self.tests)
        
        for index, test in enumerate(self.tests):
            if not self.is_running: break
            
            # Reset current bar
            self.progress_current.emit(0)
            
            # Bridge callback to signal
            def callback(val):
                self.progress_current.emit(val)
                
            try:
                result = test.run(callback)
            except Exception as e:
                result = {"error": str(e), "status": "Failed"}
            
            self.test_finished.emit(test.name, result)
            
            # Update total bar
            total_pct = int(((index + 1) / total_tests) * 100)
            self.progress_total.emit(total_pct)
            
        self.all_finished.emit()

    def stop(self):
        self.is_running = False
        for test in self.tests:
            test.stop()