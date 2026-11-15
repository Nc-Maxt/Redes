# Script paso 5. Permite enviar mensajes en el formato correcto hacia cualquier dirección.

import sys
import router
import socket

IP_router_final: str = sys.argv[1] #ip de destino
IP_router_final_bytes = bytes(map(int, IP_router_final.split(".")))
print(IP_router_final_bytes)
puerto_router_final: int = int(sys.argv[2]) #router de destino
IP_envío: str = sys.argv[3] #ip de inicio
puerto_envío: int = int(sys.argv[4]) #puerto inicio

mensaje_a_enviar:str = input("Mensaje a enviar: ")

paquete_a_enviar = router.Paquete(IP_router_final_bytes, puerto_router_final.to_bytes(2), mensaje_a_enviar.encode())
print(paquete_a_enviar)
paquete_bytes = router.create_packet(paquete_a_enviar) #lo paso a bytes

#creo el socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
address = (IP_envío, puerto_envío)

client_socket.sendto(paquete_bytes, address) #envio el paquete a la direccion de envio
#y mi paquete adentro tiene la direccion final.
