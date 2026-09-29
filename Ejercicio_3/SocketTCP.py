# archivo donde se creará la clase SpcketTCP, que implementa un socket TCP para enviar y recibir mensajes
import random
import socket
import numpy as np

class SocketTCP:
    def __init__(self):
        self.socket_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address = None
        self.connection = None
        self.sequence = None
        self.options = [b"ACK", b"SYN", b"ACK+SYN", b"FIN", b"ACK+FIN", b"DATA", b"INFO"]
        self.timeout = 5

        self.tot = None
        self.all_msg = b""
        self.msg_count = None
        self.act_count = None

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
        seq = b"m_seq: " + tcp_dict[b"m_seq"] + b"\r\n"
        fin = b"m_fin: " + tcp_dict[b"m_fin"] + b"\r\n\r\n"
        body = tcp_dict[b"body"]
        segment = msg_type + length + seq + fin + body
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
            b"m_fin": str(-1).encode(),
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
                b"m_fin": str(-1).encode(),
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
                b"m_fin": str(-1).encode(),
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
                # fijamos el contador para mensaje en 0, cosa de que al llamar recv se sepa que es el inicio del mensaje
                nuevo_socket.msg_count = 0
                return nuevo_socket, nuevo_socket.address

    def send(self, message):

        puntero = -1
        fin = len(message)
        # Enviamos el mensaje en trozos de a lo más n=16 bytes
        # con esto no se pueden enviar mensajes de 0 bytes de contenido, lo cual tiene sentido
        # nosotros ya realizamos el handshake para comprobar que existe una conexión
        # por lo que enviar mensajes vacíos sería inutil hasta cierto punto
        while puntero < fin:
            chunck = b""
            if puntero != -1:
                # se define el tamaño de los trozos a enviar
                chunck_s = 16
                # se obtiene el trozo a enviar
                if puntero + chunck_s > len(message):
                    chunck = message[puntero:]
                else:
                    chunck = message[puntero:puntero + chunck_s]
            
            # se parsea como mensaje con headers
            pack = {
                        b"m_type": (b"DATA" if puntero != -1 else b"INFO"),
                        b"m_len": str(len(chunck)).encode(),
                        b"m_seq": str(self.sequence).encode(),
                        b"m_fin": (str(fin).encode() if puntero == -1 else b"-1"),
                        b"body": chunck
                    }
            new_seq = int(self.sequence) + len(chunck)
            red = self.create_segment(pack)
            while True:
                try:
                    # intentamos enviar el mensaje al servidor, si no se recibe respuesta en el tiempo definido, se lanza una excepción de timeout
                    self.socket_UDP.settimeout(self.timeout)
                    self.socket_UDP.sendto(red, self.connection)

                    mensaje, server_address = self.socket_UDP.recvfrom(1024)

                    # si se recibe una respuesta, la procesamos
                    r_dict = self.parse_segment(mensaje)
                    r_seq = int(r_dict[b"m_seq"].decode())
                    if (r_dict[b"m_type"] == b"ACK") and (r_seq == new_seq) and (server_address == self.connection):
                        print(f"Mensaje enviado correctamente al servidor {self.connection}")
                        self.sequence = new_seq
                        # actualizo el puntero para el siguiente mensaje a enviar
                        if puntero == -1:
                            puntero = 0
                        else:
                            puntero += chunck_s
                        break
                    # en caso de que no llegue la respuesta esperada, se triggerea el timeout y se vuelve a enviar el mensaje
                except socket.timeout:
                    # el timeout 
                    print(f"Timeout al enviar el mensaje al servidor {self.connection}")
                    print(f"Reintentando enviar el mensaje al servidor {self.connection}")
                    pass             


    def recv(self, buff_size):
        recv_msg, emi_addr = self.socket_UDP.recvfrom(1024)  
        if self.msg_count == 0:
            #inicio de la comunicación, el primer mensaje
            parsed = self.parse_segment(recv_msg)
            if (b"INFO" == parsed[b"m_type"]) and (emi_addr == self.connection):
                # guardamos el largo que tendrá, así como dejamos todo listo para la comunicación
                self.tot = int(parsed[b"m_fin"].decode())
                self.act_count = 0
                self.sequence = int(parsed[b"m_seq"].decode())
                self.msg_count += 1
                # Respondemos que todo llegó bien
                parsed[b"m_type"] = b"ACK"
                rs = self.create_segment(parsed)
                self.socket_UDP.sendto(rs, self.connection)
        recieved = len(self.all_msg)
        # Comienza a llegar el resto de información
        while (recieved < min(self.tot, buff_size)):
            # recibimos mensajes y verificamos de que sean la continuación de lo anterior
            segment, emi_addr = self.socket_UDP.recvfrom(1024)
            msg_dict = self.parse_segment(segment)
            if (b"DATA" == msg_dict[b"m_type"]) and (self.sequence == int(msg_dict[b"m_seq"].decode())):
                self.all_msg += msg_dict[b"body"]
                largo = int(msg_dict[b"m_len"].decode())
                recieved += largo
                self.act_count += largo
                self.sequence += largo

                # enviamos la respuesta de que todo llegó bien
                pack = {
                            b"m_type": (b"ACK"),
                            b"m_len": str(0).encode(),
                            b"m_seq": str(self.sequence).encode(),
                            b"m_fin": b"-1",
                            b"body": b""
                        }
                env = self.create_segment(pack)
                self.socket_UDP.sendto(env, emi_addr)

                if (self.act_count == self.tot):
                    break

        rec = self.all_msg
        
        if len(rec) > buff_size:
            self.all_msg = rec[buff_size:]
            return rec[:buff_size]
        else: 
            self.all_msg = b""
            return rec


