# Script paso 5. Permite enviar mensajes en el formato correcto hacia cualquier dirección.
#
# Uso:
#   python3 sender.py IP_router_final puerto_router_final IP_envío puerto_envío
# Luego el script pide el mensaje por teclado.
#
# - (IP_router_final, puerto_router_final): destino FINAL, va dentro del header del paquete.
# - (IP_envío, puerto_envío): router al que se le entrega el paquete ahora (primer salto).

import sys
import socket
import router

IP_router_final: str = sys.argv[1]        # IP de destino final (va en el header)
puerto_router_final: int = int(sys.argv[2])  # puerto de destino final (va en el header)
IP_envío: str = sys.argv[3]               # IP del router al que se envía el paquete
puerto_envío: int = int(sys.argv[4])      # puerto del router al que se envía el paquete
ttl: int = int(sys.argv[5])               # ttl del paquete

mensaje_a_enviar: str = input("Mensaje a enviar: ")

# La conversión a bytes la hace create_packet
paquete_a_enviar = router.Paquete(IP_router_final, puerto_router_final, ttl, mensaje_a_enviar)
paquete_bytes = router.Router.create_packet(None, paquete_a_enviar)
print("Enviando:", paquete_a_enviar, "->", paquete_bytes)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.sendto(paquete_bytes, (IP_envío, puerto_envío))
client_socket.close()
