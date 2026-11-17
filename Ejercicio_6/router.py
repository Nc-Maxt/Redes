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
    mensaje: bytes  # contenido, ej: b"hola"

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
        Id = int.from_bytes(IP_packet[11:13], "big")       # 2 bytes -> int
        Offset = int.from_bytes(IP_packet[13:17], "big")   # 4 bytes -> int
        Flag = int.from_bytes(IP_packet[17:18], "big")     # 1 byte -> int

        mensaje = IP_packet[18:]                           # resto -> bytes
        return Paquete(ip, puerto, ttl, size, Id, Offset, Flag, mensaje)

    # Paquete -> bytes
    def create_packet(self, parsed_IP_packet: Paquete) -> bytes:
        ip_bytes = bytes(int(n) for n in parsed_IP_packet.ip.split("."))  # "a.b.c.d" -> 4 bytes
        puerto_bytes = parsed_IP_packet.puerto.to_bytes(2, "big")         # int -> 2 bytes
        ttl_bytes = parsed_IP_packet.ttl.to_bytes(1, "big")               # int -> 1 byte
        size_bytes = parsed_IP_packet.tamaño.to_bytes(4, "big")           # int -> 4 bytes
        Id_bytes = parsed_IP_packet.Id.to_bytes(2, "big")                 # int -> 2 bytes
        Offset_bytes = parsed_IP_packet.Offset.to_bytes(4, "big")         # int -> 4 bytes
        Flag_bytes = parsed_IP_packet.Flag.to_bytes(1, "big")             # int -> 1 byte

        mensaje_bytes = parsed_IP_packet.mensaje                          # bytes -> bytes
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

    def fragment_IP_packet(self, IP_packet, MTU):
        # Retorna lista que contiene los fragmentos del paquete IP original
        largo = IP_packet.tamaño
        if largo+18 <= MTU:  # 18 es el tamaño del header IP
            return [IP_packet]
        else:
            new_size = MTU - 18
            num_fragmentos = largo // new_size
            if largo % new_size != 0:
                num_fragmentos += 1
            fragmentos = []
            offset = IP_packet.Offset
            for i in range(num_fragmentos):
                if i == num_fragmentos - 1:
                    fragment = Paquete(ip=IP_packet.ip, puerto=IP_packet.puerto, ttl=IP_packet.ttl, tamaño=largo - new_size * i, 
                                       Id=IP_packet.Id, Offset=offset, Flag=IP_packet.Flag, mensaje=IP_packet.mensaje[i*new_size:])

                else:
                    fragment = Paquete(ip=IP_packet.ip, puerto=IP_packet.puerto, ttl=IP_packet.ttl, tamaño=new_size, 
                                   Id=IP_packet.Id, Offset=offset, Flag=1, mensaje=IP_packet.mensaje[i*new_size:(i+1)*new_size])
                    offset += new_size
                fragmentos.append(fragment)
            return fragmentos

    def reassemble_IP_packet(self, fragment_list):

        if len(fragment_list) == 1:
            pkg = fragment_list[0]
            if (pkg.Flag == 0) and (pkg.Offset == 0):
                return pkg
            else:
                return None
        else:
            # Ordenar los fragmentos por Offset
            fragment_list.sort(key=lambda x: x.Offset)
            if fragment_list[0].Offset != 0:
                return None
            if fragment_list[-1].Flag != 0:
                return None
            # Verificar que los fragmentos estén completos y en orden
            for i in range(len(fragment_list) - 1):
                if fragment_list[i].Offset + fragment_list[i].tamaño != fragment_list[i + 1].Offset:
                    return None
            
            # Crear un nuevo paquete IP con los datos reensamblados
            mensaje_reensamblado = b''.join([fragment.mensaje for fragment in fragment_list])
            paquete_reensamblado = Paquete(ip=fragment_list[0].ip, puerto=fragment_list[0].puerto, ttl=fragment_list[0].ttl, tamaño=len(mensaje_reensamblado),
                                           Id=fragment_list[0].Id, Offset=0, Flag=0, mensaje=mensaje_reensamblado)
            return paquete_reensamblado


            


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
    router_dicc = {}

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
            if data_packet.Id not in router_dicc:
                router_dicc[data_packet.Id] = []
            else:
                router_dicc[data_packet.Id].append(data_packet)
            print(f"El paquete {data_packet} es para este router {router.address}")

        else:
            direccion_next_hop, mtu_next_hop = router.check_routes(router_rutas_path, destination_address)
            if direccion_next_hop is not None:
                fragmented_packets = router.fragment_IP_packet(data_packet, mtu_next_hop)
                for pkg in fragmented_packets:
                    print(f"redirigiendo paquete {pkg} con destino final {destination_address} desde {router.address} hacia {direccion_next_hop}")
                    # actualiuzamos el ttl del paquete antes de reenviarlo
                    pkg.ttl -= 1
                    # forward: se envía con el mismo socket del router (no se hace bind de nuevo)
                    router_socket.sendto(router.create_packet(pkg), direccion_next_hop)
            else:
                print(f"No hay rutas hacia {destination_address} para paquete {paquete}")
