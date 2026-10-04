# Redes

Tareas del curso de Redes (CC4303). Todo está hecho en Python con la librería `socket`.

## Qué hay en cada carpeta


| Carpeta                        | Qué es                                                                |
| ------------------------------ | --------------------------------------------------------------------- |
| `orientados_Socket/`           | Cliente y servidor con TCP (orientado a conexión). Ejemplo básico.    |
| `No_orientados_Sockets (ex1)/` | Cliente y servidor con UDP (no orientado a conexión). Ejemplo básico. |
| `Ejercicio_1/`                 | Servidor HTTP y proxy HTTP.                                           |
| `Ejercicio_2/`                 | Resolver DNS.                                                         |


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

## Cómo correr el servidor en la VM (VirtualBox)

Para que el servidor sea alcanzable desde fuera de la VM (por ejemplo desde el navegador del host), la VM necesita estar en modo Adaptador Puente, no NAT.

1. Apaga la VM.
2. En VirtualBox ve a Configuración de la VM, luego Red, luego Adaptador 1, y en "Conectado a" elige Adaptador puente. Selecciona tu interfaz de red física (WiFi o Ethernet).
3. Enciende la VM.
4. Dentro de la VM abre una terminal y corre `ip a` para ver tu IP. Busca la interfaz que no sea `lo` (normalmente `enp0s3`), y anota la IP que aparece ahí, por ejemplo `192.168.1.50`. Esta es la IP_VM.
5. Corre el servidor con la IP_VM que anotaste.
6. Desde el navegador de tu máquina host, entra a `http://IP_VM:8000` reemplazando IP_VM por la IP real.

Para que el navegador use el proxy, hay que configurarlo en las opciones de red del navegador apuntando a `IP_VM` puerto `8000`.