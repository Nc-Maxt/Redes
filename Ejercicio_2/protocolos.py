
import dnslib
from dnslib.dns import CLASS, QTYPE
from dnslib.dns import RR, A
from dnslib import DNSRecord
import socket

def send_DNS_query(mensaje: bytes, server_ip: str, server_port: int = 53) -> bytes:
    #recordar que el mensaje de consulta es justamente el que recibo del cliente
    # ahora yo debo ser quien envia ese mensaje al sv para preguntar
    # para ello debo hacer otro socket para actuar como cliente
    # como es no orientado a conexion sera un efimero
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # recuperamos el address a donde hay que mandar el mensaje
    address = (server_ip, 53)
    print("voy a mandar un mensaje")
    client_socket.sendto(mensaje, address)
    print("esperando mensaje")
    resp, _ = client_socket.recvfrom(4096)
    print("recibí mensaje")
    client_socket.close()
    return resp

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


#root_ip = "127.0.0.53"
root_ip = "198.41.0.4"

def resolver(mensaje_consulta: bytes, ip_addr: str = root_ip, debug: bool = False) -> bytes:

    resp = send_DNS_query(mensaje_consulta, ip_addr)

    datos = parse_DNS_message(resp)
    buscado = datos["Qname"]
    print(datos)

    nombre = "."
    n_ip = ip_addr
    if datos["ANCOUNT"] > 0:
        for record in datos["Answer"]:
            if QTYPE.get(record.rtype) == "A":
                if debug:
                    print("(debug) Consulta resuelta.")
                return resp
    if datos["NSCOUNT"]>0:
        for record in datos["Additional"]:
            if QTYPE.get(record.rtype) == "A":
                n_ip = record.rdata
                nombre = record.get_rname()
                if debug:
                    print(f"(debug) Consultando '{buscado}' a '{nombre}' con dirección IP '{n_ip}'")
                valor = resolver(mensaje_consulta, n_ip, debug)
                if valor is not None:
                    return valor
                        
        for record in datos["Authority"]:
            if QTYPE.get(record.rtype) == "NS":
                ns = record
                buscar = ns.get_rdata()
                q = DNSRecord.question(buscar)
                question = q.encode()
                info = resolver(question, debug=debug)
                parseado = parse_DNS_message(info)
                for record in parseado["Answer"]:
                    if QTYPE.get(record.rtype) == "A":
                        n_ip = record.rdata
                        nombre = record.get_rname()
                        if debug:
                            print(f"(debug) Consultando '{buscado}' a '{nombre}' con dirección IP '{n_ip}'")
                        valor = resolver(mensaje_consulta, n_ip, debug)
                        if valor is not None:
                            return valor
    else:
        if debug:
            print("(debug) No es uno de los casos a estudiar.")
        return None
