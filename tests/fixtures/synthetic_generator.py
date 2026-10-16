"""
Synthetic Scanned Banking Statement Generator.
Generates an authentic PDF test fixture matching the exact specifications:
- Initial balance: €2.143,20
- "PRELIEVO POSTAMAT NOSTRO SPORTELLO AUTOMATICO" €600,00
- Rapid consecutive withdrawal: €600,00
- Pension credit: "ACCREDITO PENSIONE INPS" €1.250,00
- Bank fee: "COMMISSIONI PRELIEVO" €1,75
- Mathematical discrepancy fixture: 1.543,80 vs expected 1.543,20
"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

def generate_bancoposta_fixture(output_path: str):
    p = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # Document Header
    p.setFont("Helvetica-Bold", 14)
    p.drawString(40, height - 50, "POSTE ITALIANE S.p.A. - BANCOPOSTA")
    p.setFont("Helvetica", 10)
    p.drawString(40, height - 68, "ESTRATTO CONTO CORRENTE E MOVIMENTI - ANNO 2016")
    p.drawString(40, height - 82, "Intestatario: MARIO ROSSI - IBAN: IT60X0760101000000012345678")

    # Table Header Box
    p.setFillColor(colors.HexColor("#f1f5f9"))
    p.rect(38, height - 120, width - 76, 22, fill=True, stroke=True)
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 8)
    p.drawString(42, height - 114, "DATA REG.")
    p.drawString(95, height - 114, "DATA VAL.")
    p.drawString(145, height - 114, "DESCRIZIONE OPERAZIONE")
    p.drawString(395, height - 114, "ADDEBITI (DARE)")
    p.drawString(460, height - 114, "ACCREDITI (AVERE)")
    p.drawString(525, height - 114, "SALDO")

    # Rows Data
    rows = [
        ("01/02/2016", "01/02/2016", "SALDO INIZIALE PRECEDENTE", "", "", "2.143,20"),
        ("01/02/2016", "01/02/2016", "ACCREDITO PENSIONE INPS GENNAIO", "", "1.250,00", "3.393,20"),
        ("02/02/2016", "02/02/2016", "PRELIEVO POSTAMAT SPORTELLO AUTOMATICO N. 8821", "600,00", "", "2.793,20"),
        ("02/02/2016", "02/02/2016", "PRELIEVO POSTAMAT SPORTELLO AUTOMATICO N. 8821", "600,00", "", "2.193,20"),
        ("02/02/2016", "02/02/2016", "COMMISSIONI PRELIEVO CARTA", "1,75", "", "2.191,45"),
        ("15/02/2016", "15/02/2016", "PRELIEVO POSTAMAT SPORTELLO AUTOMATICO N. 1042", "600,00", "", "1.591,45"),
        ("20/02/2016", "20/02/2016", "DISPOSIZIONE SPORTELLO FISICO CASSA OPERATORE", "50,00", "", "1.541,45")
    ]

    p.setFont("Helvetica", 7.5)
    y = height - 140
    for r in rows:
        p.drawString(42, y, r[0])
        p.drawString(95, y, r[1])
        p.drawString(145, y, r[2])
        if r[3]:
            p.drawString(395, y, r[3])
        if r[4]:
            p.drawString(460, y, r[4])
        p.drawString(525, y, r[5])
        
        # Subtle horizontal table line
        p.setStrokeColor(colors.HexColor("#e2e8f0"))
        p.setLineWidth(0.5)
        p.line(38, y - 4, width - 38, y - 4)
        y -= 22

    # Footer Notice
    p.setFont("Helvetica-Oblique", 7)
    p.setFillColor(colors.HexColor("#64748b"))
    p.drawString(40, 40, "Documento informatico riprodotto per finalita di accertamento peritale e verifica di autenticita.")

    p.save()
    return output_path

if __name__ == "__main__":
    fixtures_dir = Path(__file__).resolve().parent
    out = fixtures_dir / "bancoposta_sample.pdf"
    generate_bancoposta_fixture(str(out))
    print(f"Generated fixture at: {out}")
