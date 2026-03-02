# Análisis del desglose de pagos — Perspectiva contable

**Documento preparado desde el rol de contador y controlador de planillas.**

---

## 1. Estructura actual del desglose

### ASIGNACIONES (2 conceptos)
| Concepto            | Origen                    | Observación              |
|---------------------|---------------------------|--------------------------|
| Salario quincenal   | Cálculo desde salario_mes | Correcto                  |
| Horas Extras        | Registro hrs_extra        | Correcto, con tarifa 1.5x |

### DEDUCCIONES (7 conceptos)
| Concepto               | Origen en registros        | ¿Se usa? |
|------------------------|----------------------------|----------|
| Vales                  | —                          | **No** (siempre 0)         |
| Días de permiso        | hrs_negativas, dia_psg     | Sí       |
| Días de incapacidades | incapacidades              | Sí       |
| Consumo vale efectivo  | vale_efectivo              | Sí       |
| Facturas crédito       | creditos_comida            | Sí       |
| Otros                  | mermas, ccss_rebajos       | Sí       |
| CCSS                   | Automático (% salario)     | Sí       |

---

## 2. Hallazgos principales

### 2.1 Redundancia
- **"Vales"** nunca se llena en la generación: el campo `vale_efectivo` va a "Consumo vale efectivo".
- "Vales" y "Consumo vale efectivo" suelen referirse al mismo concepto: adelanto que se deduce.
- Recomendación: eliminar "Vales" y dejar un solo concepto **"Vale efectivo"**.

### 2.2 Nombres largos
- "Consumo vale efectivo" es redundante.
- "Facturas crédito" podría ser "Créditos comida" (alineado con el campo en registros).

### 2.3 Orden desde el punto de vista contable
En Costa Rica es habitual mostrar primero:
1. CCSS (por normativa).
2. Deducciones del salario (días no laborados, adelantos, etc.).

### 2.4 Mermas como concepto propio
- Mermas van hoy en "Otros".
- Tiene sentido separarlas para trazabilidad y revisión interna.

---

## 3. Propuesta de simplificación

### Opción A — Simplificación leve (6 deducciones)
- Quitar "Vales".
- Renombrar para claridad.

| Nuevo orden | Concepto           | Origen                  |
|-------------|--------------------|--------------------------|
| 1           | CCSS               | Automático               |
| 2           | Días no laborados  | Permiso + Incapacidades |
| 3           | Vale efectivo     | vale_efectivo            |
| 4           | Créditos comida   | creditos_comida         |
| 5           | Mermas             | mermas                  |
| 6           | Otros              | ccss_rebajos y otros    |

### Opción B — Estructura más simple (5 deducciones)
- Unificar "Días de permiso" y "Días de incapacidades" en "Días no laborados".

| Orden | Concepto          | Origen                             |
|-------|-------------------|------------------------------------|
| 1     | CCSS              | Automático                         |
| 2     | Días no laborados | hrs_negativas, dia_psg, incapacidades |
| 3     | Vale efectivo     | vale_efectivo                      |
| 4     | Créditos comida   | creditos_comida                   |
| 5     | Otros             | mermas, ccss_rebajos, misc.       |

### Opción C — Máxima simplificación (4 deducciones)
- Agrupar adelantos en un solo concepto.

| Orden | Concepto          | Origen                             |
|-------|-------------------|------------------------------------|
| 1     | CCSS              | Automático                         |
| 2     | Días no laborados | Permiso + incapacidades            |
| 3     | Adelantos y descuentos | vale + créditos + mermas + otros |
| 4     | (no necesario)    | —                                  |

---

## 4. Recomendación

- **Opción A** equilibra claridad y detalle.
- Beneficios:
  - Elimina "Vales" (no usado).
  - Mermas visibles como concepto.
  - Nombres alineados con los campos del registro.
  - Orden más cercano a la práctica contable en CR.
- Coste: ajustar la generación del desglose y el PDF; no cambia el modelo de datos.

---

## 5. Resumen de cambios propuestos

1. Quitar el concepto "Vales" del desglose.
2. Renombrar:
   - "Consumo vale efectivo" → "Vale efectivo"
   - "Facturas crédito" → "Créditos comida"
3. Crear concepto "Mermas" separado de "Otros".
4. Reordenar deducciones: CCSS primero, luego días no laborados, vale, créditos, mermas, otros.

---

## 6. Cambios aplicados (feb 2026)

Se implementó la **Opción B** (estructura simplificada):

- Eliminado "Vales" (redundante).
- Renombrado: "Consumo vale efectivo" → "Vale efectivo", "Facturas crédito" → "Créditos comida".
- Unificado "Días de permiso" e "Incapacidades" en **"Días no laborados"**.
- Mermas como concepto separado.
- Orden contable: CCSS → Días no laborados → Vale efectivo → Créditos comida → Mermas → Otros.
- Solo se muestran filas con monto > 0 (desglose más limpio).
- Asignaciones: "Salario base" (en lugar de "Salario quincenal" cuando aplique).

## 7. ¿Es necesario modificar desgloses ya generados?

- **No obligatoriamente.** Los desgloses guardados en BD tienen líneas con `concept` y `amount`.
- El PDF mapea conceptos legacy a la nueva estructura (p. ej. "Consumo vale efectivo" → "Vale efectivo").
- Si quieres que desgloses antiguos usen la nueva estructura, habría que:
  - Regenerarlos desde BD (generar de nuevo), o
  - Crear un script de migración que actualice los `concept` de las líneas existentes.

---

## 8. Conclusiones

- El desglose actual es correcto en la lógica de cálculo.
- Se puede simplificar eliminando redundancias y mejorando nombres.
- No se requieren cambios en el modelo de datos.
- Los cambios son en:
  - `routes/payroll.py` (generación del desglose),
  - `utils/payslip_pdf.py` (orden y nombres en el PDF).
