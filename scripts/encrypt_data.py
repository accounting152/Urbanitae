"""Empaqueta los datos de todos los titulares en data.enc.json, cifrado con contraseña.

Uso:  URB_PW='la-contraseña' python3 scripts/encrypt_data.py
      (o sin URB_PW: la pide por teclado)

Formato igual que el panel de Engineered Now:
AES-256-GCM, clave PBKDF2-SHA256 (310.000 iteraciones), contenido JSON comprimido con gzip.
"""
import base64, csv, getpass, gzip, json, os
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ROOT = Path(__file__).resolve().parent.parent
ITER = 310_000
TITULARES = {"fj": "Yo", "padre": "Padre", "madre": "Madre"}
NUM = {"importe_invertido", "capital_activo", "cobrado_bruto", "pendiente_calendario_bruto",
       "pendiente_hasta_total_bruto", "total_esperado_bruto", "beneficio_esperado",
       "rentabilidad_total_pct", "tir_calculada_pct", "tir_objetivo_pct", "tir_real_pct",
       "plazo_objetivo_meses", "plazo_real_meses", "meses_hasta_vencimiento",
       "participacion_pct", "importe_bruto"}


def rows(path):
    out = []
    for r in csv.DictReader(open(path, encoding="utf-8")):
        out.append({k: (float(v) if k in NUM and v not in ("", None) else (None if v == "" else v))
                    for k, v in r.items()})
    return out


def payload():
    data = {"generado": datetime.now(timezone.utc).isoformat(timespec="minutes"),
            "titulares": {}, "inversiones": [], "pagos": [], "resumen": {}}
    for d in sorted((ROOT / "data").iterdir()):
        if d.name == "raw" or not (d / "inversiones.csv").exists():
            continue
        data["titulares"][d.name] = TITULARES.get(d.name, d.name)
        data["inversiones"] += rows(d / "inversiones.csv")
        data["pagos"] += rows(d / "pagos.csv")
        if (d / "resumen.json").exists():
            data["resumen"][d.name] = json.load(open(d / "resumen.json", encoding="utf-8"))
    return data


def main():
    pw = os.environ.get("URB_PW") or getpass.getpass("Contraseña: ")
    plain = gzip.compress(json.dumps(payload(), ensure_ascii=False).encode("utf-8"))
    salt, iv = os.urandom(16), os.urandom(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(pw.encode("utf-8"))
    ct = AESGCM(key).encrypt(iv, plain, None)
    b = lambda x: base64.b64encode(x).decode()
    pkg = {"v": 1, "z": 1, "kdf": "PBKDF2-SHA256", "iter": ITER, "salt": b(salt), "iv": b(iv), "data": b(ct)}
    (ROOT / "data.enc.json").write_text(json.dumps(pkg), encoding="utf-8")
    print("data.enc.json escrito,", len(pkg["data"]), "caracteres cifrados")


if __name__ == "__main__":
    main()
