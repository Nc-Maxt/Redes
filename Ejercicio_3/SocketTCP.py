# archivo donde se creará la clase SpcketTCP, que implementa un socket TCP para enviar y recibir mensajes
import random
import socket

class SocketTCP:
    def __init__(self):
        self.socket_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address = None
        self.connection = None
        self.sequence = None
        self.options = [b"ACK", b"SYN", b"ACK+SYN", b"FIN", b"ACK+FIN"]
        self.timeout = 5

    def set_connection(self, connection):
        self.connection = connection

    def set_timeout(self, timeout):
            self.timeout = timeout

    def set_sequence(self, sequence):
        self.sequence = sequence

    def get_sequence(self):
        return self.sequence

    def increment_sequence(self, value):
        self.sequence += value

    @staticmethod
    def parse_segment(segment):
        # parsea el segmento recibido y devuelve el mensaje y la dirección del cliente
        # separamos header de body
        head, body = segment.split(b"\r\n\r\n", 1)

        #para el head, separaremos cada línea
        head_lines = head.split(b"\r\n")
        # La estructura a usar será un diccionario
        TCP_dict = {}
        # Luego con cada línea se hace una llave y un valor, separando la clave del valor por el primer ":"
        for line in head_lines:
            key, value = line.split(b":", 1)
            # se usa strip para eliminar espacios en blanco al inicio y al final
            TCP_dict[key.strip()] = value.strip()
        TCP_dict[b"body"] = body
        return TCP_dict

    @staticmethod
    def create_segment(tcp_dict):
        # crea un segmento a partir del mensaje
        msg_type =   b"m_type: " + tcp_dict[b"m_type"] + b"\r\n"
        length =   b"m_len: " + tcp_dict[b"m_len"] + b"\r\n"
        seq = b"m_seq: " + tcp_dict[b"m_seq"] + b"\r\n\r\n"
        body = tcp_dict[b"body"]
        segment = msg_type + length + seq + body
        return segment

    def bind(self, address):
        self.socket_UDP.bind(address)
        self.address = address

    def connect(self, address):
        # generamos un número aleatorio para la secuencia inicial
        n = random.randint(0, 100)
        print(n)
        # creamos el diccionario para luego crear el segmento SYN y enviarlo al servidor
        ini_dict = {
            b"m_type": b"SYN",
            b"m_len": b"0",
            b"m_seq": str(n).encode(),
            b"body": b""
        }
        segment = self.create_segment(ini_dict)
        print(f"intentando conectar con {address}")
        self.socket_UDP.sendto(segment, address)

        # esperamos a que llegue el SYN+ACK del servidor
        print(f"Esperando mensaje devuelta de {address}")
        segment, info_add = self.socket_UDP.recvfrom(1024)
        tcp_dict = self.parse_segment(segment)
        # verificamos que la secuencia recibida sea la correcta y que la ip sea la misma a la que le enviamos el SYN
        # el puerto debería ser distinto, ya que el servidor nos asigna un puerto aleatorio para la conexión 
        if (tcp_dict[b"m_type"] == b"SYN+ACK") and (int(tcp_dict[b"m_seq"].decode()) == n + 1):
            # obtenemos la secuencia del servidor y le sumamos 1 para enviar el ACK
            seq = int(tcp_dict[b"m_seq"].decode()) + 1
            self.sequence = seq
            ack_dict = {
                b"m_type": b"ACK",
                b"m_len": b"0",
                b"m_seq": str(seq).encode(),
                b"body": b""
            }
            segment = self.create_segment(ack_dict)
            print(f"Mandamos mensaje devuelta a {info_add}")
            self.socket_UDP.sendto(segment, info_add)
            # guardamos la dirección del servidor para luego enviarle los mensajes
            self.set_connection(info_add)
            print(f"Conexión establecida con {info_add[0]}:{info_add[1]}")

    def accept(self):
        # esperamos a que llegue un segmento SYN del cliente
        print(f"Esperando mensaje de clientes")
        segment, client_address = self.socket_UDP.recvfrom(1024)
        # parseamos el segmento recibido
        tcp_dict = self.parse_segment(segment)
        if tcp_dict[b"m_type"] == b"SYN":
            # obtenemos la secuencia del cliente y le sumamos 1 para enviar el SYN+ACK
            seq = int(tcp_dict[b"m_seq"].decode()) +1

            # establecemos un nuevo socket TCP para la conexión con el cliente
            nuevo_socket = SocketTCP()
            # configuramos el nuevo socket con la dirección del cliente, la secuencia y la dirección final
            nuevo_socket.set_connection(client_address)
            nuevo_socket.set_sequence(seq)
            puerto = random.randint(1000, 9999)
            print(f"Se bindea el nuevo puerto {(self.address[0], puerto)}")
            nuevo_socket.bind((self.address[0], puerto))

            # creamos el diccionario para luego crear el segmento SYN+ACK y enviarlo al cliente
            ini_dict = {
                b"m_type": b"SYN+ACK",
                b"m_len": b"0",
                b"m_seq": str(seq).encode(),
                b"body": b""
            }
            print(ini_dict)
            segment = nuevo_socket.create_segment(ini_dict)
            print(f"Le respondemos desde el sv a {client_address}")
            nuevo_socket.socket_UDP.sendto(segment, client_address)

            # esperamos a que llegue el ACK del cliente
            print(f"Esperamos respuesta de {client_address}")
            segment, client_address = nuevo_socket.socket_UDP.recvfrom(1024)
            tcp_dict = nuevo_socket.parse_segment(segment)
            # verificamos que el segmento también corresponda al siguiente
            print(tcp_dict)
            if (tcp_dict[b"m_type"] == b"ACK") and (int(tcp_dict[b"m_seq"].decode()) == seq + 1):
                # si todo es correcto, retornamos el nuevo socket y la dirección final
                print(f"Todo ok, avisamos del nuevo puerto para comunicar {nuevo_socket.address}")
                return nuevo_socket, nuevo_socket.address
