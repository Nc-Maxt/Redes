import socket

# esta función se encarga de recibir el mensaje completo desde el cliente en caso de que el mensaje sea más grande
#  que el tamaño del buffer 'buff_size', esta función va esperar a que # llegue el resto. Para saber si el 
# mensaje ya llegó por completo, se busca el caracter de fin de mensaje (parte de nuestro protocolo inventado)
# podría ser que recibimos el mensaje desordenado, en este caso no lo ordenamos por simplicidad
# puede darse el caso de que el final del mensaje llegue antes que el resto de partes y finalizará (posteriormente se abordará solución)

def receive_full_message(buff_size, end_sequence):

    # recibimos la primera parte del mensaje
    recv_message, client_address = server_socket.recvfrom(buff_size)
    full_message = recv_message

    # verificamos si llegó el mensaje completo o si aún faltan partes del mensaje
    is_end_of_message = contains_end_of_message(full_message.decode(), end_sequence)

    # entramos a un while para recibir el resto y seguimos esperando información
    # mientras el buffer no contenga secuencia de fin de mensaje
    while not is_end_of_message:
        # recibimos un nuevo trozo del mensaje
        recv_message, client_address = server_socket.recvfrom(buff_size)

        # lo añadimos al mensaje "completo"
        full_message += recv_message

        # verificamos si es la última parte del mensaje
        is_end_of_message = contains_end_of_message(full_message.decode(), end_sequence)

    # removemos la secuencia de fin de mensaje, esto entrega un mensaje en string
    full_message = remove_end_of_message(full_message.decode(), end_sequence)

    # finalmente retornamos el mensaje
    return full_message, client_address


def contains_end_of_message(message, end_sequence):
    return message.endswith(end_sequence)


def remove_end_of_message(full_message, end_sequence):
    index = full_message.rfind(end_sequence)
    return full_message[:index]

if __name__ == "__main__":
    # definimos el tamaño del buffer de recepción y la secuencia de fin de mensaje
    buff_size = 1024
    end_of_message = "\n"
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
        recv_message, client_address = receive_full_message(buff_size, end_of_message)

        print(f' -> Se ha recibido el siguiente mensaje: {recv_message}')

        # respondemos indicando que recibimos el mensaje
        response_message = recv_message

        # el mensaje debe pasarse a bytes antes de ser enviado, para ello usamos encode
        server_socket.sendto(response_message.encode(), client_address)

        # recordar que no hay conexiones en este por lo cual
        # seguimos esperando por si llegan otras conexiones