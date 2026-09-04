import socket
import protocolos as po

print('Creando socket - resolver')

# armamos el socket, los parámetros que recibe el socket indican el tipo de conexión
# socket.SOCK_DGRAM = socket NO orientado a conexión
resolver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Como buscamos ver mensajes DNS necesitamos un socket NO orientado a conexión 
address = ('localhost', 8000)

# ESTO ABRE EL SOCKET PARA QUE PUEDA RECIBIR DATOS EN LA DIRECCION Y PUERTO INDICADOS
resolver_socket.bind(address)
buffer_size = 4096

# nos quedamos esperando a que llegue un mensaje
print('... Esperando clientes')
while True:
    # En vez de aceptar una conexión, recibimos un mensaje desde el socket
    # la función recvfrom entrega una tupla con el mensaje y la dirección del cliente
    recv_message, client_address = resolver_socket.recvfrom(buffer_size)
    print(f' -> Se ha recibido el siguiente mensaje: {recv_message}')

    info = po.resolver(recv_message)
    print("mensaje para enviar devuelta al cliente es")
    print(info)
    resolver_socket.sendto(info, client_address)
    