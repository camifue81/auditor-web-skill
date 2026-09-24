"""
Demostración completa de la skill web-audit (para la presentación).

Ejecutar desde la raíz del repositorio:
    python demo.py

Corre 5 escenarios y muestra el código de salida de cada uno:
  1. Caso exitoso con errores detectados   (tienda-con-errores)
  2. Caso exitoso sin errores               (proyecto-limpio)
  3. Error: la carpeta no existe            -> código 2
  4. Error: proyecto sin archivos JS        -> código 3
  5. Error: archivo de reglas corrupto      -> código 4
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUDIT = "web-audit/scripts/audit.py"
EX = "examples"

ESCENARIOS = [
    ("1. Proyecto con errores", [f"{EX}/tienda-con-errores", "--out", f"{EX}/tienda-con-errores/audit-report"]),
    ("2. Proyecto limpio", [f"{EX}/proyecto-limpio", "--out", f"{EX}/proyecto-limpio/audit-report"]),
    ("3. Carpeta inexistente", [f"{EX}/no-existe"]),
    ("4. Proyecto que no es JavaScript", [f"{EX}/proyecto-python"]),
    ("5. Reglas corruptas", [f"{EX}/tienda-con-errores", "--rules", f"{EX}/reglas-rotas.json"]),
]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for titulo, args in ESCENARIOS:
        print("=" * 70)
        print(titulo)
        print("=" * 70)
        proc = subprocess.run([sys.executable, AUDIT, *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        print((proc.stdout + proc.stderr).strip())
        print(f"--> código de salida: {proc.returncode}\n")
    print("Abre examples/tienda-con-errores/audit-report/reporte.html en el navegador para ver el reporte.")


if __name__ == "__main__":
    main()
