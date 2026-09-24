"""
Pruebas de la skill web-audit (solo biblioteca estándar).

Ejecutar desde la raíz del repositorio:
    python -m unittest discover -s tests -v
"""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "web-audit" / "scripts"))

import audit  # noqa: E402

EXAMPLES = REPO / "examples"


def write_project(tmp, files):
    for name, content in files.items():
        path = Path(tmp) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return tmp


def run_main(args):
    """Ejecuta audit.main sin ensuciar la salida de las pruebas."""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return audit.main(args)


def rules_found(result):
    return {f["rule"] for f in result["findings"]}


class CasosExitosos(unittest.TestCase):
    def test_tienda_con_errores_detecta_problemas(self):
        result = audit.run_audit(EXAMPLES / "tienda-con-errores")
        self.assertEqual(len(result["files_scanned"]), 4)
        esperadas = {
            "mutacion-estado", "debugger", "secreto-en-codigo", "effect-sin-deps",
            "fetch-sin-errores", "igualdad-debil", "map-sin-key", "inner-html",
            "url-http", "console-log", "alert", "var", "todo",
        }
        self.assertTrue(esperadas.issubset(rules_found(result)), rules_found(result))
        self.assertLess(result["score"], 50)
        self.assertEqual(result["grade"], "Crítico")

    def test_proyecto_limpio_tiene_100(self):
        result = audit.run_audit(EXAMPLES / "proyecto-limpio")
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["score"], 100)

    def test_genera_html_y_json(self):
        with tempfile.TemporaryDirectory() as out:
            code = run_main([str(EXAMPLES / "tienda-con-errores"), "--out", out])
            self.assertEqual(code, 0)
            html = (Path(out) / "reporte.html").read_text(encoding="utf-8")
            data = json.loads((Path(out) / "reporte.json").read_text(encoding="utf-8"))
            self.assertIn("tienda-con-errores", html)
            # Todos los marcadores {{MAYUSCULAS}} de la plantilla fueron reemplazados
            self.assertNotRegex(html, r"\{\{[A-Z_]+\}\}")
            self.assertEqual(data["project"], "tienda-con-errores")

    def test_fail_on_devuelve_1(self):
        with tempfile.TemporaryDirectory() as out:
            code = run_main([str(EXAMPLES / "tienda-con-errores"), "--out", out, "--fail-on", "alta"])
            self.assertEqual(code, 1)

    def test_fail_on_proyecto_limpio_devuelve_0(self):
        with tempfile.TemporaryDirectory() as out:
            code = run_main([str(EXAMPLES / "proyecto-limpio"), "--out", out, "--fail-on", "baja"])
            self.assertEqual(code, 0)


class ReglasEspeciales(unittest.TestCase):
    def test_mutacion_de_estado(self):
        text = "const [items, setItems] = useState([])\nitems.push(1)\nitems[0] = 2\nconst otra = []\notra.push(1)\n"
        lines = [l for l, _ in audit.check_state_mutation(text)]
        self.assertEqual(sorted(lines), [2, 3])  # 'otra' no es estado

    def test_effect_con_y_sin_dependencias(self):
        self.assertEqual(len(audit.check_effect_without_deps("useEffect(() => { load() })")), 1)
        self.assertEqual(audit.check_effect_without_deps("useEffect(() => { load() }, [])"), [])
        self.assertEqual(audit.check_effect_without_deps("useEffect(() => { f(a) }, [a, b])"), [])

    def test_map_con_y_sin_key(self):
        self.assertEqual(len(audit.check_map_without_key("{xs.map(x => <li>{x}</li>)}")), 1)
        self.assertEqual(audit.check_map_without_key("{xs.map(x => <li key={x}>{x}</li>)}"), [])

    def test_fetch_con_catch_no_se_marca(self):
        self.assertEqual(audit.check_fetch_without_errors("fetch(u).then(r => r.json()).catch(e => e)"), [])
        self.assertEqual(len(audit.check_fetch_without_errors("fetch(u).then(r => r.json())")), 1)

    def test_ignora_node_modules(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_project(tmp, {
                "src/a.js": "const x = 1\n",
                "node_modules/lib/index.js": "debugger\n",
            })
            result = audit.run_audit(tmp)
            self.assertEqual(result["files_scanned"], ["src/a.js"])
            self.assertEqual(result["findings"], [])


class ManejoDeErrores(unittest.TestCase):
    def test_ruta_inexistente_codigo_2(self):
        self.assertEqual(run_main(["carpeta/que/no/existe"]), 2)

    def test_ruta_es_archivo_codigo_2(self):
        self.assertEqual(run_main([str(REPO / "README.md")]), 2)

    def test_sin_archivos_js_codigo_3(self):
        self.assertEqual(run_main([str(EXAMPLES / "proyecto-python")]), 3)

    def test_reglas_json_roto_codigo_4(self):
        code = run_main([str(EXAMPLES / "tienda-con-errores"), "--rules", str(EXAMPLES / "reglas-rotas.json")])
        self.assertEqual(code, 4)

    def test_regla_con_severidad_invalida(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "r.json"
            bad.write_text(json.dumps({
                "extensions": [".js"], "penalties": {},
                "rules": [{"id": "x", "type": "regex", "pattern": "a", "severity": "urgente"}],
            }), encoding="utf-8")
            with self.assertRaises(audit.AuditError) as ctx:
                audit.load_rules(bad)
            self.assertEqual(ctx.exception.code, 4)

    def test_archivo_latin1_no_rompe(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "viejo.js").write_bytes("// comentario con ñ\nvar a = 1\n".encode("latin-1"))
            result = audit.run_audit(tmp)
            self.assertIn("var", rules_found(result))


if __name__ == "__main__":
    unittest.main(verbosity=2)
