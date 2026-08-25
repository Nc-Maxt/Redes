import socket
import protocolos as proto
import json
import sys


def it_receive_full_message(connection_socket, buff_size) -> bytes:

    # recibimos la primera parte del mensaje
    first_message = connection_socket.recv(buff_size)
    
    #separamos head del body por el doble salto de linea
    head, body = first_message.split(b"\r\n\r\n")
    
    #para el head, separaremos cada línea
    head_lines = head.split(b"\r\n")

    # guardamos el contador de las cosas
    C_length = 0

    # Luego encontraremos el header de Content-Length para saber si nos faltan bytes que leer
    for line in head_lines[1:]:
        if (line.find(b"Content-Length:")!=-1):
            key, value = line.split(b":")
            C_length = value.decode()            

    # entramos a un while para recibir el resto y seguimos esperando información
    # mientras que el tamano del body no sea el largo declarado
    while not (int(C_length) == len(body)):
        # recibimos un nuevo trozo del mensaje
        recv_message = connection_socket.recv(buff_size)
        
        # lo añadimos al mensaje "completo"
        body += recv_message

    full = head+b"\r\n\r\n"+body
    # finalmente retornamos el mensaje en bytes
    return full

# empaquetamos el receive message iterativo para parsear el mensaje HTTP y devolver un diccionario
def receive_mes(connection_socket, buff_size) -> dict:
    full_message=it_receive_full_message(connection_socket, buff_size)
    full_message=proto.parse_HTTP_message(full_message)

    return full_message


if __name__ == "__main__":

    path_prohibidos = str(sys.args[0])
    # definimos el tamaño del buffer de recepción y el socket donde estaremos escuchando
    # cuando el proxy actue como servidor
    buff_size = 1024
    new_socket_address = ('localhost', 5003)

    print('Creando sockets - Socket server')
    # armamos los sockets, uno es para el cliente y el otro para el servidor. 
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #este es el que sirve al cliente
    ################
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ################
    
    print('Creando sockets - Socket cliente')
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #este hace el request al server

    # le indicamos al server socket que debe atender peticiones en la dirección address
    # para ello usamos bind
    server_socket.bind(new_socket_address) 

    # luego con listen (función de sockets de python)
    server_socket.listen(10)

    # nos quedamos esperando a que llegue una petición de conexión
    print('... Esperando clientes')
    while True:
        # cuando llega una petición de conexión la aceptamos
        # y se crea un nuevo socket que se comunicará con el cliente
        new_socket, new_socket_address = server_socket.accept()
        
        # luego recibimos el mensaje usando la función que programamos
        # esta función entrega el mensaje comoo un diccionario en bytes
        recv_message = receive_mes(new_socket, buff_size)
        # el cliente nos envio un mensaje con el host al que quiere conectarse, y al cual, como proxy, tenemos que hacerle una request
        host = recv_message["ruta"].decode()
        _, host = host.split("://",1)
        host = host[:-1]
        address = (host, 80)
        recv_message["ruta"] = b"/" 

        with open(path_prohibidos) as file:
            # usamos json para manejar los datos
            data = json.load(file)
            prohibidos = []
            # leemos cada linea de los valores
            for key,value in data:
                prohibidos.append(value)

        html = open('respuesta.html', 'r').read()

        if host in prohibidos["blocked"]:
            response_dict = {
                "versión": "HTTP/1.1",
                "código": "403",
                "razón": "OK",
                "Content-Type": "text/html; charset=utf-8",
                "Content-Length": str(len(html.encode())),
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "body": html,
            }
            response_message2= = proto.create_HTTP_message(response_dict)

        else:

            #el client socket tiene que solicitar conectarse al server
            client_socket.connect(address)
                
            # armamos la response HTTP como diccionario, siguiendo el mismo formato que entrega parse_HTTP_message, y usamos create_HTTP_message para
            # convertirla a bytes (status line + headers + body)
            response_message = proto.create_HTTP_message(recv_message)
            print(f"MENSAJE QUE VAMOS A HACERLE ECHO: {response_message}")

            # create_HTTP_message ya retorna bytes, no hace falta volver a encode
            client_socket.send(response_message)
            response_message2 = receive_mes(client_socket, buff_size)

            print(f"MENSAJE QUE recibimos DE VUELTA: {response_message2}")

        # y ahora hacemos echo de lo que nos respondio el server, o bien de nuestro mensaje de error. 
        server_socket.send(response_message2)

        # cerramos la conexión
        # notar que la dirección que se imprime indica un número de puerto distinto al 5000
        new_socket.close()
        #print(f"conexión con {new_socket_address} ha sido cerrada")

        # seguimos esperando por si llegan otras conexiones
