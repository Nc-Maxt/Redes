import sys
import socket
from dataclasses import dataclass
from itertools import cycle

from typing_extensions import Iterator

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
    ttl: int      # saltos restantes que le quedan al paquete entre 0 y 255
    tamaño: int   # tamaño del mensaje sin headers, usa 4 bytes fijo
    Id: int       # sirve para identificar fragmentos de un mismo paquete Ip
    Offset: int   # sirve para identificar la posición del inicio de este mensaje relativo al datagrama original
    Flag: int     # sirve para indicar si este paquete es el último fragmento 0 o no 1 
    # body
    mensaje: str  # contenido, ej: "hola"

class Router:
    def __init__(self, router_IP, router_puerto, router_rutas_path) -> None:
        self.ip: str = router_IP
        self.puerto: int = router_puerto
        self.path_rutas: str = router_rutas_path
        self.address:tuple[str,int] = (self.ip,self.puerto)
        self.rutas = self.map_routes(self.path_rutas)

    # bytes -> Paquete
    def parse_packet(self, IP_packet: bytes) -> Paquete:
        ip = ".".join(str(b) for b in IP_packet[0:4])      # 4 bytes -> "a.b.c.d"
        puerto = int.from_bytes(IP_packet[4:6], "big")     # 2 bytes -> int
        ttl = IP_packet[6]                                 # 1 byte -> int
        size = int.from_bytes(IP_packet[7:11], "big")      # 4 bytes -> int
        Id = int.from_bytes(IP_packet[11:15], "big")       # 4 bytes -> int
        Offset = int.from_bytes(IP_packet[15:19], "big")   # 4 bytes -> int
        Flag = int.from_bytes(IP_packet[19:20], "big")     # 1 byte -> int

        mensaje = IP_packet[20:].decode()                   # resto -> str
        return Paquete(ip, puerto, ttl, size, Id, Offset, Flag, mensaje)

    # Paquete -> bytes
    def create_packet(self, parsed_IP_packet: Paquete) -> bytes:
        ip_bytes = bytes(int(n) for n in parsed_IP_packet.ip.split("."))  # "a.b.c.d" -> 4 bytes
        puerto_bytes = parsed_IP_packet.puerto.to_bytes(2, "big")         # int -> 2 bytes
        ttl_bytes = parsed_IP_packet.ttl.to_bytes(1, "big")               # int -> 1 byte
        size_bytes = parsed_IP_packet.tamaño.to_bytes(4, "big")           # int -> 4 bytes
        Id_bytes = parsed_IP_packet.Id.to_bytes(4, "big")                 # int -> 4 bytes
        Offset_bytes = parsed_IP_packet.Offset.to_bytes(4, "big")         # int -> 4 bytes
        Flag_bytes = parsed_IP_packet.Flag.to_bytes(1, "big")             # int -> 1 byte

        mensaje_bytes = parsed_IP_packet.mensaje.encode()                 # str -> bytes
        return ip_bytes + puerto_bytes + ttl_bytes + size_bytes + Id_bytes + Offset_bytes + Flag_bytes + mensaje_bytes

    # 6. Función para checkear la tabla de rutas e indicar la dirección del siguiente salto
    def check_routes(self, routes_file_name: str, destination_address: tuple[str, int]) -> tuple[str,int] | None:
        _, puerto = destination_address
        rutas = self.rutas
        for rango in rutas:
            if puerto >= rango[0] and puerto <= rango[1]:
                round_robin = rutas[rango]
                # Se obtiene la ruta a donde se debe realizar el salto
                destino = next(round_robin) #round robin
                address_destino:tuple[str,int] = (destino[0][0], destino[0][1])
                mtu = destino[1]
                return address_destino, mtu
        return None
    
    # 8. Round robin
    # Funcion que recibe un path a un archivo con las rutas y devuelve un diccionario donde la llave
    # es cada rango y las llaves almacenan una lista de todos los destinos + el destino que le tocaria segun Round Robin
    def map_routes(self, path_rutas:str) -> dict[tuple[int,int], Iterator]:
        with open(path_rutas, "r") as archivo:
            router_rutas: list[str] = archivo.read().splitlines()
            diccionario_final = {}
            for line in router_rutas: #primero leo el archivo y almaceno los destinos de cada rango
                # se ignoran las líneas vacías o con solo espacios
                if line.strip() == "":
                    continue
                linea = line.split()
                tupla_rango = (int(linea[1]), int(linea[2]))
                next_hop = [(linea[3], int(linea[4])), linea[5]]  # (IP, puerto) del siguiente salto
                if tupla_rango in diccionario_final:
                    diccionario_final[tupla_rango].append(next_hop)
                else:
                    # opcion con clases
                    # diccionario_final[tupla_rango] = Ciclic_list([[next_hop]])
                    diccionario_final[tupla_rango] = [next_hop]

        #Luego hago un cycle sobre cada lista de cada rango
        for range in diccionario_final:
            diccionario_final[range] = cycle(diccionario_final[range])
        return diccionario_final


if __name__ == "__main__":
    # 2. Recibir los args
    router_IP: str = sys.argv[1] #127.0.0.1
    router_puerto: int = int(sys.argv[2]) #8881
    router_rutas_path: str = sys.argv[3] #rutas_R1_v2

    router = Router(router_IP, router_puerto, router_rutas_path)

    # Test
    print("Router iniciado con la IP ", router_IP, "en el puerto: ", router_puerto, "y su mapa de rutas: ", router_rutas_path)

    # 3. Crear el socket UDP (no orientado a conexión)
    router_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # hacer que escuche de forma bloqueante
    router_socket.bind(router.address)

    while True:
        paquete, direccion = router_socket.recvfrom(1024)

        # primero revisamos si el ttl es >0
        if paquete[6] <= 0:
            print(f"Se recibió paquete {paquete} con TTL 0")
            continue

        data_packet = router.parse_packet(paquete)
        print("Paquete recibido: ", data_packet, " desde: ", direccion)

        destination_address: tuple[str, int] = (data_packet.ip, data_packet.puerto)

        # 7. El router checkea si el paquete es para él.
        # Un router es el par (IP, puerto), así que se comparan ambos.
        if destination_address == router.address:
            print(data_packet.mensaje)
        else:
            direccion_next_hop, mtu_next_hop = router.check_routes(router_rutas_path, destination_address)
            if direccion_next_hop is not None:
                print(f"redirigiendo paquete {paquete} con destino final {destination_address} desde {router.address} hacia {direccion_next_hop}")
                # actualiuzamos el ttl del paquete antes de reenviarlo
                data_packet.ttl -= 1
                # forward: se envía con el mismo socket del router (no se hace bind de nuevo)
                router_socket.sendto(router.create_packet(data_packet), direccion_next_hop)
            else:
                print(f"No hay rutas hacia {destination_address} para paquete {paquete}")
