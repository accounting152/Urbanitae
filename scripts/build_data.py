"""Genera los CSV/JSON limpios a partir de los datos extraídos de Urbanitae.

Entrada:  data/raw/inversiones_<titular>.tsv, data/raw/calendario_<titular>.json
Salida:   data/<titular>/inversiones.csv, data/<titular>/pagos.csv, data/<titular>/resumen.json
"""
import csv, json, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELO = {"LENDING": "Préstamo", "SOLD": "Plusvalía", "RENT": "Rentas"}
FASE = {"FORMALIZED": "En curso", "CLOSED": "Cerrado", "CANCELED": "Cancelado"}
Q_MID = {"Q1": (2, 15), "Q2": (5, 15), "Q3": (8, 15), "Q4": (11, 15)}


def num(v):
    return float(v) if v not in ("", None) else None


def xirr(flows):
    """flows: [(date, amount)] — TIR anual por bisección."""
    if not flows or all(a <= 0 for _, a in flows) or all(a >= 0 for _, a in flows):
        return None
    t0 = min(d for d, _ in flows)
    f = lambda r: sum(a / (1 + r) ** ((d - t0).days / 365) for d, a in flows)
    lo, hi = -0.99, 5.0
    if f(lo) * f(hi) > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return round(mid * 100, 2)


def build(titular):
    raw = ROOT / "data" / "raw"
    inv = list(csv.DictReader(open(raw / f"inversiones_{titular}.tsv", encoding="utf-8"), delimiter="\t"))
    cal = json.load(open(raw / f"calendario_{titular}.json", encoding="utf-8"))
    pagos = []
    for pid, pdate, q, y, amt, done in cal["paymentPeriods"]:
        m, d = Q_MID[q]
        pagos.append({
            "id": pid, "estado": "cobrado" if done else "previsto",
            "fecha": pdate or "", "trimestre": f"{y}-{q}",
            "fecha_estimada": pdate or date(int(y), m, d).isoformat(),
            "importe_bruto": amt,
        })
    names = {r["id"]: r["nombre"] for r in inv}
    total_ref = cal["totalRefunds"]

    out = []
    for r in inv:
        pid, imp = r["id"], float(r["importe"])
        mis = [p for p in pagos if p["id"] == pid]
        cobrado = round(sum(p["importe_bruto"] for p in mis if p["estado"] == "cobrado"), 2)
        pendiente = round(sum(p["importe_bruto"] for p in mis if p["estado"] == "previsto"), 2)
        prev = [p for p in mis if p["estado"] == "previsto"]
        venc = max((p["fecha_estimada"] for p in prev), default="")
        venc_q = max((p["trimestre"] for p in prev), default="")
        if r["fase"] in ("CLOSED", "CANCELED"):
            devuelto = num(r["devuelto"]) or cobrado
            total_esperado = devuelto
        else:
            total_esperado = total_ref.get(pid, round(cobrado + pendiente, 2))
        # Flujos para la TIR: lo ya cobrado en su fecha y lo que falta hasta el total
        # esperado por Urbanitae, al vencimiento estimado.
        flows = [(date.fromisoformat(r["fecha_inversion"]), -imp)]
        flows += [(date.fromisoformat(p["fecha_estimada"][:10]), p["importe_bruto"])
                  for p in mis if p["estado"] == "cobrado"]
        falta = round(total_esperado - cobrado, 2)
        nota = ""
        if r["fase"] not in ("CLOSED", "CANCELED"):
            if falta > 0 and venc:
                flows.append((date.fromisoformat(venc[:10]), falta))
            if abs(falta - pendiente) > 1:
                nota = (f"El calendario muestra {pendiente:.2f} € pendientes; para llegar al total "
                        f"esperado faltan {falta:.2f} €")
        ultimo = max((p["fecha_estimada"][:10] for p in mis), default="")
        activo = num(r["activo"])
        if activo is None:
            activo = 0.0 if r["fase"] in ("CLOSED", "CANCELED") else imp
        out.append({
            "titular": titular, "id": pid, "proyecto": r["nombre"],
            "url": f"https://urbanitae.com/es/menuPrivado/proyecto/{pid}/",
            "modelo": MODELO.get(r["modelo"], r["modelo"]), "estado": FASE.get(r["fase"], r["fase"]),
            "promotor": r["promotor"], "fecha_inversion": r["fecha_inversion"],
            "fecha_financiado": r["fecha_financiado"],
            "importe_invertido": imp, "capital_activo": activo,
            "cobrado_bruto": cobrado, "pendiente_calendario_bruto": pendiente,
            "pendiente_hasta_total_bruto": max(falta, 0) if r["fase"] == "FORMALIZED" else 0,
            "total_esperado_bruto": total_esperado,
            "beneficio_esperado": round(total_esperado - imp, 2),
            "rentabilidad_total_pct": round((total_esperado / imp - 1) * 100, 2),
            "tir_calculada_pct": xirr(flows),
            "tir_objetivo_pct": num(r["target_irr"]), "tir_real_pct": num(r["actual_irr"]),
            "plazo_objetivo_meses": num(r["plazo_obj_meses"]), "plazo_real_meses": num(r["plazo_real_meses"]),
            "vencimiento_trimestre": venc_q, "vencimiento_estimado": venc[:10],
            "ultimo_pago": ultimo, "participacion_pct": num(r["participacion_pct"]),
            "nota": nota,
        })

    dest = ROOT / "data" / titular
    dest.mkdir(parents=True, exist_ok=True)
    with open(dest / "inversiones.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader(); w.writerows(out)
    with open(dest / "pagos.csv", "w", newline="", encoding="utf-8") as f:
        rows = [{"titular": titular, "proyecto": names.get(p["id"], p["id"]), **p} for p in pagos]
        rows.sort(key=lambda p: p["fecha_estimada"])
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    resumen = dict(cal["resumen_cartera"])
    resumen.update({
        "titular": titular, "n_inversiones": len(out),
        "n_en_curso": sum(o["estado"] == "En curso" for o in out),
        "capital_activo": round(sum(o["capital_activo"] for o in out), 2),
        "cobrado_bruto": round(sum(p["importe_bruto"] for p in pagos if p["estado"] == "cobrado"), 2),
        "pendiente_bruto": round(sum(p["importe_bruto"] for p in pagos if p["estado"] == "previsto"), 2),
    })
    json.dump(resumen, open(dest / "resumen.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return out, pagos, resumen


if __name__ == "__main__":
    for t in sys.argv[1:] or ["fj"]:
        o, p, r = build(t)
        print(json.dumps(r, ensure_ascii=False, indent=1))
