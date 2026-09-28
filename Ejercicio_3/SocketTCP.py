# archivo donde se creará la clase SpcketTCP, que implementa un socket TCP para enviar y recibir mensajes


class SocketTCP:
    def __init__(self):
        self.socket_UDP = None
        self.final_address = None
        self.sequence = None
        self.options = [b"ACK", b"SYN", b"ACK+SYN", b"FIN", b"ACK+FIN"]
        self.timeout = 5

    def set_socket_UDP(self, socket_UDP):
        self.socket_UDP = socket_UDP

    def set_final_address(self, final_address):
        self.final_address = final_address

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
        length =   b"m_length: " + tcp_dict[b"m_length"] + b"\r\n"
        seq = b"m_sequence: " + tcp_dict[b"m_sequence"] + b"\r\n\r\n"
        body = tcp_dict[b"body"]
        segment = msg_type + length + seq + body
        return segment