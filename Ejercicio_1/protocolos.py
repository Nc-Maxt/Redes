# toma un mensaje en bytes y lo transforma en un dict de bytes
def parse_HTTP_message(http_message: bytes) -> dict[bytes]:
    # separamos header de body
    head, body = http_message.split(b"\r\n\r\n", 1)

    #para el head, separaremos cada línea
    head_lines = head.split(b"\r\n")
    # La estructura a usar será un diccionario
    HTTP_dict = {}
    # Primero trabajamos y agregamos la información de la startline
    informacion(HTTP_dict, head_lines[0])

    # Luego con cada línea se hace una llave y un valor, separando la clave del valor por el primer ":"
    for line in head_lines[1:]:
        key, value = line.split(b":", 1)
        # se usa strip para eliminar espacios en blanco al inicio y al final
        HTTP_dict[key.strip()] = value.strip()

    # El body se agrega al diccioanrio
    HTTP_dict["body"] = body
    return HTTP_dict

def informacion(head_dict: dict, start_line: bytes) -> None:
    # Separamos la start_line en sus 3 partes principales.
    # Si empieza con "HTTP/" es una response (versión código razón),
    # si no, es una request (método ruta versión)
    primero, segundo, tercero = start_line.split(b" ", 2)
    if primero.decode().startswith("HTTP/"):
        head_dict["versión"] = primero.strip() #"HTTP/1.1"
        head_dict["código"] = segundo.strip() # 200
        head_dict["razón"] = tercero.strip() # "OK"
    else:
        head_dict["método"] = primero.strip() # "GET"
        head_dict["ruta"] = segundo.strip() # "/"
        head_dict["versión"] = tercero.strip() # "HTTP/1.1"


def create_HTTP_message(data: dict[bytes]) -> bytes:
    # recibimos la estructura de datos enviada por parse_HTTP y lo convertimos en una cadena de texto con el formato HTTP

    #Creamos el string que contendrá el mensaje HTTP completo
    http_message = ""
    # Primero agregamos la startline
    http_message = st_l(data, http_message)

    # Luego sacamos el body del diccionario
    body = data.pop('body')

    #Luego agregamos los headers
    for key in data.keys():
        http_message += f"{key.decode()}: {data[key].decode()}\r\n"

    # Agregamos el body
    http_message = http_message + b"\r\n" + body

    # Retornamos el mensaje HTTP completo en bytes
    return http_message

def st_l(data: dict, msg: bytes) -> str:
    # Armamos la startline con los datos del diccionario.
    # Si el diccionario tiene 'código', es una response; si no, es una request.
    if "código" in data:
        msg += data.pop('versión') + b" " + data.pop('código') + b" " data.pop('razón') + b"\r\n"
    else:
        msg += data.pop('método') + data.pop('ruta') + b" " + data.pop('versión').decode()}\r\n"
    return msg

        
