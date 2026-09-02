from dnslib.dns import RR, A
from dnslib import DNSRecord
import socket

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

root_ip = "198.41.0.4"
def resolver(mensaje_consulta: bytes, ip_addr=root_ip) -> bytes:
    #recordar que el mensaje de consulta es justamente el que recibo del cliente
    # ahora yo debo ser quien envia ese mensaje al sv para preguntar
    # para ello debo hacer otro socket para actuar como cliente
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Como es un socket NO orientado a conexión no necesitamos conectarlo a una dirección específica
    address = ('localhost', 5000)
    print("voy a mandar un mensaje")
    client_socket.sendto(mensaje_consulta, address)
    print("esperando mensaje")
    resp, _ = client_socket.recvfrom(4096)
    print("recibí mensaje")
    datos = parse_DNS_message(resp)
    return datos
