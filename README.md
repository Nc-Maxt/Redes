# Redes

Tareas del curso de Redes (CC4303). Todo está hecho en Python con la librería `socket`.

## Qué hay en cada carpeta


| Carpeta                        | Qué es                                                                |
| ------------------------------ | --------------------------------------------------------------------- |
| `orientados_Socket/`           | Cliente y servidor con TCP (orientado a conexión). Ejemplo básico.    |
| `No_orientados_Sockets (ex1)/` | Cliente y servidor con UDP (no orientado a conexión). Ejemplo básico. |
| `Ejercicio_1/`                 | Servidor HTTP y proxy HTTP.                                           |
| `Ejercicio_2/`                 | Resolver DNS.                                                         |
| `Ejercicio_3/`                 | TCP simplificado sobre UDP con Stop & Wait.                           |
| `Ejercicio_4/`                 | Go-Back-N y control de congestión (TCP Tahoe simplificado).           |
| `Ejercicio_5/`                 | Forwarding básico con Round Robin y TTL en los paquetes.              |
| `Ejercicio_6/`                 | Fragmentación usando como base el código del ejercicio anterior.      |


## Ejemplos básicos de sockets

Sirven para ver la diferencia entre TCP y UDP. Se usan en dos terminales: primero el servidor, después el cliente.

```bash
# terminal 1
python3 servidor.py

# terminal 2
python3 cliente.py
```

El cliente pide que escribas un mensaje y lo manda al servidor. Ambos usan `localhost:5000`.

## Ejercicio 1: servidor HTTP y proxy



### `protocolos.py`

Tiene las funciones que arman y desarman mensajes HTTP:

- `parse_HTTP_message(bytes)` toma un mensaje HTTP y lo convierte en un diccionario.
- `create_HTTP_message(dict)` hace lo contrario: toma el diccionario y arma el mensaje en bytes.



### `servidor_HTTP_1.py`

Servidor HTTP simple. Escucha, recibe una petición y siempre responde con el archivo `respuesta.html`.

```bash
cd Ejercicio_1
python3 servidor_HTTP_1.py
```



### `servidor_proxy.py`

El proxy se pone en medio entre el navegador y el servidor real. Hace tres cosas:

1. **Reenvía** la petición al servidor real y devuelve la respuesta.
2. **Bloquea** los sitios que están en la lista `blocked` (responde 403).
3. **Censura** palabras del body usando la lista `forbidden_words`.

También agrega el header `X-ElQuePregunta` con el correo del usuario a cada petición que hace.

```bash
cd Ejercicio_1
python3 servidor_proxy.py assets/prohibidos.json IP_VM
```

- El primer argumento es el archivo JSON con la configuración.
- El segundo es la IP donde el proxy va a escuchar (puerto 8000).

El archivo `assets/prohibidos.json` se ve así:

```json
{
  "user": "tu@correo.com",
  "blocked": ["www.dcc.uchile.cl"],
  "forbidden_words": [{"proxy": "[REDACTED]"}]
}
```



## Ejercicio 2: resolver DNS

Un resolver escucha peticiones DNS en `localhost:8000` y las contesta. Hay tres versiones que van de menos a más:

- `resolver_v2.py`: solo recibe el mensaje y lo imprime.
- `resolver_v3.py`: recibe el mensaje y lo parsea con `parse_DNS_message`.
- `resolver.py`: recibe el mensaje y se lo pregunta a otro servidor DNS.

```bash
cd Ejercicio_2
python3 resolver.py
```

Para probarlo desde otra terminal:

```bash
dig @localhost -p 8000 www.uchile.cl
```

Necesita la librería `dnslib`:

```bash
pip install dnslib
```

> Nota: `protocolos.py` de este ejercicio apunta al resolver local `127.0.0.53`. Para usar un servidor raíz de verdad hay que cambiar la variable `root_ip`.



## Ejercicio 3: Stop & Wait

`SocketTCP.py` implementa un socket orientado a conexión sobre UDP (handshake, Stop & Wait y cierre). `cliente.py` envía un archivo a `servidor.py` usando esa clase.

Se ejecuta en dos terminales, primero el servidor (escucha en `localhost:8000`):

```bash
cd Ejercicio_3

# terminal 1
python3 servidor.py

# terminal 2
python3 cliente.py localhost 8000 < archivo.txt
```

