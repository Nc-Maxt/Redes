from dnslib.dns import RR, A
from dnslib import DNSRecord
from dnslib.dns import CLASS, QTYPE
import dnslib


# toma un mensaje en bytes y lo transforma en un dict de bytes
def parse_DNS_message(dns_message: bytes) -> dict[hex]:
    # como el mensaje esta en formato dns por la librería, podemos usar la librería para parsearlo 
    # y obtener la información relevante Qname, ANCOUNT, NSCOUNT, ARCOUNT, la sección Answer, la sección Authority y la sección Additional

    d = DNSRecord.parse(dns_message)
    # armamos un diccionario con la información relevante   
    info = {}
    info["Qname"] = d.questions[0].get_qname()
    info["ANCOUNT"] = d.header.a
    info["NSCOUNT"] = d.header.auth
    info["ARCOUNT"] = d.header.ar
    info["Answer"] = d.rr
    info["Authority"] = d.auth
    info["Additional"] = d.ar
    return info


def informacion(head_dict: dict, start_line: bytes) -> None:
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
    # recibimos la estructura de datos enviada por parse_HTTP y lo convertimos en una cadena de texto con el formato HTTP

    #Creamos el string que contendrá el mensaje HTTP completo
    http_message = b""
    # Primero agregamos la startline
    http_message = st_l(data, http_message)
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

def st_l(data: dict, msg: bytes) -> bytes:
    # Armamos la startline con los datos del diccionario.
    # Si el diccionario tiene 'código', es una response; si no, es una request.
    if b"response" in data:
        msg = msg + data.pop(b'version') + b" " + data.pop(b'response') + b" " + data.pop(b'reason') + b"\r\n"
    else:
        msg = msg + data.pop(b'method')+ b" " + data.pop(b'path') + b" " + data.pop(b'version') + b"\r\n"
    return msg

        
