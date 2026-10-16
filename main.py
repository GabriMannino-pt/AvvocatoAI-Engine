import sys
import argparse
import subprocess
from pathlib import Path
import uvicorn

# Ensure UTF-8 stdout/stderr on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from core.forensic_pipeline import ForensicPipeline
from core.config import settings

def run_analyze(pdf_path: str, initial_balance: float = None, authorized: float = None):
    print(f"\n=======================================================")
    print(f"⚖️ AVVOCATO_AI — ESECUZIONE PIPELINE FORENSE MULTI-STADIO")
    print(f"=======================================================")
    print(f"Documento: {pdf_path}")
    if initial_balance is not None:
        print(f"Saldo Iniziale Noto: €{initial_balance:.2f}")
    if authorized is not None:
        print(f"Plafond Autorizzato: €{authorized:.2f}")
        
    pipeline = ForensicPipeline()
    case = pipeline.process_pdf(
        pdf_path=pdf_path,
        initial_balance=initial_balance,
        authorized_spending=authorized
    )
    
    print(f"\n[+] Analisi completata con successo:")
    print(f"    - Movimenti estratti: {len(case.transactions)}")
    print(f"    - Anomalie & pattern rilevati: {len(case.anomalies)}")
    print(f"    - Ipotesi giuridiche formulate: {len(case.legal_hypotheses)}")
    print(f"    - Richieste documentali generate: {len(case.document_requests)}")
    print(f"    - Riconciliazione matematica: {'CONFERMATA' if (case.summary and case.summary.is_mathematically_reconciled) else 'DISCREPANZA SEGNALATA'}")
    
    report_file = pipeline.output_dir / f"{Path(pdf_path).stem}_perizia_forense.md"
    print(f"\n[+] Relazione peritale forense in 20 sezioni salvata in:")
    print(f"    {report_file}")
    print(f"=======================================================\n")

def run_benchmark():
    print(f"\n=======================================================")
    print(f"📊 AVVOCATO_AI — ESECUZIONE BENCHMARK INTERNO E TEST")
    print(f"=======================================================\n")
    venv_pytest = Path(__file__).resolve().parent / ".venv" / "Scripts" / "pytest.exe"
    cmd = [str(venv_pytest), "-v", "tests/"]
    subprocess.run(cmd)

def run_server(host: str = "127.0.0.1", port: int = 8000):
    print(f"\n=======================================================")
    print(f"🌐 AVVOCATO_AI — AVVIO DASHBOARD FORENSE WEB")
    print(f"=======================================================")
    print(f"Interfaccia attiva su: http://{host}:{port}")
    print(f"Visualizzatore split-screen, bounding box reticle e audit trail pronti.")
    print(f"=======================================================\n")
    uvicorn.run("server.app:app", host=host, port=port, reload=False)

def main():
    parser = argparse.ArgumentParser(description="AVVOCATO_AI — OCR Forense Bancario & Legal Intelligence")
    subparsers = parser.add_subparsers(dest="command")

    # Analyze
    p_analyze = subparsers.add_parser("analyze", help="Analizza un PDF bancario")
    p_analyze.add_argument("pdf_path", help="Percorso del file PDF")
    p_analyze.add_argument("--initial-balance", type=float, default=None, help="Saldo contabile iniziale noto")
    p_analyze.add_argument("--authorized", type=float, default=None, help="Importo massimo autorizzato per operazione")

    # Benchmark
    subparsers.add_parser("benchmark", help="Esegue la suite di test e il benchmark")

    # Serve
    p_serve = subparsers.add_parser("serve", help="Avvia il server e la dashboard web")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()
    if args.command == "analyze":
        run_analyze(args.pdf_path, initial_balance=args.initial_balance, authorized=args.authorized)
    elif args.command == "benchmark":
        run_benchmark()
    elif args.command == "serve":
        run_server(host=args.host, port=args.port)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
