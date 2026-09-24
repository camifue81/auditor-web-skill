# Guion para la presentación (5 minutos)

1. **Qué es (30 s).** "web-audit es una skill que audita proyectos React/JS y genera un reporte con puntaje, archivo y línea de cada problema."
2. **Estructura (1 min).** Mostrar `web-audit/`: `SKILL.md` (cuándo usarla y pasos), `scripts/audit.py` (motor), `assets/rules.json` (reglas) y `report_template.html` (diseño), `references/reglas.md` (cómo corregir cada problema).
3. **Demo en vivo (2 min).**
   ```powershell
   python demo.py
   start examples\tienda-con-errores\audit-report\reporte.html
   ```
   Mostrar el 22/100 del proyecto con errores, el 100/100 del limpio y los 3 errores controlados (códigos 2, 3 y 4).
   Extra: auditar el repo de clase `python web-audit\scripts\audit.py ..\Practica1` → 83/100, encuentra `cart.push`.
4. **Pruebas (30 s).** `python -m unittest discover -s tests -v` → 16 pruebas OK.
5. **Decisiones (1 min).**
   - Sin dependencias: se instala copiando la carpeta.
   - Reglas en JSON: agregar una regla no requiere programar.
   - Lo complejo (useState, useEffect, .map) en Python, porque una regex no basta.
   - Códigos de salida distintos para que el agente sepa qué hacer ante cada error.
   - El agente confirma la línea antes de corregir (el análisis por patrones puede dar falsos positivos).

**Preguntas probables:**
- *¿Por qué no usar ESLint?* Requiere Node e instalación por proyecto; esta skill funciona con Python solo y además genera un reporte con puntaje y guía de arreglos para el agente.
- *¿Cómo agrego una regla?* Ver `web-audit/references/agregar-reglas.md`.
