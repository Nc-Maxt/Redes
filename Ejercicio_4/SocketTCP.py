# archivo donde se creará la clase SocketTCP, que implementa un socket TCP para enviar y recibir mensajes
import random
import socket
from threading import Timer
import CongestionControl
from slidingWindowCC import SlidingWindowCC
from socketUDP import SocketUDP

#TCP Tahoe solo considera slow start, congestion avoidance (AIMD) y fast retransmit. 
STOP_AND_WAIT = "stop_and_wait"
GO_BACK_N = "go_back_n"

class SocketTCP:
    def __init__(self):
        self.socket_UDP = SocketUDP()
        self.address = None
        self.connection = None
        self.sequence = None
        self.options = [b"ACK", b"SYN", b"ACK+SYN", b"FIN", b"ACK+FIN", b"DATA", b"INFO"]
        self.timeout = 5
        self.buffer_size = 68 + 16 #enunciado
        self.debug = False
        self.congestion_control_on = False
        self.congestion_controler = None
        self.number_of_sent_segments = 0  # segmentos de datos enviados con Go-Back-N (para comparar con y sin control de congestión)

        self.tot = None
        self.all_msg = b""
        self.msg_count = 0
        self.act_count = None

        self.connected = 0
        self.responded = 0
        self.last_msg = None

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

    def set_congestion_control(self, value: bool):
        self.congestion_control_on = value

    def parar_timer(self):
        # SocketUDP no detiene sus timers solo: hay que pararlo a mano cuando llega lo esperado o tras un timeout
        # (si no se para tras un timeout, el siguiente sendto intenta reiniciar un Timer ya usado y falla)
        # stop_timer falla si no hay timer creado, por eso se revisa antes
        if self.socket_UDP.timer_list[0] is not None:
            self.socket_UDP.stop_timer(0)

    def enviar(self, segment, address):
        # si el timer ya cumplió su timeout pero no alcanzamos a pararlo (llegó un mensaje justo antes),
        # SocketUDP intentaría reiniciar un Timer ya usado y falla, así que lo reseteamos antes de enviar
        timer = self.socket_UDP.timer_list[0]
        if timer is not None and not timer.is_alive():
            self.socket_UDP.stop_timer(0)
        try:
            self.socket_UDP.sendto(segment, address)
        except RuntimeError:
            # el timer venció justo mientras enviábamos: el segmento ya salió pero no se pudo reiniciar el timer.
            # como igual correspondía reenviar por timeout, reseteamos el timer y reenviamos (el receptor maneja duplicados)
            self.socket_UDP.stop_timer(0)
            self.socket_UDP.sendto(segment, address)

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
        header_len = len(msg_type) + len(length) + len(seq) + len(fin)
        if header_len < 68:
            #le sumamos lo que falta para llevar a 68 a fin
             tcp_dict[b"m_fin"].zfill(len(tcp_dict[b"m_fin"]) + 68 - header_len)
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
        # print(n)
        # creamos el diccionario para luego crear el segmento SYN y enviarlo al servidor
        ini_dict = {
            b"m_type": b"SYN",
            b"m_len": b"0",
            b"m_seq": str(n).encode(),
            b"m_fin": str(-1).encode(),
            b"body": b""
        }
        segment = self.create_segment(ini_dict)
        if self.debug:
            print(f"[DEBUG] Intentando conectar con {address}")
        self.last_msg = segment
        while not self.connected:
            try:
                self.socket_UDP.settimeout(self.timeout)
                self.enviar(segment, address)

                # esperamos a que llegue el SYN+ACK del servidor
                if self.debug:
                    print(f"[DEBUG] Esperando mensaje devuelta de {address}")
                segment, info_add = self.socket_UDP.recvfrom(self.buffer_size)
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
                    self.last_msg = segment
                    if self.debug:
                        print(f"[DEBUG] Mandamos mensaje devuelta a {info_add}")
                    self.enviar(segment, info_add)
                    # el ACK final no espera respuesta, así que paramos el timer
                    self.parar_timer()
                    # guardamos la dirección del servidor para luego enviarle los mensajes
                    self.connected = 1
                    self.set_connection(info_add)
                    print(f"Conexión cliente-sv establecida con {info_add[0]}:{info_add[1]}")
            except TimeoutError:
                self.parar_timer()
                if self.debug:
                    print(f"[DEBUG] Timeout, reintentando conectar con {address}")
                pass
                

    def accept(self):
        # esperamos a que llegue un segmento SYN del cliente
        if self.debug:
            print("[DEBUG] Esperando mensaje de clientes")
        while not self.connected:
            segment, client_address = self.socket_UDP.recvfrom(self.buffer_size)
            # parseamos el segmento recibido
            tcp_dict = self.parse_segment(segment)
            if tcp_dict[b"m_type"] == b"SYN":
                # obtenemos la secuencia del cliente y le sumamos 1 para enviar el SYN+ACK
                seq = int(tcp_dict[b"m_seq"].decode()) +1

                # establecemos un nuevo socket TCP para la conexión con el cliente
                nuevo_socket = SocketTCP()
                nuevo_socket.debug = self.debug  # el socket de la conexión hereda el modo debug
                # configuramos el nuevo socket con la dirección del cliente, la secuencia y la dirección final
                nuevo_socket.set_connection(client_address)
                nuevo_socket.set_sequence(seq)
                puerto = random.randint(1024, 9999)
                if self.debug:
                    print(f"[DEBUG] Se bindea el nuevo puerto {(self.address[0], puerto)}")
                nuevo_socket.bind((self.address[0], puerto))

                # creamos el diccionario para luego crear el segmento SYN+ACK y enviarlo al cliente
                ini_dict = {
                    b"m_type": b"SYN+ACK",
                    b"m_len": b"0",
                    b"m_seq": str(seq).encode(),
                    b"m_fin": str(-1).encode(),
                    b"body": b""
                }
                if self.debug:
                    print("[DEBUG]", ini_dict)
                syn_ack = nuevo_socket.create_segment(ini_dict)
                if self.debug:
                    print(f"[DEBUG] Le respondemos desde el sv a {client_address}")
                while not nuevo_socket.connected:
                    try:
                        nuevo_socket.socket_UDP.settimeout(nuevo_socket.timeout)
                        nuevo_socket.enviar(syn_ack, client_address)

                        # esperamos a que llegue el ACK del cliente
                        if self.debug:
                            print(f"[DEBUG] Esperamos respuesta de {client_address}")
                        segment, client_address = nuevo_socket.socket_UDP.recvfrom(self.buffer_size)
                        tcp_dict = nuevo_socket.parse_segment(segment)
                        # verificamos que el segmento también corresponda al siguiente
                        if (client_address == nuevo_socket.connection):
                            if ((tcp_dict[b"m_type"] == b"ACK") and (int(tcp_dict[b"m_seq"].decode()) == seq + 1)):
                                # si todo es correcto, retornamos el nuevo socket y la dirección final
                                if self.debug:
                                    print(f"[DEBUG] Todo ok, avisamos del nuevo puerto para comunicar {nuevo_socket.address}")
                                self.sequence = seq + 2
                                nuevo_socket.parar_timer()
                                return nuevo_socket, nuevo_socket.address
                            elif (tcp_dict[b"m_type"] == b"SYN"):
                                # en el caso de que me llegue nuevamente el SYN, quiere decir que el cliente no recibió el SYN+ACK
                                # pero no es problema porque al acabarse el tiempo de espera, vuelvo al inicio del while para enviarlo denuevo
                                if self.debug:
                                    print("[DEBUG] SYN repetido: el cliente no recibió el SYN+ACK, se reenviará al timeout")
                            else:
                                # Recibimos algo posterior al handshake.
                                # Probablemente se perdió el ACK del cliente, pero con esto se confirma que el cliente recibió el SYN+ACK, 
                                # por lo que podemos continuar con la comunicación
                                if self.debug:
                                    print("[DEBUG] Recibimos un mensaje posterior al handshake")
                                self.sequence = seq + 2
                                nuevo_socket.parar_timer()
                                return nuevo_socket, nuevo_socket.address
                        pass
                    except TimeoutError:
                        nuevo_socket.parar_timer()
                        if self.debug:
                            print(f"[DEBUG] Timeout, reintentando enviar mensaje a {client_address}")
                        pass

    def send(self, message, mode=STOP_AND_WAIT):
        if mode == STOP_AND_WAIT:
            self.send_using_stop_and_wait(message)
        elif mode == GO_BACK_N:
            self.send_using_go_back_n(message)

    def recv(self, buff_size, mode=STOP_AND_WAIT):
        if mode == STOP_AND_WAIT:
            return self.recv_using_stop_and_wait(buff_size)
        elif mode == GO_BACK_N:
            return self.recv_using_go_back_n(buff_size)
        
    def send_using_stop_and_wait(self, message):
        puntero = -1
        fin = len(message)
        # Enviamos el mensaje en trozos de a lo más n=16 bytes
        # con esto no se pueden enviar mensajes de 0 bytes de contenido, lo cual tiene sentido
        # nosotros ya realizamos el handshake para comprobar que existe una conexión
        # por lo que enviar mensajes vacíos sería inutil hasta cierto punto
        if self.debug:
            print(f"[DEBUG] Enviando mensaje de largo {len(message)} al servidor {self.connection}")
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
            if self.debug:
                print("[DEBUG] send_using_stop_and_wait: Comienza el intento de enviar la información al receptor")
            while True:
                try:
                    # intentamos enviar el mensaje al receptor, si no se recibe respuesta en el tiempo definido, se lanza una excepción de timeout
                    self.socket_UDP.settimeout(self.timeout)
                    if self.debug:
                        print(f"[DEBUG] send_using_stop_and_wait: Enviando mensaje al receptor {self.connection}")
                    self.enviar(red, self.connection)

                    mensaje, server_address = self.socket_UDP.recvfrom(self.buffer_size)

                    # si se recibe una respuesta, la procesamos
                    r_dict = self.parse_segment(mensaje)
                    if self.debug:
                        print(f"[DEBUG] send_using_stop_and_wait: Recibimos respuesta del receptor {server_address}: {r_dict}")
                    r_seq = int(r_dict[b"m_seq"].decode())
                    if (r_dict[b"m_type"] == b"ACK") and (r_seq == new_seq) and (server_address == self.connection):
                        if self.debug:
                            print(f"[DEBUG] Mensaje enviado correctamente al receptor {self.connection}")
                        self.sequence = new_seq
                        self.parar_timer()
                        # actualizo el puntero para el siguiente mensaje a enviar
                        if puntero == -1:
                            puntero = 0
                        else:
                            puntero += chunck_s
                        break
                    # en caso de que no llegue la respuesta esperada, se triggerea el timeout y se vuelve a enviar el mensaje
                except TimeoutError:
                    # el timeout 
                    self.parar_timer()
                    if self.debug:
                        print(f"[DEBUG] Timeout, reintentando enviar el mensaje al receptor {self.connection}")
                    pass   

    def iniciar_timer(self):
        # SocketUDP solo arranca su timer al hacer sendto. En Go-Back-N, si llega un ACK que avanza la ventana
        # pero no entra nada nuevo a ella (se acabaron los datos), hay que reiniciar el timer de los segmentos
        # que siguen sin confirmar sin reenviar nada, así que lo creamos a mano igual que lo haría sendto
        if self.socket_UDP.timer_list[0] is None:
            timer = Timer(self.socket_UDP.timeout, self.socket_UDP._time_up_function, args=(0,))
            self.socket_UDP.timer_list[0] = timer
            timer.start()

    def segmento_go_back_n(self, data_window, i, largo_mensaje):
        # arma el segmento del elemento i de la ventana.
        data = data_window.get_data(i)
        seq = data_window.get_sequence_number(i)
        es_info = (seq == data_window.initial_seq) #si es el primer segmento entonces es el info
        pack = {
            b"m_type": (b"INFO" if es_info else b"DATA"),
            b"m_len": str(len(data)).encode(),
            b"m_seq": str(seq).encode(),
            b"m_fin": (str(largo_mensaje).encode() if es_info else b"-1"),
            b"body": data
        }
        return self.create_segment(pack)

    def debug_congestion(self, evento, data_window):
        # modo debug de la ventana de congestión: muestra cómo evolucionan el estado, cwnd, ssthresh y la ventana
        if self.debug and self.congestion_control_on:
            cc = self.congestion_controler
            estado = "slow start" if cc.is_state_slow_start() else "congestion avoidance"
            print(f"[DEBUG CC] {evento}: estado={estado}, cwnd={cc.get_cwnd()} B, ssthresh={cc.get_ssthresh()}, "
                  f"window_size={data_window.window_size}")

    def actualizar_window_size(self, data_window):
        # tras un evento que pudo cambiar cwnd, la ventana pasa a tener tantos segmentos como MSS completos caben en cwnd.
        # en congestion avoidance cwnd crece en fracciones de MSS, así que get_MSS_in_cwnd puede venir como float
        if self.congestion_control_on:
            data_window.update_window_size(max(1, int(self.congestion_controler.get_MSS_in_cwnd())))

    def send_using_go_back_n(self, message: bytes):
        mss = 8  # parte 3: trozos de MSS = 8 bytes
        fin = len(message)

        # dividimos el mensaje en trozos de a lo más MSS bytes.
        data_list = [str(fin).encode()] + [message[i:i + mss] for i in range(0, fin, mss)]

        # con control de congestión la ventana parte con cwnd = 1 MSS
        # sino se mantiene la ventana fija de 8 segmentos de la Parte 2
        self.congestion_controler = CongestionControl.CongestionControl(mss)
        if self.congestion_control_on:
            window_size = max(1, int(self.congestion_controler.get_MSS_in_cwnd()))
        else:
            window_size = 8
        data_window = SlidingWindowCC(window_size, data_list, self.sequence)

        if self.debug:
            print(f"[DEBUG] send_using_go_back_n: Enviando mensaje de largo {fin} al receptor {self.connection} en {len(data_list)} segmentos")
        self.debug_congestion("inicio", data_window)

        self.socket_UDP.settimeout(self.timeout)

        # seq del último elemento enviado: cuando la ventana avanza o crece, se envían (de forma consecutiva)
        # justo los elementos que entraron a ella, que son los que tienen seq mayor a este
        self.max_seq_enviado = -1

        def enviar_elemento(i):
            self.socket_UDP.sendto(self.segmento_go_back_n(data_window, i, fin), self.connection)
            self.number_of_sent_segments += 1
            self.max_seq_enviado = max(self.max_seq_enviado, data_window.get_sequence_number(i))

        def enviar_nuevos():
            for i in range(data_window.window_size):
                if data_window.get_data(i) is not None and data_window.get_sequence_number(i) > self.max_seq_enviado:
                    enviar_elemento(i)

        # enviamos toda la ventana inicial. Hay un solo timer (índice 0) para toda la ventana:
        # lo arranca el primer sendto y corresponde al segmento más antiguo sin confirmar
        enviar_nuevos()

        while data_window.get_data(0) is not None: #mientras el primer elemento de la ventana tenga datos
            try:
                mensaje, server_address = self.socket_UDP.recvfrom(self.buffer_size)
                r_dict = self.parse_segment(mensaje)
                if (r_dict[b"m_type"] != b"ACK") or (server_address != self.connection):
                    continue
                r_seq = int(r_dict[b"m_seq"].decode())

                # los ACKs son acumulativos
                # caso borde: si la ventana se achico justo después de enviar el último elemento de la ventana previa,
                # puede llegar un ACK mayor al seq más grande de la ventana actual. Entonces movemos la ventana
                # completa como si hubiese llegado su último elemento, y repetimos hasta que el ACK caiga dentro de ella
                confirmados = 0
                while data_window.get_data(0) is not None:
                    k = 0
                    for i in range(data_window.window_size):
                        data = data_window.get_data(i)
                        if data is None or data_window.get_sequence_number(i) + len(data) > r_seq:
                            break
                        k = i + 1
                    if k == 0:
                        break
                    data_window.move_window(k)
                    confirmados += k
                    if k < data_window.window_size:
                        break

                if confirmados == 0:
                    # ACK repetido o atrasado: no confirma nada nuevo, seguimos esperando
                    if self.debug:
                        print(f"[DEBUG] send_using_go_back_n: ACK {r_seq} no avanza la ventana")
                    continue

                if self.debug:
                    print(f"[DEBUG] send_using_go_back_n: ACK {r_seq} confirma {confirmados} segmento(s), movemos la ventana")
                # paramos el timer del segmento confirmado
                self.parar_timer()
                if self.congestion_control_on:
                    self.congestion_controler.event_ack_received()
                    self.actualizar_window_size(data_window)
                    self.debug_congestion(f"ACK {r_seq}", data_window)
                # enviamos los elementos que entraron a la ventana (por avanzar y/o por crecer)
                enviar_nuevos()
                # si quedan segmentos sin confirmar pero no se envió nada nuevo, el timer sigue corriendo por ellos
                if data_window.get_data(0) is not None:
                    self.iniciar_timer()

            except TimeoutError:
                # Go-Back-N: se reenvía toda la ventana desde el segmento más antiguo sin confirmar
                self.parar_timer()
                if self.congestion_control_on:
                    self.congestion_controler.event_timeout()
                    self.actualizar_window_size(data_window)
                    self.debug_congestion("timeout", data_window)
                if self.debug:
                    print(f"[DEBUG] send_using_go_back_n: Timeout, reenviando la ventana desde seq {data_window.get_sequence_number(0)}")
                # lo que quedó fuera de la ventana al achicarse se tendrá que volver a enviar cuando vuelva a entrar
                self.max_seq_enviado = -1
                enviar_nuevos()

        # todo confirmado: el timer ya no tiene nada que vigilar
        self.parar_timer()
        self.sequence = data_window.initial_seq + len(data_list[0]) + fin
        if self.debug:
            print(f"[DEBUG] send_using_go_back_n: Mensaje enviado completo, seq final {self.sequence}")


    def recv_using_stop_and_wait(self, buff_size):
        # el receptor espera sin límite, los reenvíos son responsabilidad del emisor
        self.socket_UDP.settimeout(-1)
        if (self.msg_count == 0) and (self.all_msg != b""):
            rec = self.all_msg

            if len(rec) > buff_size:
                self.all_msg = rec[buff_size:]
                return rec[:buff_size]
            else:
                self.all_msg = b""
                return rec

        while self.msg_count == 0:
            recv_msg, emi_addr = self.socket_UDP.recvfrom(self.buffer_size)  
            #inicio de la comunicación, el primer mensaje
            parsed = self.parse_segment(recv_msg)
            if self.debug:
                print(f"[DEBUG] Recibimos mensaje del emisor {emi_addr}: {parsed}")
            if (b"INFO" == parsed[b"m_type"]) and (emi_addr == self.connection):
                # guardamos el largo que tendrá, así como dejamos todo listo para la comunicación
                self.tot = int(parsed[b"m_fin"].decode())
                self.act_count = 0
                self.sequence = int(parsed[b"m_seq"].decode())
                self.msg_count = 1
                # Respondemos que todo llegó bien
                parsed[b"m_type"] = b"ACK"
                rs = self.create_segment(parsed)
                self.last_msg = rs
                self.enviar(rs, self.connection)
            # si tengo msg_count = 0 quiere decir que no hay un mensaje enviandose activamente,
            # por lo que si llega un FIN, es porque el emisor quiere cerrar la conexión
            elif (emi_addr == self.connection) and (parsed[b"m_type"] == b"FIN") and (int(parsed[b"m_seq"].decode()) == self.sequence):
                self.recv_close()
                return None
            #caso el ultimo DATA que llegó se mandó repetido 
            elif (emi_addr == self.connection) and (parsed[b"m_type"] == b"DATA") and (int(parsed[b"m_seq"].decode()) < self.sequence):
                if self.debug:
                    print("[DEBUG] DATA repetido (fuera de recepción): se perdió nuestro ACK, reenviando el último ACK")
                self.enviar(self.last_msg, emi_addr)

        recieved = len(self.all_msg)
        # Comienza a llegar el resto de información
        while (recieved < min(self.tot, buff_size)):
            # recibimos mensajes y verificamos de que sean la continuación de lo anterior
            segment, emi_addr = self.socket_UDP.recvfrom(self.buffer_size)
            if self.debug:
                print(f"[DEBUG] Recibimos mensaje del emisor {emi_addr}: {segment}")
            msg_dict = self.parse_segment(segment)
            if (b"DATA" == msg_dict[b"m_type"]):
                if (self.sequence == int(msg_dict[b"m_seq"].decode())):
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
                    self.last_msg = env
                    if self.debug:
                        print(f"[DEBUG] Enviamos mensaje de respuesta al emisor {emi_addr}: {env}")
                    self.enviar(env, emi_addr)

                    if (self.act_count == self.tot):
                        self.msg_count = 0
                        self.tot = None
                        self.act_count = None
                        break
                elif (self.sequence > int(msg_dict[b"m_seq"].decode())):
                    # si el número de secuencia esperado es mayor al recibido, reenviamos el último mensaje enviado
                    if self.debug:
                        print("[DEBUG] DATA repetido: se perdió nuestro ACK, reenviando el último ACK")
                    self.enviar(self.last_msg, emi_addr)
            elif (b"INFO" == msg_dict[b"m_type"]) and (emi_addr == self.connection) and (int(msg_dict[b"m_seq"].decode()) == self.sequence):
                if self.debug:
                    print("[DEBUG] INFO repetido: se perdió nuestro ACK del INFO, reenviándolo")
                self.enviar(self.last_msg, emi_addr)

        rec = self.all_msg
        if len(rec) > buff_size:
            self.all_msg = rec[buff_size:]
            return rec[:buff_size]
        else: 
            self.all_msg = b""
            return rec

    def recv_using_go_back_n(self, buff_size):
        # el receptor espera sin límite, los reenvíos son responsabilidad del emisor
        self.socket_UDP.settimeout(-1)
        if (self.msg_count == 0) and (self.all_msg != b""):
            rec = self.all_msg

            if len(rec) > buff_size:
                self.all_msg = rec[buff_size:]
                return rec[:buff_size]
            else:
                self.all_msg = b""
                return rec

        while self.msg_count == 0:
            recv_msg, emi_addr = self.socket_UDP.recvfrom(self.buffer_size)  
            #inicio de la comunicación, el primer mensaje
            parsed = self.parse_segment(recv_msg)
            if self.debug:
                print(f"[DEBUG] Recibimos mensaje del emisor {emi_addr}: {parsed}")
            # un INFO con seq menor al esperado es un reenvío del mensaje anterior (Go-Back-N reenvía la ventana
            # completa, que puede incluir el INFO si se perdieron todos los ACKs), no un mensaje nuevo
            if (b"INFO" == parsed[b"m_type"]) and (emi_addr == self.connection) and (int(parsed[b"m_seq"].decode()) >= self.sequence):
                # guardamos el largo que tendrá
                self.tot = int(parsed[b"m_fin"].decode())
                self.act_count = 0
                # el INFO ocupa tantos bytes de secuencia como su body (el largo del mensaje escrito como texto)
                self.sequence = int(parsed[b"m_seq"].decode()) + int(parsed[b"m_len"].decode())
                self.msg_count = 1
                # Respondemos que todo llegó bien
                parsed[b"m_type"] = b"ACK"
                parsed[b"m_len"] = b"0"
                parsed[b"m_seq"] = str(self.sequence).encode()
                parsed[b"body"] = b""
                rs = self.create_segment(parsed)
                self.last_msg = rs
                self.enviar(rs, self.connection)
            # si tengo msg_count = 0 quiere decir que no hay un mensaje enviandose activamente,
            # por lo que si llega un FIN, es porque el emisor quiere cerrar la conexión
            elif (emi_addr == self.connection) and (parsed[b"m_type"] == b"FIN") and (int(parsed[b"m_seq"].decode()) == self.sequence):
                self.recv_close()
                return None
            # DATA o INFO repetidos del mensaje anterior (se perdió nuestro ACK), o DATA que llegó antes que su INFO
            # (se perdió el INFO): reenviamos el último ACK. El emisor reenviará la ventana al cumplirse su timeout
            elif (emi_addr == self.connection) and (parsed[b"m_type"] in (b"DATA", b"INFO")):
                if self.debug:
                    print("[DEBUG] Segmento fuera de recepción: reenviando el último ACK")
                if self.last_msg is not None:
                    self.enviar(self.last_msg, emi_addr)

        recieved = len(self.all_msg)
        # Comienza a llegar el resto de información
        while (recieved < min(self.tot, buff_size)):
            # recibimos mensajes y verificamos de que sean la continuación de lo anterior
            segment, emi_addr = self.socket_UDP.recvfrom(self.buffer_size)
            if self.debug:
                print(f"[DEBUG] Recibimos mensaje del emisor {emi_addr}: {segment}")
            msg_dict = self.parse_segment(segment)
            if emi_addr != self.connection:
                continue
            if (b"DATA" == msg_dict[b"m_type"]):
                if (self.sequence == int(msg_dict[b"m_seq"].decode())):
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
                    self.last_msg = env
                    if self.debug:
                        print(f"[DEBUG] Enviamos mensaje de respuesta al emisor {emi_addr}: {env}")
                    self.enviar(env, emi_addr)

                    if (self.act_count == self.tot):
                        self.msg_count = 0
                        self.tot = None
                        self.act_count = None
                        break
                else:
                    # Go Back N: el receptor no guarda segmentos fuera de orden. Si es repetido (seq menor) o se perdió
                    # uno anterior (seq mayor), se descarta y se reenvía el último ACK acumulativo
                    if self.debug:
                        print(f"[DEBUG] DATA fuera de orden (seq {int(msg_dict[b'm_seq'].decode())}, esperado {self.sequence}): reenviando el último ACK")
                    self.enviar(self.last_msg, emi_addr)
            elif (b"INFO" == msg_dict[b"m_type"]) and (int(msg_dict[b"m_seq"].decode()) < self.sequence):
                if self.debug:
                    print("[DEBUG] INFO repetido: se perdió nuestro ACK del INFO, reenviándolo")
                self.enviar(self.last_msg, emi_addr)

        rec = self.all_msg
        if len(rec) > buff_size:
            self.all_msg = rec[buff_size:]
            return rec[:buff_size]
        else: 
            self.all_msg = b""
            return rec

    def close(self):
        # generamos el mensaje FIN para cerrar la conexión
        fin_dict = {
            b"m_type": b"FIN",
            b"m_len": b"0",
            b"m_seq": str(self.sequence).encode(),
            b"m_fin": str(-1).encode(),
            b"body": b""
        }
        fin_segment = self.create_segment(fin_dict)

        intentos = 0 #cantidad de intentos de enviar el FIN
        while intentos < 3:
            try:
                # seteamos un timeout para esperar la respuesta del ACK del servidor
                self.socket_UDP.settimeout(self.timeout)
                self.enviar(fin_segment, self.connection) #mandamos FIN

                resp, addr = self.socket_UDP.recvfrom(self.buffer_size)  # esperamos el ACK del servidor
                parsed_resp = self.parse_segment(resp)
                #caso recibimos el FIN+ACK del servidor
                if (addr == self.connection) and (parsed_resp[b"m_type"] == b"FIN+ACK") and (int(parsed_resp[b"m_seq"].decode()) == self.sequence + 1):
                    print(f"Cierre de conexión con {self.connection} exitoso")
                    fin_ack_dict = {
                        b"m_type": b"ACK",
                        b"m_len": b"0",
                        b"m_seq": str(self.sequence + 2).encode(),
                        b"m_fin": str(-1).encode(),
                        b"body": b""
                    }
                    fin_ack_segment = self.create_segment(fin_ack_dict)
                    # llegó el FIN+ACK, paramos el timer del FIN
                    self.parar_timer()
                    #mandamos 3 veces el ultimo ACK con un timeout entremedio
                    for i in range(3):
                        self.enviar(fin_ack_segment, self.connection)
                        try:
                            #el server ya no respondera nada mas, por lo que el timeout se triggereara siempre
                            if self.debug:
                                print("[DEBUG] Enviando ultimo ACK 3 veces, intento ", i+1)
                            self.socket_UDP.recvfrom(self.buffer_size) 
                        except TimeoutError:
                            self.parar_timer()
                    self.parar_timer()
                    self.socket_UDP.close()
                    break
            #caso timeout, reintentamos enviar el FIN
            except TimeoutError:
                self.parar_timer()
                if self.debug:
                    print(f"[DEBUG] Timeout, reintentando enviar FIN a {self.connection}")
                intentos += 1
                pass
            if intentos == 3:
                print("Error: No se recibió el ACK del servidor después de 3 intentos. Se asume que el servidor no recibió el FIN y se cierra la conexión")
                self.socket_UDP.close()

    def recv_close(self):
        if self.debug:
            print(f"[DEBUG] Solicitud de cierre de conexión con {self.connection} exitosa")
        self.sequence += 1
        fin_ack_dict = {
            b"m_type": b"FIN+ACK",
            b"m_len": b"0",
            b"m_seq": str(self.sequence).encode(),
            b"m_fin": str(-1).encode(),
            b"body": b""
        }

        fin_ack_segment = self.create_segment(fin_ack_dict)
        
        intentos = 0 #cantidad de intentos de enviar el FIN+ACK
        while intentos < 3:
            try:
                self.socket_UDP.settimeout(self.timeout)
                self.enviar(fin_ack_segment, self.connection)
                #esperamos el ACK del cliente
                ack_resp, addr = self.socket_UDP.recvfrom(self.buffer_size) 
                parsed_ack_resp = self.parse_segment(ack_resp)
                if (addr == self.connection) and (parsed_ack_resp[b"m_type"] == b"ACK") and (int(parsed_ack_resp[b"m_seq"].decode()) == self.sequence + 1):
                    print(f"Cierre de conexión con {self.connection} exitoso")
                    # cerramos el socket
                    self.parar_timer()
                    self.socket_UDP.close()
                    break
                elif self.debug:
                    print(f"[DEBUG] llegó {parsed_ack_resp[b'm_type']} en vez del ACK final (probablemente FIN repetido), reenviando FIN+ACK")
            except TimeoutError:
                self.parar_timer()
                if self.debug:
                    print(f"[DEBUG] Timeout, reintentando enviar FIN+ACK a {self.connection}")
                intentos += 1
                pass
        if intentos == 3:
            print("Error: No se recibió el ACK del cliente después de 3 intentos. Se asume que el cliente no recibió el FIN+ACK y se cierra la conexión")
            self.socket_UDP.close()
