import sys
import socket

# 2. Recibir los args
router_IP: str = sys.argv[1] #127.0.0.1
router_puerto: int = int(sys.argv[2]) #8881
router_rutas_path: str = sys.argv[3] #rutas_R1_v1

with open(router_rutas_path, "rb") as archivo:
    router_rutas: bytes = archivo.read()


# 3. Crear el socket UDP (no orientado a conexión)
socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# hacer que escuche de forma bloqueante
address = (router_IP, router_puerto)
socket.bind(address)

while True:
    paquete, direccion = socket.recvfrom(1024)
