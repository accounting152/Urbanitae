# Urbanitae — seguimiento de inversiones familiares

Datos económicos de las inversiones en Urbanitae (crowdfunding), extraídos del área privada de la web.

## Titulares

| Código | Titular | Última extracción |
|---|---|---|
| `fj` | Francisco Javier | 2026-11-17 |

## Ficheros

- `data/<titular>/inversiones.csv`: una fila por proyecto con importe invertido, capital activo, cobrado, pendiente, total esperado, rentabilidad total, TIR, vencimiento estimado y estado.
- `data/<titular>/pagos.csv`: calendario de pagos, con los cobrados (con fecha) y los previstos (con trimestre).
- `data/<titular>/resumen.json`: totales y rentabilidades ponderadas de la cartera tal como las muestra Urbanitae.
- `data/raw/`: datos tal como vienen de la web.
- `scripts/build_data.py`: genera los ficheros limpios a partir de `data/raw/`.

## Cómo leer los datos

- **Importes brutos.** Los pagos están en bruto, antes de la retención fiscal del 19 % sobre los rendimientos; en *Movimientos* Urbanitae muestra los netos.
- **Total esperado.** Es el total que Urbanitae prevé devolver por proyecto (`totalRefunds`). La rentabilidad total sale de ahí.
- **Vencimiento estimado.** Es el último trimestre previsto en el calendario de Urbanitae. Para calcular, se toma la mitad de ese trimestre.
- **TIR calculada.** Es una aproximación propia a partir de la fecha de inversión, los cobros y el pendiente al vencimiento estimado. La TIR oficial de Urbanitae solo está disponible a nivel de cartera, en `resumen.json`.
- **Columna `nota`.** En algunos proyectos con pagos parciales, el calendario de Urbanitae no reparte todo lo que falta por cobrar. Esta columna señala esas diferencias.

## Actualizar

1. Extraer de nuevo los datos de la web y sustituir los ficheros de `data/raw/`.
2. Ejecutar `python3 scripts/build_data.py fj`.
