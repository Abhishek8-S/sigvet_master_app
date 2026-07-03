import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from core.evaluator import evaluate_result

def draw_footer(c):
    c.saveState()
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.gray)
    c.drawString(50, 40, "Developed by")
    c.setFillColor(colors.black)
    c.drawString(50, 28, "© 2025 Abhishek S | Sigtuple Technologies")
    c.restoreState()

def generate_headless_pdf(all_data, device_name, output_path):
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        c = canvas.Canvas(output_path, pagesize=letter)
        w, h = letter
        y = h - 50
        
        c.setFillColor(colors.HexColor("#3b82f6"))
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, y, "Compute Benchmark Report")
        y -= 25
        
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, f"Device Identifier: {device_name}")
        y -= 20
        
        c.setLineWidth(1)
        c.setStrokeColor(colors.gray)
        c.line(50, y, w-50, y)
        y -= 40
        
        for name, data in all_data.items():
            if y < 150: 
                draw_footer(c)
                c.showPage()
                y = h - 50 
            
            c.setFillColor(colors.HexColor("#1e1e2e"))
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y, name)
            y -= 20
            
            has_bench, comparisons = evaluate_result(name, data)
            
            c.setFillColor(colors.gray)
            c.setFont("Helvetica", 9)
            c.drawString(60, y, "METRIC")
            c.drawString(250, y, "VALUE / (EXPECTED)")
            c.drawString(450, y, "DEVIATION")
            y -= 15
            
            c.setFont("Helvetica", 10)
            if has_bench:
                for comp in comparisons:
                    label = comp['label']
                    val = f"{comp['actual']} (Exp: {comp['expected']})"
                    dev = comp['deviation']
                    
                    c.setFillColor(colors.black)
                    c.drawString(60, y, label)
                    c.drawString(250, y, val)
                    
                    if "FAIL" in dev or "-" in dev: c.setFillColor(colors.red)
                    else: c.setFillColor(colors.green)
                    c.drawString(450, y, dev)
                    
                    y -= 15
            
            c.setFillColor(colors.darkgray)
            c.setFont("Helvetica", 9)
            for k, v in data.items():
                if k not in ['report', 'status', 'report_saved', 'metrics', 'key']:
                    if y < 60: 
                        draw_footer(c)
                        c.showPage()
                        y = h - 50
                    c.drawString(60, y, f"{k}: {v}")
                    y -= 12
            
            y -= 25 

        draw_footer(c)
        c.save()
        return output_path
    except Exception as e:
        print(f"Headless PDF Error: {e}")
        return None
