import socket
import protocolos as proto
import json


def it_receive_full_message(connection_socket, buff_size):

    # recibimos la primera parte del mensaje
    first_message = connection_socket.recv(buff_size)

    # Modificar todo esto para que lo saque con find, buscamos el content lenght
    print(first_message)
    print(first_message.split(b"\r\n\r\n"))
    head, body = first_message.split(b"\r\n\r\n")
    
    #para el head, separaremos cada línea
    head_lines = head.split(b"\r\n")

    # guardamos el contador de las cosas
    C_length = 0

    # Luego con cada línea se hace una llave y un valor, separando la clave del valor por el primer ":"
    for line in head_lines[1:]:
        if (line.find(b"Content_Lenght")!=-1):
            print(line)
            key, value = line.split(b":")
            C_length = value.decode()
            break

    # entramos a un while para recibir el resto y seguimos esperando información
    # mientras el buffer no contenga secuencia de fin de mensaje
    while not (C_length == len(body)):
        # recibimos un nuevo trozo del mensaje
        recv_message = connection_socket.recv(buff_size)

        # lo añadimos al mensaje "completo"
        body += recv_message

    # finalmente retornamos el mensaje
    return head+b"\r\n\r\n"+body

def receive_mes(connection_socket, buff_size):
    full_message=it_receive_full_message(connection_socket, buff_size)
    full_message=proto.parse_HTTP_message(full_message)

    return full_message


if __name__ == "__main__":
    # definimos el tamaño del buffer de recepción y la secuencia de fin de mensaje
    buff_size = 1024
    end_of_message = "\r\n\r\n" #http eol
    #host = input('Ingrese el host: ')
    #new_socket_address = (f'{host}', 80)
    address_cliente = ('localhost', 5003)

    print('Creando socket - Proxy')
    # armamos los sockets, uno es para el cliente y el otro para el servidor. 
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #este es el que sirve al cliente
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #este hace el request al server

    # le indicamos al server socket que debe atender peticiones en la dirección address
    # para ello usamos bind
    server_socket.bind(address_cliente) 

    # luego con listen (función de sockets de python) le decimos que puede
    # tener hasta 3 peticiones de conexión encoladas
    # si recibiera una 4ta petición de conexión la va a rechazar
    server_socket.listen(10)

    # nos quedamos esperando a que llegue una petición de conexión
    print('... Esperando clientes')
    while True:
        # cuando llega una petición de conexión la aceptamos
        # y se crea un nuevo socket que se comunicará con el cliente
        new_socket, new_socket_address = server_socket.accept()

        # luego recibimos el mensaje usando la función que programamos
        # esta función entrega el mensaje comoo un diccionario en bytes
        recv_message = receive_mes(new_socket, buff_size, end_of_message)
        host = recv_message["ruta"]
        print(host)
        print(recv_message) 

        #print(f' -> Se ha recibido el siguiente mensaje: {recv_message}')

        #html = open('respuesta.html', 'r').read()

        #######
        #el client socket tiene que solicitar conectarse al server
        client_socket.connect(f"{host}", 80)
        #######

        with open("prohibidos.json") as file:
            # usamos json para manejar los datos
            data = json.load(file)
            # leemos cada linea de los valores
            nombre = data["nombre"]

        # armamos la response HTTP como diccionario, siguiendo el mismo formato que entrega parse_HTTP_message, y usamos create_HTTP_message para
        # convertirla a bytes (status line + headers + body)
        response_message = proto.create_HTTP_message(recv_message)
        #print(response_message.decode())

        # create_HTTP_message ya retorna bytes, no hace falta volver a encode
        client_socket.send(response_message)
        response_message2 = receive_mes(client_socket, buff_size, end_of_message)

        # cerramos la conexión
        # notar que la dirección que se imprime indica un número de puerto distinto al 5000
        new_socket.close()
        #print(f"conexión con {new_socket_address} ha sido cerrada")

        # seguimos esperando por si llegan otras conexiones
