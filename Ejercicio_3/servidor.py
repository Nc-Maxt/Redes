import socket
from SocketTCP import *



if __name__ == "__main__":
    # definimos el tamaño del buffer de recepción y la secuencia de fin de mensaje
    buff_size = 1024
    new_socket_address = ('localhost', 5000)

    print('Creando socket - Servidor')
    # armamos el socket
    # los parámetros que recibe el socket indican el tipo de conexión
    # socket.SOCK_DGRAM = socket NO orientado a conexión
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # ESTO ABRE EL SOCKET PARA QUE PUEDA RECIBIR DATOS EN LA DIRECCION Y PUERTO INDICADOS
    server_socket.bind(new_socket_address)

    # En este caso, como es un socket NO orientado a conexión, no usamos listen ni accept
    
    # nos quedamos esperando a que llegue un mensaje
    print('... Esperando clientes')
    while True:
        # En vez de aceptar una conexión, recibimos un mensaje desde el socket
        # la función recvfrom entrega una tupla con el mensaje y la dirección del cliente
        recv_message, client_address = server_socket.recvfrom(buff_size)
        ns = SocketTCP()
        red = ns.parse_segment(recv_message)

        print(f'{red[b"body"].decode()}')