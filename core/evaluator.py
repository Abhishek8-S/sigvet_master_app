from core.config import BENCHMARK_STANDARDS
import re

def parse_value(val):
    """Parses strings like '129k', '505MiB/s' into floats."""
    if isinstance(val, (int, float)):
        return float(val)
    
    val = str(val).strip()
    # Handle 'k' suffix (thousands)
    if val.lower().endswith('k'):
        try:
            return float(val[:-1]) * 1000
        except ValueError:
            pass
            
    # Handle 'MiB/s' or 'MB/s'
    match = re.match(r"([\d\.]+)\s*(MiB/s|MB/s)", val, re.IGNORECASE)
    if match:
        return float(match.group(1))
        
    try:
        return float(val)
    except ValueError:
        # Return the raw string for exact matches (like 'Pass', '10/10')
        return val

def evaluate_result(test_name, result_data):
    """
    Analyzes a test result against benchmark standards.
    Returns: (has_benchmark, [list_of_comparisons])
    Comparison dict: {label, expected, actual, deviation, dev_color}
    """
    std = BENCHMARK_STANDARDS.get(test_name)
    if not std or not isinstance(std, dict):
        return False, []

    comparisons = []

    # Helper to process a single metric config
    def process_metric(metric_conf):
        target_key = metric_conf.get('key')
        expected_raw = metric_conf.get('expected')
        unit = metric_conf.get('unit', '')
        
        if target_key not in result_data:
            return

        actual_raw = result_data[target_key]
        
        expected_val = parse_value(expected_raw)
        actual_val = parse_value(actual_raw)

        if expected_val is None or actual_val is None:
            return

        # Handle String Exact Matches (e.g. 'Pass' vs 'Passed' vs '10/10')
        if isinstance(expected_val, str) or isinstance(actual_val, str):
            exp_str = str(expected_val).lower().strip()
            act_str = str(actual_val).lower().strip()
            
            # Special logic for wifi score (assume "x/10" where x >= 7 is pass)
            if target_key == 'wifi_score' and '/' in act_str:
                try:
                    score = float(act_str.split('/')[0])
                    is_pass = score >= 7
                except ValueError:
                    is_pass = False
            # Standard exact/substring match
            else:
                is_pass = (exp_str in act_str) or (act_str in exp_str)

            if is_pass:
                deviation_str = "Match"
                color = "#a6e3a1" # Green
            else:
                deviation_str = "Failed"
                color = "#f38ba8" # Red
                
            comparisons.append({
                "label": target_key.replace("_", " ").title(),
                "expected": f"{expected_raw}{unit}",
                "actual": f"{actual_raw}{unit}",
                "deviation": deviation_str,
                "dev_color": color
            })
            return

        # Handle Numeric Deviation
        try:
            diff = actual_val - expected_val
            # Avoid division by zero
            if expected_val == 0:
                percent = 0.0
            else:
                percent = (diff / expected_val) * 100
            
            sign = "+" if percent > 0 else ""
            deviation_str = f"{sign}{percent:.1f}%"
            
            # Simple color logic: Green if >= expected (or close), Red if < expected
            # (Assuming higher is better for all current tests)
            color = "#a6e3a1" if percent >= -5.0 else "#f38ba8"

            comparisons.append({
                "label": target_key.replace("_", " ").title(),
                "expected": f"{expected_raw}{unit}",
                "actual": f"{actual_raw}{unit}",
                "deviation": deviation_str,
                "dev_color": color
            })
        except Exception:
            pass

    # Support multiple metrics (New Format)
    if 'metrics' in std:
        for m in std['metrics']:
            process_metric(m)
    
    # Support single key (Old Format) - Backward compatibility
    elif 'key' in std:
        process_metric(std)

    return (len(comparisons) > 0), comparisons