El archivo llega por la entrada estándar (`< archivo.txt`), no como argumento. El servidor imprime el contenido recibido.

Flags opcionales (se pueden usar en cliente y servidor). En `cliente.py` van siempre después de `localhost 8000`:

| Flag | Qué hace | Por defecto |
|---|---|---|
| `--perdidas` | Simula pérdidas a mano con `perdidas.py`. Usarlo en ambos lados para tener pérdidas en las dos direcciones. | Desactivado: sin pérdidas y timeout de 5 s (`SocketTCP.py`). |
| `--loss=X` | Tasa de pérdida entre 0 y 1 (ej. `0.4` = 40%). Solo tiene efecto junto a `--perdidas`. | `0.2` (`LOSS_RATE` en `perdidas.py`) |
| `--timeout=X` | Timeout de reenvío en segundos. Solo tiene efecto junto a `--perdidas`. | `0.5` (`TIMEOUT` en `perdidas.py`) |
| `--debug` | Muestra los mensajes `[DEBUG]` de envíos, timeouts y reenvíos. | Desactivado |

```bash
# pérdidas con los valores por defecto (20%, timeout 0.5 s)
python3 servidor.py --perdidas --debug
python3 cliente.py localhost 8000 --perdidas --debug < ejemplo.txt

# pérdidas personalizadas (usar los mismos valores en ambos lados)
python3 servidor.py --perdidas --loss=0.4 --timeout=1
python3 cliente.py localhost 8000 --perdidas --loss=0.4 --timeout=1 < ejemplo.txt
```

## Ejercicio 4: Go-Back-N y control de congestión

Parte del código del Ejercicio 3, pero usa las clases `SocketUDP` (`socketUDP.py`) y `SlidingWindowCC` (`slidingWindowCC.py`) entregadas en u-cursos, sin modificarlas.

- `CongestionControl.py`: clase `CongestionControl(MSS)` con slow start y congestion avoidance (Parte 1).
- `SocketTCP.py`: `send` y `recv` reciben un `mode`, que puede ser `"stop_and_wait"` (por defecto) o `"go_back_n"`.
  - Go-Back-N usa trozos de MSS = 8 bytes.
  - Sin control de congestión, la ventana queda fija en 8 segmentos (Parte 2).
  - Con `set_congestion_control(True)`, la ventana parte en 1 segmento y sigue a `cwnd` (Parte 3).

### Test de `CongestionControl`

```bash
cd Ejercicio_4
python3 CongestionControl_test.py
```

### Cliente y servidor

Igual que en el Ejercicio 3: dos terminales, primero el servidor (escucha en `localhost:8000`, y se detiene con Ctrl+C), y el archivo entra por la entrada estándar.

```bash
cd Ejercicio_4

# terminal 1
python3 servidor.py --gbn

# terminal 2
python3 cliente.py localhost 8000 --gbn --cc < archivo.txt
```

Al terminar, el cliente imprime el tiempo de envío y, en Go-Back-N, cuántos segmentos de datos mandó (`number_of_sent_segments`). El cierre de la conexión tarda unos segundos más, porque el último ACK se reenvía 3 veces con un timeout entremedio.

Flags (en `cliente.py` van siempre después de `localhost 8000`):

| Flag | Dónde | Qué hace | Por defecto |
|---|---|---|---|
| `--gbn` | cliente **y** servidor | Usa Go-Back-N en vez de Stop & Wait. Tiene que ir en los dos lados, o no se entienden. | Stop & Wait |
| `--cc` | cliente | Activa el control de congestión en Go-Back-N. Solo afecta a quien envía. Sin `--gbn` no hace nada. | Ventana fija de 8 |
| `--perdidas` | cliente y servidor | Simula pérdidas con `perdidas.py`. Usarlo en ambos lados para tener pérdidas en las dos direcciones. | Sin pérdidas, timeout de 5 s |
| `--loss=X` | junto a `--perdidas` | Tasa de pérdida entre 0 y 1. | `0.2` |
| `--timeout=X` | junto a `--perdidas` | Timeout de reenvío en segundos. | `0.5` |
| `--debug` | cliente y servidor | Muestra los mensajes `[DEBUG]`. Con `--cc`, el cliente además muestra `[DEBUG CC]` con el estado, `cwnd`, `ssthresh` y `window_size` en cada ACK y timeout. | Desactivado |

