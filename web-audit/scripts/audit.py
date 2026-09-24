#!/usr/bin/env python3
"""
web-audit: auditor estático para proyectos JavaScript / React.

Uso:
    python audit.py <carpeta_del_proyecto> [--out carpeta_salida] [--fail-on alta|media|baja]

Lee las reglas de ../assets/rules.json, analiza los archivos .js/.jsx/.ts/.tsx
y genera:
    - reporte.html  (a partir de ../assets/report_template.html)
    - reporte.json  (datos estructurados, útil para otras herramientas)

Códigos de salida:
    0  auditoría completada (y sin hallazgos del nivel indicado en --fail-on)
    1  auditoría completada, pero hay hallazgos >= --fail-on
    2  la ruta del proyecto no existe o no es una carpeta
    3  no se encontraron archivos JavaScript/React para analizar
    4  el archivo de reglas no existe o es inválido

Solo usa la biblioteca estándar de Python (3.8+).
"""

import argparse
import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_RULES = SKILL_DIR / "assets" / "rules.json"
TEMPLATE = SKILL_DIR / "assets" / "report_template.html"
SEVERITY_ORDER = {"alta": 3, "media": 2, "baja": 1}


class AuditError(Exception):
    """Error controlado: se muestra al usuario con un código de salida."""

    def __init__(self, message, code):
        super().__init__(message)
        self.code = code


# --------------------------------------------------------------------------- #
# Carga de reglas y archivos
# --------------------------------------------------------------------------- #
def load_rules(path):
    path = Path(path)
    if not path.is_file():
        raise AuditError(f"No existe el archivo de reglas: {path}", 4)
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AuditError(
            f"El archivo de reglas no es JSON válido ({path.name}, línea {exc.lineno}): {exc.msg}", 4
        )
    for key in ("extensions", "rules", "penalties"):
        if key not in config:
            raise AuditError(f"Al archivo de reglas le falta la clave obligatoria '{key}'", 4)
    for rule in config["rules"]:
        if rule.get("severity") not in SEVERITY_ORDER:
            raise AuditError(f"Regla '{rule.get('id')}' tiene una severidad inválida", 4)
        if rule.get("type") == "regex":
            try:
                rule["_compiled"] = re.compile(rule["pattern"])
            except (re.error, KeyError) as exc:
                raise AuditError(f"Regla '{rule.get('id')}' tiene un patrón inválido: {exc}", 4)
    return config


def collect_files(root, config, warnings):
    exts = set(config["extensions"])
    ignore = set(config.get("ignore_dirs", []))
    max_bytes = config.get("max_file_kb", 500) * 1024
    files = []
    for path in sorted(root.rglob("*")):
        if any(part in ignore for part in path.relative_to(root).parts):
            continue
        if path.is_file() and path.suffix in exts:
            if path.stat().st_size > max_bytes:
                warnings.append(f"Omitido por tamaño (> {config.get('max_file_kb', 500)} KB): {path.relative_to(root)}")
                continue
            files.append(path)
    return files


def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


# --------------------------------------------------------------------------- #
# Chequeos especiales (más que una expresión regular)
# --------------------------------------------------------------------------- #
def line_of(text, index):
    return text.count("\n", 0, index) + 1


def match_paren(text, open_index):
    """Devuelve el índice del paréntesis que cierra el abierto en open_index."""
    depth = 0
    quote = None
    i = open_index
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "'\"`":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def check_state_mutation(text):
    names = re.findall(r"const\s*\[\s*(\w+)\s*,\s*set\w+\s*\]\s*=\s*useState", text)
    hits = []
    for name in set(names):
        pattern = re.compile(
            rf"\b{name}\.(push|pop|shift|unshift|splice|sort|reverse)\s*\("
            rf"|\b{name}(\[[^\]]+\]|\.\w+)\s*=(?!=)"
        )
        for m in pattern.finditer(text):
            hits.append((line_of(text, m.start()), f"Variable de estado '{name}'"))
    return hits


