def parse_HTTP_message(http_message: bytes):
    # Con esto llega un mensage HTTP completo en bytes, por lo que primero hay que decodificarlo a string
    http_message = http_message.decode()
    # ahora este tiene el header y el body, se debe separar en dos. Usamos como referencia el doble salto de línea
    head, body = http_message.split("\r\n\r\n", 1)

    #para el head, separaremos cada línea
    head_lines = head.split("\r\n")
    # La estructura a usar será un diccionario
    HTTP_dict = {}
    # Primero trabajamos y agregamos la información de la startline
    informacion(HTTP_dict, head_lines[0])

    # Luego con cada línea se hace una llave y un valor, separando la clave del valor por el primer ":"
    for line in head_lines[1:]:
        key, value = line.split(":", 1)
        # se usa strip para eliminar espacios en blanco al inicio y al final
        HTTP_dict[key.strip()] = value.strip()

    # El body se agrega al diccioanrio
    HTTP_dict["body"] = body
    return HTTP_dict

def informacion(head_dict, start_line):
    # Separamos la start_line en las 3 partes principales
    # Método, ruta y versión
    met, path, vers = start_line.split(" ", 2)
    # los agregamos al diccionario
    head_dict["método"] = met.strip()
    head_dict["ruta"] = path.strip()
    head_dict["versión"] = vers.strip()


def create_HTTP_message(data: dict):
    # recibimos la estructura de datos enviada por parse_HTTP y lo convertimos en una cadena de texto con el formato HTTP

    #Creamos el string que contendrá el mensaje HTTP completo
    http_message = ""
    # Primero agregamos la startline
    http_message = st_l(data, http_message)

    # Luego sacamos el body del diccionario
    body = data.pop('body')

    #Luego agregamos los headers
    for key in data.keys():
        http_message += f"{key}: {data[key]}\r\n"

    # Agregamos el body
    http_message += f"\r\n{body}"

    # Retornamos el mensaje HTTP completo en bytes
    return http_message.encode()

def st_l(data: dict, msg: str):
    # Armamos la startline con los datos del diccionario
    msg += f"{data.pop('método')} {data.pop('ruta')} {data.pop('versión')}\r\n"
    return msg
        