```bash
# Go-Back-N con ventana fija de 8 (Parte 2), con pérdidas
python3 servidor.py --gbn --perdidas
python3 cliente.py localhost 8000 --gbn --perdidas < archivo.txt

# Go-Back-N con control de congestión (Parte 3), viendo cómo evoluciona la ventana
python3 servidor.py --gbn --perdidas
python3 cliente.py localhost 8000 --gbn --cc --debug --perdidas < archivo.txt
```

Para comparar con y sin control de congestión, transmite el mismo archivo 5 veces con `--cc` y 5 veces sin él, con pérdida 20% y timeout 0.5 s (los valores por defecto de `--perdidas`), y anota el tiempo y los segmentos que imprime el cliente.

### Tests del paso 5 (`t_sv.py` / `t_client.py`)

Prueban mensajes de 16 y 19 bytes, un `recv` con `buff_size` menor al mensaje y el cierre. Usan el puerto 5000 y aceptan los mismos flags (`--cc` y `--debug` solo en `t_client.py`).

```bash
cd Ejercicio_4

# terminal 1
python3 t_sv.py --gbn --perdidas

# terminal 2
python3 t_client.py --gbn --cc --perdidas
```

El servidor imprime `Test N: Passed` o `Test N: Failed` para cada uno de los 4 tests.

## Cómo correr el servidor en la VM (VirtualBox)

Para que el servidor sea alcanzable desde fuera de la VM (por ejemplo desde el navegador del host), la VM necesita estar en modo Adaptador Puente, no NAT.

1. Apaga la VM.
2. En VirtualBox ve a Configuración de la VM, luego Red, luego Adaptador 1, y en "Conectado a" elige Adaptador puente. Selecciona tu interfaz de red física (WiFi o Ethernet).
3. Enciende la VM.
4. Dentro de la VM abre una terminal y corre `ip a` para ver tu IP. Busca la interfaz que no sea `lo` (normalmente `enp0s3`), y anota la IP que aparece ahí, por ejemplo `192.168.1.50`. Esta es la IP_VM.
5. Corre el servidor con la IP_VM que anotaste.
6. Desde el navegador de tu máquina host, entra a `http://IP_VM:8000` reemplazando IP_VM por la IP real.

Para que el navegador use el proxy, hay que configurarlo en las opciones de red del navegador apuntando a `IP_VM` puerto `8000`.

## Ejercicio 5: Forwarding, Round Robin y TTL

Simula una red de routers ejecutando cada nodo como un proceso distinto en `localhost` sobre sockets UDP. Cada router lee su tabla de rutas al iniciar, al recibir paquetes que debe reenviar alterna entre los siguientes saltos por área usando `round-robin` (`itertools.cycle`), decrementa el `TTL` en cada reenvío y descarta paquetes si `TTL == 0` o si no encuentra ruta.

El header del paquete ocupa **7 bytes** (`IP` 4 B + `Puerto` 2 B + `TTL` 1 B), seguido del mensaje:

- `router.py`: implementa la clase `Router` (`map_routes`, `check_routes`, `parse_packet` y `create_packet`).
- `sender.py`: envía un mensaje individual ingresado por teclado hacia un destino final a través de un primer salto.
- `prueba_router.py`: lee `ejemplo.txt` línea por línea y envía cada línea como un paquete independiente.

### Levantar la red y enviar mensajes

Las tablas tienen formato `red/máscara puerto_inicio puerto_fin IP_siguiente_salto puerto_siguiente_salto`. Para levantar la red de 5 routers (`rutas_R1_v3.txt` a `rutas_R5_v3.txt`), abre 5 terminales:

```bash
cd Ejercicio_5

# terminal 1 a 5 (una por router)
python3 router.py 127.0.0.1 8881 rutas_R1_v3.txt
python3 router.py 127.0.0.1 8882 rutas_R2_v3.txt
python3 router.py 127.0.0.1 8883 rutas_R3_v3.txt
python3 router.py 127.0.0.1 8884 rutas_R4_v3.txt
python3 router.py 127.0.0.1 8885 rutas_R5_v3.txt
```

Para la red de 7 routers se usan las tablas `rutas_R0_v4.txt` a `rutas_R6_v4.txt` en los puertos `8880` a `8886`.

En otra terminal, envía mensajes con `sender.py` o `prueba_router.py`:

