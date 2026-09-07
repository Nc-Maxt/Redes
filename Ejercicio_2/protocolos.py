
import dnslib
from dnslib.dns import CLASS, QTYPE
from dnslib.dns import RR, A
from dnslib import DNSRecord
import socket

class Cache():
    def __init__(self):
        self.hist = []
        self.presentes = {}
        self.guardados = [None, None, None]

    def act_top(self):
        ordenado = sorted(self.presentes,
                    key = lambda nm: self.presentes[nm], reverse= True)
        self.guardados = ordenado[:3]

        while len(self.guardados) < 3:
            self.guardados.append(None)

    def act_presentes(self, nombre, resta):
        nm = str(nombre)
        if nm not in self.presentes:
            self.presentes[nm] = 1
        else:
            if resta:
                self.presentes[nm] -= 1
                if self.presentes[nm] == 0:
                    del self.presentes[nm]
            else:
                self.presentes[nm] += 1
    
    def actualizar_20(self, consulta):   
        nm = consulta[0]
        ip = consulta[1]
        if len(self.hist)==20:
            ant = self.hist.pop(0)
            nm_ant = ant[0]
            self.act_presentes(nm_ant, True)

        self.hist.append([nm, ip])
        self.act_presentes(nm, False)
        self.act_top()

    def recuperar_ip(self, nombre):
        nm = str(nombre)
        if nm in self.guardados:
            for consulta in self.hist:
                if consulta[0] == nm:
                    return consulta[1]
        return None
        

def send_DNS_query(mensaje: bytes, server_ip: str, server_port: int = 53) -> bytes:
    #recordar que el mensaje de consulta es justamente el que recibo del cliente
    # ahora yo debo ser quien envia ese mensaje al sv para preguntar
    # para ello debo hacer otro socket para actuar como cliente
    # como es no orientado a conexion sera un efimero
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(2)
    # recuperamos el address a donde hay que mandar el mensaje
    address = (server_ip, server_port)
    print("voy a mandar un mensaje")
    client_socket.sendto(mensaje, address)
    print("esperando mensaje")
    resp, _ = client_socket.recvfrom(4096)
    print("recibí mensaje")
    client_socket.close()
    return resp


def retrieve_info(datos: dict[hex]) -> tuple[str| None, str| None]:
    # esta función toma un dict de bytes y devuelve el Qname y la dirección IP
    # si no hay dirección IP devuelve None
    qname = str(datos["Qname"])
    ip = None
    if datos["ANCOUNT"] > 0:
        for record in datos["Answer"]:
            if QTYPE.get(record.rtype) == "A":
                if str(record.get_rname()) == qname:
                    ip = str(record.rdata)
                    return (qname, ip)
    return (None, None)


# toma un mensaje en bytes y lo transforma en un dict de bytes
def parse_DNS_message(dns_message: bytes) -> dict[hex]:
    # como el mensaje esta en formato dns por la librería, podemos usar la librería para parsearlo 
    # y obtener la información relevante Qname, ANCOUNT, NSCOUNT, ARCOUNT, la sección Answer, la sección Authority y la sección Additional

    d = DNSRecord.parse(dns_message)
    # armamos un diccionario con la información relevante   
    info = {}
    info["Qname"] = d.questions[0].get_qname()
    info["ANCOUNT"] = d.header.a
    info["NSCOUNT"] = d.header.auth
    info["ARCOUNT"] = d.header.ar
    info["Answer"] = d.rr
    info["Authority"] = d.auth
    info["Additional"] = d.ar
    return info