def check_map_without_key(text):
    hits = []
    for m in re.finditer(r"\.map\s*\(", text):
        end = match_paren(text, m.end() - 1)
        body = text[m.end(): end if end != -1 else m.end() + 400]
        first_tag = re.search(r"<([A-Za-z][\w.]*)([^>]*)>", body, re.S)
        if first_tag and "key=" not in first_tag.group(2):
            hits.append((line_of(text, m.start()), f"Elemento <{first_tag.group(1)}> sin key"))
    return hits


def check_effect_without_deps(text):
    hits = []
    for m in re.finditer(r"\buseEffect\s*\(", text):
        end = match_paren(text, m.end() - 1)
        if end == -1:
            continue
        inside = text[m.end():end].rstrip().rstrip(",").rstrip()
        if not inside.endswith("]"):
            hits.append((line_of(text, m.start()), ""))
    return hits


def check_fetch_without_errors(text):
    m = re.search(r"\bfetch\s*\(", text)
    if not m:
        return []
    handled = re.search(r"\.catch\s*\(|\btry\s*\{|\.ok\b", text)
    return [] if handled else [(line_of(text, m.start()), "")]


CHECKS = {
    "mutacion-estado": check_state_mutation,
    "map-sin-key": check_map_without_key,
    "effect-sin-deps": check_effect_without_deps,
    "fetch-sin-errores": check_fetch_without_errors,
}


# --------------------------------------------------------------------------- #
# Auditoría
# --------------------------------------------------------------------------- #
def audit_file(path, root, rules):
    text = read_text(path)
    lines = text.splitlines()
    rel = path.relative_to(root).as_posix()
    findings = []

    def add(rule, line_no, extra=""):
        snippet = lines[line_no - 1].strip() if 0 < line_no <= len(lines) else ""
        findings.append({
            "rule": rule["id"],
            "severity": rule["severity"],
            "category": rule["category"],
            "message": rule["message"] + (f" ({extra})" if extra else ""),
            "file": rel,
            "line": line_no,
            "code": snippet[:160],
        })

    for rule in rules:
        if rule["type"] == "regex":
            for number, line in enumerate(lines, start=1):
                if rule["_compiled"].search(line):
                    add(rule, number)
        elif rule["type"] == "check" and rule["id"] in CHECKS:
            for line_no, extra in CHECKS[rule["id"]](text):
                add(rule, line_no, extra)
    return findings


def score_for(findings, penalties):
    penalty = sum(penalties.get(f["severity"], 0) for f in findings)
    score = max(0, 100 - penalty)
    if score >= 90:
        grade = "Excelente"
    elif score >= 70:
        grade = "Aceptable"
    elif score >= 50:
        grade = "Necesita mejoras"
    else:
        grade = "Crítico"
    return score, grade


def run_audit(project, rules_path=DEFAULT_RULES):
    root = Path(project).resolve()
    if not root.exists():
        raise AuditError(f"La ruta no existe: {project}", 2)
    if not root.is_dir():
        raise AuditError(f"La ruta debe ser una carpeta de proyecto, no un archivo: {project}", 2)

    config = load_rules(rules_path)
    warnings = []
    files = collect_files(root, config, warnings)
    if not files:
        raise AuditError(
            f"No se encontraron archivos {', '.join(config['extensions'])} en {project} "
            f"(se ignoran: {', '.join(config.get('ignore_dirs', []))})", 3
        )

    findings = []
    for path in files:
        findings.extend(audit_file(path, root, config["rules"]))
    findings.sort(key=lambda f: (-SEVERITY_ORDER[f["severity"]], f["file"], f["line"]))

    score, grade = score_for(findings, config["penalties"])
    counts = {sev: sum(1 for f in findings if f["severity"] == sev) for sev in SEVERITY_ORDER}
    return {
        "project": root.name,
        "path": str(root),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "files_scanned": [p.relative_to(root).as_posix() for p in files],
        "score": score,
        "grade": grade,
        "counts": counts,
        "warnings": warnings,
        "findings": findings,
    }