```bash
# enviar un mensaje a R5 (8885) entrando por R1 (8881) con TTL 10 (pide el mensaje por teclado)
python3 sender.py 127.0.0.1 8885 127.0.0.1 8881 10

# enviar todas las líneas de ejemplo.txt ("IP;puerto;TTL" IP_inicial puerto_inicial)
python3 prueba_router.py "127.0.0.1;8885;10" 127.0.0.1 8881
```

> Nota: `prueba_router.py` tiene fijo el nombre `ejemplo.txt`, así que debe ejecutarse desde `Ejercicio_5/`. Si no se tiene `typing_extensions` instalado, se debe utilizar con el entorno virtual `pip install typing_extensions`.

### Router default y tests

Las tablas terminan con una ruta default (`0` a `65535`) apuntando a `127.0.0.1:7000`. Puedes escuchar ahí con `netcat` y enviar a un puerto fuera de la red (ej. `9000`) para comprobar que el paquete sale hacia el router default:

```bash
# terminal extra (escucha como router default)
nc -u -l 7000

# enviar a destino fuera de la red
python3 sender.py 127.0.0.1 9000 127.0.0.1 8881 10
```

Tests unitarios:

```bash
cd Ejercicio_5
python3 test.py                  # verifica que parse_packet y create_packet sean inversas
python3 test_checkout_routes.py  # verifica check_routes y casos borde en las tablas
```

## Ejercicio 6: Fragmentación y reensamblado IP

Parte del código del Ejercicio 5 y agrega límites de **MTU** por enlace, fragmentación (incluyendo refragmentación en saltos intermedios si el siguiente enlace tiene un MTU menor) y reensamblado de paquetes por `Id` en el destino.

El header crece a **18 bytes** para soportar fragmentación:

| Campo | Tamaño | Bytes | Descripción |
| :--- | :---: | :---: | :--- |
| `IP` | 4 B | 0–3 | IP de destino final |
| `Puerto` | 2 B | 4–5 | Puerto de destino final |
| `TTL` | 1 B | 6 | Time To Live |
| `tamaño` | 4 B | 7–10 | Largo en bytes del payload de este paquete |
| `Id` | 2 B | 11–12 | Identificador del paquete original |
| `Offset` | 4 B | 13–16 | Posición (en bytes) donde empieza este fragmento respecto al mensaje original |
| `Flag` | 1 B | 17 | `1` si vienen más fragmentos; `0` si es el último o no está fragmentado |

Principales cambios respecto al ejercicio anterior:

- `router.py`: agrega `fragment_IP_packet(IP_packet, MTU)` y `reassemble_IP_packet(fragment_list)`. Las tablas de rutas incorporan una columna adicional al final con el `MTU` del enlace.
- `sender.py`: recibe el `Id` del paquete como último argumento.

### Ejecución y prueba de fragmentación

Levanta los 5 routers en terminales separadas y envía paquetes indicando el `Id` al final:

```bash
cd Ejercicio_6

# terminal 1 a 5
python3 router.py 127.0.0.1 8881 rutas_R1_v3.txt
python3 router.py 127.0.0.1 8882 rutas_R2_v3.txt
python3 router.py 127.0.0.1 8883 rutas_R3_v3.txt
python3 router.py 127.0.0.1 8884 rutas_R4_v3.txt
python3 router.py 127.0.0.1 8885 rutas_R5_v3.txt

# terminal 6: enviar paquete con TTL=10 e Id=347 (pide el mensaje por teclado)
python3 sender.py 127.0.0.1 8881 127.0.0.1 8885 10 347
```

Para forzar fragmentación y refragmentación en cascada (paquete total de 150 bytes = 18 B de header + 132 B de mensaje), ingresa un texto de 132 caracteres cuando `sender.py` pida el mensaje, por ejemplo:

```text
Como decir paralelepipedo sin bipedo ni niptero?. O bien, como se dice hipopotomonstrosesquipedaliofobia sin fobia y sin hipopotamo?
```

### Tests

```bash
cd Ejercicio_6
python3 test.py           # verifica ida y vuelta de parse/create y fragment/reassemble
python3 test_fragment.py  # prueba fragmentación de un paquete de 24 B con MTU 30 y MTU 20
python3 test_info.py      # simula recepción de fragmentos de 2 Ids distintos (ordenados, desordenados e intercalados)
```