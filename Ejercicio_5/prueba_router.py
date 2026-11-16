# Test del paso 4, parte 2: prueba que lee un archivo linea por linea
# con las tablas de los ejemplos mayores a 3 routers.
import sys
import socket
import router

headers = sys.argv[1]                     # header IP;puerto;ttl
Ip_router_inicial = sys.argv[2]           # IP del router inicial
puerto_router_inicial = int(sys.argv[3])  # puerto del router inicial

heds = headers.split(";")
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

with open("ejemplo.txt", "r", encoding="utf-8") as archivo:
    for linea in archivo:
        mensaje = linea.rstrip("\n")
        paquete_a_enviar = router.Paquete(heds[0], int(heds[1]), int(heds[2]), mensaje)

        paquete_bytes = router.Router.create_packet(None, paquete_a_enviar)
        print("Enviando:", paquete_a_enviar, "->", paquete_bytes)

        client_socket.sendto(paquete_bytes, (Ip_router_inicial, puerto_router_inicial))
client_socket.close()
