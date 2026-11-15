import sys
import socket
from dataclasses import dataclass

# 4. Estructura de datos para el paquete.
# Dentro del programa los campos se guardan con tipos "cómodos" (str e int).
# La conversión a bytes y desde bytes ocurre SOLO en parse_packet y create_packet.
#
# Formato en bytes del paquete:
#   [ IP: 4 bytes ][ puerto: 2 bytes ][ mensaje: resto ]
@dataclass
class Paquete:
    # header
    ip: str       # IP de destino final, ej: "127.0.0.1"
    puerto: int   # puerto de destino final, ej: 8882
    # body
    mensaje: str  # contenido, ej: "hola"


# bytes -> Paquete
def parse_packet(IP_packet: bytes) -> Paquete:
    ip = ".".join(str(b) for b in IP_packet[0:4])      # 4 bytes -> "a.b.c.d"
    puerto = int.from_bytes(IP_packet[4:6], "big")     # 2 bytes -> int
    mensaje = IP_packet[6:].decode()                   # resto -> str
    return Paquete(ip, puerto, mensaje)


# Paquete -> bytes
def create_packet(parsed_IP_packet: Paquete) -> bytes:
    ip_bytes = bytes(int(n) for n in parsed_IP_packet.ip.split("."))  # "a.b.c.d" -> 4 bytes
    puerto_bytes = parsed_IP_packet.puerto.to_bytes(2, "big")         # int -> 2 bytes
    mensaje_bytes = parsed_IP_packet.mensaje.encode()                 # str -> bytes
    return ip_bytes + puerto_bytes + mensaje_bytes

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
        data_packet = parse_packet(paquete)
        print("Paquete recibido: ", data_packet, " desde: ", direccion)

        destination_address: tuple[str, int] = (data_packet.ip, data_packet.puerto)

        # 7. El router checkea si el paquete es para él.
        # Un router es el par (IP, puerto), así que se comparan ambos.
        if destination_address == address:
            print(data_packet.mensaje)
        else:
            direccion_next_hop = check_routes(router_rutas_path, destination_address)
            if direccion_next_hop is not None:
                print(f"redirigiendo paquete {paquete} con destino final {destination_address} desde {address} hacia {direccion_next_hop}")
                # forward: se envía con el mismo socket del router (no se hace bind de nuevo)
                router_socket.sendto(create_packet(data_packet), direccion_next_hop)
            else:
                print(f"No hay rutas hacia {destination_address} para paquete {paquete}")