# --------------------------------------------------------------------------- #
# Salidas
# --------------------------------------------------------------------------- #
def render_html(result):
    if not TEMPLATE.is_file():
        raise AuditError(f"No se encontró la plantilla: {TEMPLATE}", 4)
    template = TEMPLATE.read_text(encoding="utf-8")

    rows = []
    for f in result["findings"]:
        rows.append(
            f'<tr class="sev-{f["severity"]}">'
            f'<td><span class="badge {f["severity"]}">{f["severity"]}</span></td>'
            f'<td>{html.escape(f["category"])}</td>'
            f'<td><code>{html.escape(f["file"])}:{f["line"]}</code></td>'
            f'<td>{html.escape(f["message"])}<pre>{html.escape(f["code"])}</pre></td>'
            f'<td><code>{f["rule"]}</code></td></tr>'
        )
    if not rows:
        rows.append('<tr><td colspan="5" class="empty">No se encontraron problemas. ¡Buen trabajo!</td></tr>')

    warnings = "".join(f"<li>{html.escape(w)}</li>" for w in result["warnings"])
    if result["score"] >= 90:
        score_class = "good"
    elif result["score"] >= 70:
        score_class = "ok"
    else:
        score_class = "bad"

    values = {
        "{{PROJECT}}": html.escape(result["project"]),
        "{{DATE}}": result["date"],
        "{{SCORE}}": str(result["score"]),
        "{{SCORE_CLASS}}": score_class,
        "{{GRADE}}": result["grade"],
        "{{FILES}}": str(len(result["files_scanned"])),
        "{{TOTAL}}": str(len(result["findings"])),
        "{{ALTA}}": str(result["counts"]["alta"]),
        "{{MEDIA}}": str(result["counts"]["media"]),
        "{{BAJA}}": str(result["counts"]["baja"]),
        "{{ROWS}}": "\n".join(rows),
        "{{WARNINGS}}": f"<ul class='warnings'>{warnings}</ul>" if warnings else "",
    }
    # Reemplazo en una sola pasada: el código del usuario nunca se reinterpreta como marcador.
    return re.sub(r"\{\{[A-Z_]+\}\}", lambda m: values.get(m.group(0), m.group(0)), template)


def pretty(path):
    """Muestra la ruta relativa a la carpeta actual si es posible (más legible)."""
    try:
        return Path(path).resolve().relative_to(Path.cwd()).as_posix()
    except ValueError:
        return str(path)


def print_summary(result, out_dir):
    print(f"Proyecto auditado : {result['project']}")
    print(f"Archivos revisados: {len(result['files_scanned'])}")
    print(f"Puntaje           : {result['score']}/100 ({result['grade']})")
    c = result["counts"]
    print(f"Hallazgos         : {len(result['findings'])} (alta: {c['alta']}, media: {c['media']}, baja: {c['baja']})")
    for w in result["warnings"]:
        print(f"AVISO: {w}")
    if result["findings"]:
        print("\nPrincipales hallazgos:")
        for f in result["findings"][:10]:
            print(f"  [{f['severity'].upper():5}] {f['file']}:{f['line']}  {f['rule']}")
        if len(result["findings"]) > 10:
            print(f"  ... y {len(result['findings']) - 10} más (ver reporte)")
    print(f"\nReporte HTML: {pretty(out_dir / 'reporte.html')}")
    print(f"Reporte JSON: {pretty(out_dir / 'reporte.json')}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Audita un proyecto JavaScript/React y genera un reporte.")
    parser.add_argument("project", help="Carpeta del proyecto a auditar")
    parser.add_argument("--out", default="audit-report", help="Carpeta de salida (por defecto: audit-report)")
    parser.add_argument("--rules", default=str(DEFAULT_RULES), help="Archivo de reglas JSON alternativo")
    parser.add_argument("--fail-on", choices=list(SEVERITY_ORDER), help="Devuelve código 1 si hay hallazgos de este nivel o superior")
    args = parser.parse_args(argv)

    # Consola de Windows: forzar UTF-8 para que las tildes se vean bien.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    try:
        result = run_audit(args.project, args.rules)
        out_dir = Path(args.out).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "reporte.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        (out_dir / "reporte.html").write_text(render_html(result), encoding="utf-8")
    except AuditError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return exc.code

    print_summary(result, out_dir)
    if args.fail_on:
        limit = SEVERITY_ORDER[args.fail_on]
        if any(SEVERITY_ORDER[f["severity"]] >= limit for f in result["findings"]):
            print(f"\nResultado: FALLA (hay hallazgos de nivel '{args.fail_on}' o superior)")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
