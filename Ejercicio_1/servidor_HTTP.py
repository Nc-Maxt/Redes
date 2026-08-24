import socket
import protocolos as proto


# esta función se encarga de recibir el mensaje completo desde el cliente
# en caso de que el mensaje sea más grande que el tamaño del buffer 'buff_size', esta función va esperar a que
# llegue el resto. Para saber si el mensaje ya llegó por completo, se busca el caracter de fin de mensaje (parte de nuestro protocolo inventado)

def receive_full_message(connection_socket, buff_size, end_sequence):

    # recibimos la primera parte del mensaje
    recv_message = connection_socket.recv(buff_size)
    full_message = recv_message

    # verificamos si llegó el mensaje completo o si aún faltan partes del mensaje
    # lo hacemos sin decodear, aun en bytes
    is_end_of_message = contains_end_of_message(full_message.decode(), end_sequence)

    # entramos a un while para recibir el resto y seguimos esperando información
    # mientras el buffer no contenga secuencia de fin de mensaje
    while not is_end_of_message:
        # recibimos un nuevo trozo del mensaje
        recv_message = connection_socket.recv(buff_size)

        # lo añadimos al mensaje "completo"
        full_message += recv_message

        # verificamos si es la última parte del mensaje
        # lo hacemos sin decodear, aun en bytes
        is_end_of_message = contains_end_of_message(full_message.decode(), end_sequence)

    print(full_message)
    # parseamos el mensaje
    full_message = proto.parse_HTTP_message(full_message)
    print(full_message)
    full_message = proto.create_HTTP_message(full_message)
    print("CREATE HTTP: ", full_message)

    # removemos la secuencia de fin de mensaje, esto entrega un mensaje en string
    full_message = remove_end_of_message(full_message.decode(), end_sequence)

    # finalmente retornamos el mensaje
    return full_message


def contains_end_of_message(message, end_sequence):
    return message.endswith(end_sequence)


def remove_end_of_message(full_message, end_sequence):
    index = full_message.rfind(end_sequence)
    return full_message[:index]

if __name__ == "__main__":
    # definimos el tamaño del buffer de recepción y la secuencia de fin de mensaje
    buff_size = 1024
    end_of_message = "\r\n\r\n" #http eol
    host = input('Ingrese el host: ')
    new_socket_address = (f'{host}', 80)

    print('Creando socket - Servidor')
    # armamos el socket
    # los parámetros que recibe el socket indican el tipo de conexión
    # socket.SOCK_STREAM = socket orientado a conexión
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # le indicamos al server socket que debe atender peticiones en la dirección address
    # para ello usamos bind
    server_socket.bind(new_socket_address)

    # luego con listen (función de sockets de python) le decimos que puede
    # tener hasta 3 peticiones de conexión encoladas
    # si recibiera una 4ta petición de conexión la va a rechazar
    server_socket.listen(3)

    # nos quedamos esperando a que llegue una petición de conexión
    print('... Esperando clientes')
    while True:
        # cuando llega una petición de conexión la aceptamos
        # y se crea un nuevo socket que se comunicará con el cliente
        new_socket, new_socket_address = server_socket.accept()

        # luego recibimos el mensaje usando la función que programamos
        # esta función entrega el mensaje en string (no en bytes) y sin el end_of_message
        recv_message = receive_full_message(new_socket, buff_size, end_of_message)

        print(f' -> Se ha recibido el siguiente mensaje: {recv_message}')

        html = open('respuesta.html', 'r').read()

        # armamos la response HTTP como diccionario, siguiendo el mismo formato que entrega parse_HTTP_message, y usamos create_HTTP_message para
        # convertirla a bytes (status line + headers + body)
        response_dict = {
            "versión": "HTTP/1.1",
            "código": "200",
            "razón": "OK",
            "Content-Type": "text/html; charset=utf-8",
            "Content-Length": str(len(html.encode())),
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "X-ElQuePregunta": "paul0li",
            "body": html,
        }
        response_message = proto.create_HTTP_message(response_dict)

        # create_HTTP_message ya retorna bytes, no hace falta volver a encode
        new_socket.send(response_message)

        # cerramos la conexión
        # notar que la dirección que se imprime indica un número de puerto distinto al 5000
        new_socket.close()
        print(f"conexión con {new_socket_address} ha sido cerrada")

        # seguimos esperando por si llegan otras conexiones
