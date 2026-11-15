# Test del paso 6: prueba check_routes directamente, sin sockets,
# con las tablas del ejemplo 2 (R1 <-> R2 <-> R3).
import router

IP = "127.0.0.1"

# (archivo de rutas, puerto de destino, resultado esperado)
casos = [
    # R1: todo lo que va a 8882 u 8883 sale por R2
    ("rutas_R1_v2.txt", 8882, (IP, 8882)),
    ("rutas_R1_v2.txt", 8883, (IP, 8882)),
    ("rutas_R1_v2.txt", 8884, None),

    # R2: 8881 sale por R1, 8883 sale por R3
    ("rutas_R2_v2.txt", 8881, (IP, 8881)),
    ("rutas_R2_v2.txt", 8883, (IP, 8883)),
    ("rutas_R2_v2.txt", 8884, None),

    # R3: todo lo que va a 8881 u 8882 sale por R2
    ("rutas_R3_v2.txt", 8881, (IP, 8882)),
    ("rutas_R3_v2.txt", 8882, (IP, 8882)),
    ("rutas_R3_v2.txt", 8884, None),
]

# Tablas de borde, creadas en archivos temporales:
#  - sin salto de línea al final: la última ruta no se debe perder
#  - con una línea en blanco en medio: no se debe caer
#  - rango con el destino en medio (no en un extremo)
import os
import tempfile

tablas_borde = {
    "sin_salto": "127.0.0.1/24 8881 8881 127.0.0.1 8881\n127.0.0.1/24 8883 8883 127.0.0.1 8883",
    "linea_vacia": "127.0.0.1/24 8881 8881 127.0.0.1 8881\n\n   \n127.0.0.1/24 8883 8883 127.0.0.1 8883\n",
    "rango_medio": "127.0.0.1/24 8881 8885 127.0.0.1 8882\n",
}
tmp_dir = tempfile.mkdtemp()
rutas_borde = {}
for nombre, contenido in tablas_borde.items():
    ruta = os.path.join(tmp_dir, f"rutas_{nombre}.txt")
    with open(ruta, "w") as f:
        f.write(contenido)
    rutas_borde[nombre] = ruta

casos += [
    (rutas_borde["sin_salto"], 8883, (IP, 8883)),
    (rutas_borde["linea_vacia"], 8883, (IP, 8883)),
    (rutas_borde["rango_medio"], 8883, (IP, 8882)),
    (rutas_borde["rango_medio"], 8886, None),
]

ok = 0
for archivo, puerto, esperado in casos:
    try:
        # check_routes ahora es un método: se crea un Router nuevo por caso
        # (puerto propio irrelevante, no se abre socket) para que el estado
        # del round-robin de un caso no afecte al siguiente.
        obtenido = router.Router(IP, 0, archivo).check_routes(archivo, (IP, puerto))
    except Exception as e:
        obtenido = f"ERROR {type(e).__name__}: {e}"

    paso = obtenido == esperado
    ok += paso
    marca = "OK   " if paso else "FALLA"
    print(f"[{marca}] {archivo} destino {puerto} -> esperado {esperado}, obtenido {obtenido}")

print(f"\n{ok}/{len(casos)} casos correctos")
