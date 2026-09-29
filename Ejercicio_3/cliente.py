import socket
import os
import sys
from SocketTCP import *

print('Creando socket - Cliente')

# armamos el socket, los parámetros que recibe el socket indican el tipo de conexión
# socket.SOCK_DGRAM = socket NO orientado a conexión
client_socketTCP = SocketTCP()

# Como queremos hacer un socket TCP debemos hacer el 3 way handshake
address = ('localhost', 5000)
client_socketTCP.connect(address)
n_address = client_socketTCP.connection

message = input("Escribir la dirección del archivo a enviar: ")
print(f"Escribiste: {message}")

if not os.path.isabs(message):
    directorio_actual = os.getcwd()
    ruta_completa = os.path.join(directorio_actual, message)
else:
    ruta_completa = message

# abrimos el archivo en modo lectura binaria para poder enviar 
# cualquier tipo de archivo (texto, imagen, video, etc.)
archivo = open(ruta_completa, "rb")
send_message = archivo.read()
archivo.close()

puntero = 0
# Enviamos el mensaje en trozos de a lo más n=16 bytes
while puntero < len(send_message):
    # se define el tamaño de los trozos a enviar
    chunck_s = 16
    # se obtiene el trozo a enviar
    if puntero + chunck_s > len(send_message):
        chunck = send_message[puntero:]
    else:
        chunck = send_message[puntero:puntero + chunck_s]

    # se parsea como mensaje con headers
    pack = {
                b"m_type": b"",
                b"m_len": str(chunck_s).encode(),
                b"m_seq": str(1).encode(),
                b"body": chunck
            }
    
    red = client_socketTCP.create_segment(pack)
    client_socketTCP.socket_UDP.sendto(red, n_address)

    #actualizo el puntero para el siguiente trozo
    puntero += chunck_s

print("... Mensaje enviado")

#
## Finalmente esperamos una respuesta
## Para ello debemos definir el tamaño del buffer de recepción
#buffer_size = 1024
#message, server_address = client_socket.recvfrom(buffer_size)
#
## Pasamos el mensaje de bytes a string
#decoded_message = message.decode()
#
#print(f' -> Respuesta del servidor: {decoded_message}')
#
## cerramos la conexión
#print(f"conexión con {client_socket.getsockname()}")
#client_socket.close()
#print("ha sido cerrada")
