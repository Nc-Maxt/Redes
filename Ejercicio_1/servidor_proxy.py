import socket
import protocolos as proto
import json
import sys


def it_receive_full_message(connection_socket, buff_size) -> bytes:

    head = b""
    ciclos = 0 #contador de ciclos para leer respuestas


    # iteramos hasta encontrar el body
    while head.find(b"\r\n\r\n") == -1:
        recv_message = connection_socket.recv(buff_size)
        ciclos +=1
        head += recv_message

    #separamos head del body por el doble salto de linea
    head, body = head.split(b"\r\n\r\n", 1)

    #para el head, separaremos cada línea
    head_lines = head.split(b"\r\n")

    # guardamos el contador de las cosas
    C_length = 0

    # Luego encontraremos el header de Content-Length para saber si nos faltan bytes que leer
    for line in head_lines[1:]:
        if (line.find(b"Content-Length:")!=-1):
            _, value = line.split(b":")
            C_length = value.decode()

    # entramos a un while para recibir el resto y seguimos esperando información
    # mientras que el tamano del body no sea el largo declarado
    if int(C_length) > 0:
        while not (int(C_length) == len(body)):
            # recibimos un nuevo trozo del mensaje
            recv_message = connection_socket.recv(buff_size)

            # lo añadimos al mensaje "completo"
            body += recv_message
            ciclos+=1

    full = head+b"\r\n\r\n"+body
    # finalmente retornamos el mensaje en bytes
    print(f"Se necesitaron {ciclos} ciclos.")
    return full

# empaquetamos el receive message iterativo para parsear el mensaje HTTP y devolver un diccionario
def receive_mes(connection_socket, buff_size) -> dict:
    full_message=it_receive_full_message(connection_socket, buff_size)
    full_message=proto.parse_HTTP_message(full_message)

    return full_message


if __name__ == "__main__":

    path_prohibidos = sys.argv[1]
    print(path_prohibidos)
    # definimos el tamaño del buffer de recepción y el socket donde estaremos escuchando
    # cuando el proxy actue como servidor
    buff_size = 50
    new_socket_address = ('172.20.10.3', 5003)

    print('Creando sockets - Socket server')
    # armamos los sockets, uno es para el cliente y el otro para el servidor.
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #este es el que sirve al cliente
    ################
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ################


    # le indicamos al server socket que debe atender peticiones en la dirección address
    # para ello usamos bind
    server_socket.bind(new_socket_address)

    # luego con listen (función de sockets de python)
    server_socket.listen(10)

    # nos quedamos esperando a que llegue una petición de conexión
    print('... Esperando clientes')
    while True:
        print("Nueva peticion: ")
        print('Creando sockets - Socket cliente')
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #este hace el request al server
        # cuando llega una petición de conexión la aceptamos
        # y se crea un nuevo socket que se comunicará con el cliente
        new_socket, new_socket_address = server_socket.accept()

        # luego recibimos el mensaje usando la función que programamos
        # esta función entrega el mensaje comoo un diccionario en bytes
        recv_message = receive_mes(new_socket, buff_size)
        # el cliente nos envio un mensaje con el host al que quiere conectarse, y al cual, como proxy, tenemos que hacerle una request
        # la ruta viene como URI absoluta (http://example.com/loquesea), asi que le sacamos
        # el esquema y despues separamos el host de la ruta en el primer "/"
        uri = recv_message[b"path"].decode()
        # si no viene el esquema, partition deja el separador vacio y el "antes" es la uri
        # completa, asi que en ese caso nos quedamos con la uri tal cual
        _, sep, resto = uri.partition("://")
        if sep == "":
            resto = uri
        host, _, ruta = resto.partition("/") #algo.com, /, otracosa

        address = (host, 80)
        recv_message[b"path"] = ("/" + ruta).encode()

        with open(path_prohibidos) as file:
            # usamos json para manejar los datos
            data_json = json.load(file)
            prohibidos = data_json["blocked"]
            censura = data_json["forbidden_words"]
            elquepregunta = data_json["user"]

        html = open('assets/respuesta.html', 'r').read()

        if resto in prohibidos:
            response_dict = {
                b"version": b"HTTP/1.1",
                b"response": b"403",
                b"reason": b"OK",
                b"Content-Type": b"text/html; charset=utf-8",
                b"Content-Length": str(len(html.encode())).encode(),
                b"Connection": b"keep-alive",
                b"Access-Control-Allow-Origin": b"*",
                b"body": html.encode(),
            }
            response_message2 = proto.create_HTTP_message(response_dict)

        else:

            #el client socket tiene que solicitar conectarse al server
            client_socket.connect(address)

            # armamos la response HTTP como diccionario, siguiendo el mismo formato que entrega parse_HTTP_message, y usamos create_HTTP_message para
            # convertirla a bytes (status line + headers + body)
            recv_message[b"X-ElQuePregunta"] = elquepregunta.encode() #anado header personalizado a la request que mando al server.

            response_message = proto.create_HTTP_message(recv_message)

            print(f"MENSAJE QUE VAMOS A HACERLE ECHO: {response_message}")

            # create_HTTP_message ya retorna bytes, no hace falta volver a encode
            client_socket.send(response_message)
            recv_message2 = receive_mes(client_socket, buff_size)


            # ahora veremos si es que hay palabras prohibidas en el body
            for pair in censura:
                for key in pair:
                    mess_body = recv_message2[b"body"]
                    new_body = mess_body.replace(key.encode(),pair[key].encode().strip())
                    recv_message2[b'body'] = new_body

            # al censurar cambiamos el largo del body, asi que el Content-Length
            # que venia del server ya no sirve y hay que recalcularlo
            recv_message2[b"Content-Length"] = str(len(recv_message2[b"body"])).encode()

            response_message2 = proto.create_HTTP_message(recv_message2)

            print(f"MENSAJE QUE recibimos DE VUELTA: {response_message2}")
            client_socket.close()

        # y ahora hacemos echo de lo que nos respondio el server, o bien de nuestro mensaje de error.
        new_socket.send(response_message2)

        # cerramos la conexión
        # notar que la dirección que se imprime indica un número de puerto distinto al 5000
        new_socket.close()
        print(f"conexión con {new_socket_address} ha sido cerrada")

        # seguimos esperando por si llegan otras conexiones
