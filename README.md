# Urbanitae — seguimiento de inversiones familiares

App web (instalable en el móvil) con las inversiones en Urbanitae: importes, rentabilidad, vencimientos y calendario de pagos.

**Abrir:** https://accounting152.github.io/Urbanitae/

La app lee `data.enc.json`, cifrado con AES-256-GCM y una clave derivada de la contraseña (PBKDF2-SHA256).

### Instalar en el móvil
- **iPhone (Safari):** abrir el enlace → botón Compartir → *Añadir a pantalla de inicio*.
- **Android (Chrome):** abrir el enlace → menú ⋮ → *Instalar aplicación* o *Añadir a pantalla de inicio*.

La primera vez pide la contraseña; con "Recordar en este dispositivo" no la vuelve a pedir.

Datos económicos de las inversiones en Urbanitae (crowdfunding), extraídos del área privada de la web.

## Titulares

| Código | Titular | Última extracción |
|---|---|---|
| `fj` | Yo | 2026-11-17 |
| `padre` | Padre | 2026-11-17 |

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
2. Ejecutar `python3 scripts/build_data.py fj padre`.
3. Ejecutar `python3 scripts/encrypt_data.py` (pide la contraseña) para regenerar `data.enc.json`.

## Panel en Claude

Versión del panel dentro de Claude, con cuatro informes (Resumen, Inversiones, Calendario de pagos y Tabla por trimestres): https://claude.ai/artifact/RpgGPVLR2bEVossdeihYT2

El código de la página está en `dashboard/index.html`. Lee `data/<titular>/inversiones.csv` y `data/<titular>/pagos.csv`.
