import sys
import socket
from dataclasses import dataclass

# 4. Estructura de datos para el paquete
@dataclass
class Paquete:
    #header
    ip: bytes #a.b.c.d son 4 bytes
    puerto: bytes # son 2 bytes. es un int de python transformado a bytes
    #body
    mensaje: bytes

# Función para parsear el mensaje recibido y extraer los headers
def parse_packet(IP_packet: bytes) -> Paquete:
    parsed_packet = Paquete(IP_packet[0:5], IP_packet[5:7], IP_packet[7:])
    return parsed_packet

# Función para crear un paquete en bytes a partir de la estructura Paquete
def create_packet(parsed_IP_packet: Paquete) -> bytes:
    extended_packet = parsed_IP_packet.ip + parsed_IP_packet.puerto + parsed_IP_packet.mensaje
    return extended_packet

# 2. Recibir los args
router_IP: str = sys.argv[1] #127.0.0.1
router_puerto: int = int(sys.argv[2]) #8881
router_rutas_path: str = sys.argv[3] #rutas_R1_v1

with open(router_rutas_path, "r") as archivo:
    router_rutas: str = archivo.read()


# 3. Crear el socket UDP (no orientado a conexión)
router_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# hacer que escuche de forma bloqueante
address = (router_IP, router_puerto)
router_socket.bind(address)

while True:
    paquete, direccion = router_socket.recvfrom(1024)
