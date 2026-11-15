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
    parsed_packet = Paquete(IP_packet[0:4], IP_packet[4:6], IP_packet[6:])
    return parsed_packet

# Función para crear un paquete en bytes a partir de la estructura Paquete
def create_packet(parsed_IP_packet: Paquete) -> bytes:
    extended_packet = parsed_IP_packet.ip + parsed_IP_packet.puerto + parsed_IP_packet.mensaje
    return extended_packet

# 6. Función para checkear la tabla de rutas e indicar la dirección del siguiente salto
def check_routes(routes_file_name: str, destination_address: tuple[str, int]) -> tuple[str,int] | None:
    with open(routes_file_name, "r") as archivo:
        router_rutas: list[str] = archivo.read().split("\n")
        _, puerto = destination_address
        for line in router_rutas:
            #print(line)
            linea = line.split(" ")
            #print(linea)
            rango = linea[1:3]
            rango = map(int, rango)
            #print(rango)
            if puerto in rango:
                ip = linea[3]
                puerto_destino = int(linea[4])
                return (ip, puerto_destino)
        return None


if __name__ == "__main__":
    # 2. Recibir los args
    router_IP: str = sys.argv[1] #127.0.0.1
    router_puerto: int = int(sys.argv[2]) #8881
    router_rutas_path: str = sys.argv[3] #rutas_R1_v2

    # Test
    print("Router iniciado con la IP ", router_IP, "en el puerto: ", router_puerto, "y su mapa de rutas: ", router_rutas_path)

    # 3. Crear el socket UDP (no orientado a conexión)
    router_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # hacer que escuche de forma bloqueante
    address = (router_IP, router_puerto)
    router_socket.bind(address)

    while True:
        paquete, direccion = router_socket.recvfrom(1024)
        print(paquete)
        data_packet = parse_packet(paquete)
        print("Paquete recibido: ", paquete, " con la direccion: ", direccion)
        print(data_packet, paquete)

        paquete_ip:str = data_packet.ip.decode() #ip destino
        destination_address:int = int.from_bytes(data_packet.puerto) #puerto destino

        # 7. El router checkea si el paquete es para el
        print("Checkeando si es para mí...")
        if destination_address == router_puerto:
            print(data_packet.mensaje)
        else:
            direccion_next_hop = check_routes(router_rutas_path, (paquete_ip,destination_address))
            if direccion_next_hop is not None:
                print(f"Redirigiendo paquete {paquete_ip} con destino final {destination_address} desde {router_puerto} hacia {direccion_next_hop}")
            else:
                print(f"No hay rutas hacia {destination_address} para paquete {paquete_ip}")
