# Simulación de pérdidas a mano para probar SocketTCP sin modificar su código.

import random
import socket

# guardamos la clase original antes de reemplazarla
socket_original = socket.socket


class SocketConPerdidas:
    loss_rate = 0.0          
    timeout_override = None  # si no es None, reemplaza los timeouts que pida SocketTCP

    def __init__(self, *args, **kwargs):
        self.s = socket_original(*args, **kwargs)

    def sendto(self, data, address):
        if random.random() < SocketConPerdidas.loss_rate:
            # primeras líneas del header: m_type y m_len / m_seq
            header = data.split(b"\r\n")[:3]
            print(f"[PÉRDIDA SIMULADA] hacia {address}: {b' | '.join(header).decode(errors='replace')}")
            return len(data)  # fingimos que se envió
        return self.s.sendto(data, address)

    def settimeout(self, t):
        # con --perdidas, acorta los timeouts de reenvío al valor de TIMEOUT,
        # sin tocar settimeout(None), que significa "esperar sin límite"
        if t is not None and SocketConPerdidas.timeout_override is not None:
            t = SocketConPerdidas.timeout_override
        return self.s.settimeout(t)

    def __getattr__(self, name):
        # todo lo demás (bind, recvfrom, close...) se delega al socket real
        return getattr(self.s, name)


# valores usados al activar las pérdidas con --perdidas
LOSS_RATE = 0.2   # 20% de los segmentos enviados se pierden
TIMEOUT = 0.5     # timeout de reenvío más corto, para que las pruebas no tarden tanto


def activar(loss_rate=LOSS_RATE, timeout=TIMEOUT):
    SocketConPerdidas.loss_rate = loss_rate
    SocketConPerdidas.timeout_override = timeout
    socket.socket = SocketConPerdidas
