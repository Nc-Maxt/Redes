def parse_HTTP_message(http_message: bytes) -> dict[bytes]:
    """Parsea un mensaje HTTP crudo y lo transforma en un diccionario.

    La start line se descompone en sus partes (method/path/version o
    version/response/reason), cada header pasa a ser una entrada llave -> valor
    y el body queda bajo la llave b"body". Es la operación inversa de
    create_HTTP_message.

    Args:
        http_message: Mensaje HTTP completo (request o response) en bytes.

    Returns:
        Diccionario con llaves y valores en bytes.
    """
    # separamos header de body
    head, body = http_message.split(b"\r\n\r\n", 1)

    #para el head, separaremos cada línea
    head_lines = head.split(b"\r\n")
    # La estructura a usar será un diccionario
    HTTP_dict = {}
    # Primero trabajamos y agregamos la información de la startline
    _informacion(HTTP_dict, head_lines[0])

    # Luego con cada línea se hace una llave y un valor, separando la clave del valor por el primer ":"
    for line in head_lines[1:]:
        key, value = line.split(b":", 1)
        # se usa strip para eliminar espacios en blanco al inicio y al final
        HTTP_dict[key.strip()] = value.strip()

    # El body se agrega al diccioanrio
    HTTP_dict[b"body"] = body
    return HTTP_dict

def _informacion(head_dict: dict, start_line: bytes) -> None:
    """Interpreta la start line de un mensaje HTTP y la agrega a head_dict.

    Si la línea empieza con "HTTP/" se trata como response y se guardan las
    llaves b"version", b"response" y b"reason". En caso contrario se trata
    como request y se guardan b"method", b"path" y b"version".

    Args:
        head_dict: Diccionario al que se agregan las llaves (se modifica in-place).
        start_line: Primera línea del mensaje HTTP en bytes.

    Returns:
        None.
    """
    # Separamos la start_line en sus 3 partes principales.
    # Si empieza con "HTTP/" es una response (version response reason),
    # si no, es una request (method path version)
    primero, segundo, tercero = start_line.split(b" ", 2)
    if primero.decode().startswith("HTTP/"):
        head_dict[b"version"] = primero.strip() #"HTTP/1.1"
        head_dict[b"response"] = segundo.strip() # 200
        head_dict[b"reason"] = tercero.strip() # "OK"
    else:
        head_dict[b"method"] = primero.strip() # "GET"
        head_dict[b"path"] = segundo.strip() # "/"
        head_dict[b"version"] = tercero.strip() # "HTTP/1.1"


def create_HTTP_message(data: dict[bytes]) -> bytes:
    """Construye un mensaje HTTP completo en bytes a partir de un diccionario.

    Recibe la misma estructura que entrega parse_HTTP_message. Arma la start
    line, agrega cada header como "llave: valor\\r\\n" y finalmente el body
    separado por una línea en blanco.

    Args:
        data: Diccionario con llaves y valores en bytes. Se modifica, ya que
            las llaves de la start line y el body se extraen con pop.

    Returns:
        Mensaje HTTP completo (start line + headers + body) en bytes.
    """
    # recibimos la estructura de datos enviada por parse_HTTP y lo convertimos en una cadena de texto con el formato HTTP

    #Creamos el string que contendrá el mensaje HTTP completo
    http_message = b""
    # Primero agregamos la startline
    http_message = _st_l(data, http_message)
    print(http_message)

    # Luego sacamos el body del diccionario
    body = data.pop(b'body')

    #Luego agregamos los headers
    for key in data.keys():
        http_message += key + b": " + data[key]+ b"\r\n"

    # Agregamos el body
    http_message = http_message + b"\r\n" + body

    # Retornamos el mensaje HTTP completo en bytes
    return http_message

def _st_l(data: dict, msg: bytes) -> bytes:
    """Arma la start line del mensaje HTTP y la concatena al final de msg.

    Si el diccionario contiene la llave b"response" se genera una status line
    ("version response reason"); si no, una request line ("method path version").

    Args:
        data: Diccionario del mensaje. Las llaves usadas se extraen con pop.
        msg: Mensaje parcial en bytes al que se agrega la start line.

    Returns:
        msg con la start line agregada, en bytes.
    """
    # Armamos la startline con los datos del diccionario.
    # Si el diccionario tiene 'código', es una response; si no, es una request.
    if b"response" in data:
        msg = msg + data.pop(b'version') + b" " + data.pop(b'response') + b" " + data.pop(b'reason') + b"\r\n"
    else:
        msg = msg + data.pop(b'method')+ b" " + data.pop(b'path') + b" " + data.pop(b'version') + b"\r\n"
    return msg

        
