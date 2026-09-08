
import dnslib
from dnslib.dns import CLASS, QTYPE
from dnslib.dns import RR, A
from dnslib import DNSRecord
import socket

class Cache():
    """Cache de las consultas DNS más frecuentes entre las últimas 20.

    Mantiene un historial de las últimas 20 consultas (nombre, ip), un conteo
    de cuántas veces aparece cada nombre en ese historial y los 3 nombres más
    consultados, que son los únicos que se responden desde la cache.
    """
    def __init__(self):
        """Inicializa la cache con historial vacío, sin conteos y sin top 3.

        Atributos:
            hist: Lista de pares [nombre, ip] de las últimas 20 consultas.
            presentes: Diccionario nombre -> apariciones en hist.
            guardados: Los 3 nombres más frecuentes (None si hay menos de 3).
        """
        self.hist = []
        self.presentes = {}
        self.guardados = [None, None, None]

    def act_top(self):
        """Recalcula los 3 nombres más consultados según los conteos.

        Ordena los nombres de mayor a menor frecuencia y guarda los 3 primeros
        en guardados, rellenando con None si hay menos de 3.

        Returns:
            None.
        """
        ordenado = sorted(self.presentes,
                    key = lambda nm: self.presentes[nm], reverse= True)
        self.guardados = ordenado[:3]

        while len(self.guardados) < 3:
            self.guardados.append(None)

    def act_presentes(self, nombre, resta):
        """Actualiza el conteo de apariciones de un nombre en el historial.

        Args:
            nombre: Nombre de dominio cuyo conteo se modifica.
            resta: Si es True se descuenta una aparición (y se elimina el
                nombre cuando llega a 0); si es False se suma una.

        Returns:
            None.
        """
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
        """Agrega una consulta al historial manteniendo solo las últimas 20.

        Si el historial ya tiene 20 entradas, elimina la más antigua y
        descuenta su conteo. Luego agrega la nueva consulta, suma su conteo y
        recalcula el top 3.

        Args:
            consulta: Tupla o lista (nombre, ip) de la consulta resuelta.

        Returns:
            None.
        """
        nm = consulta[0]
        ip = consulta[1]
        if len(self.hist)==20:
            ant = self.hist.pop(0)
            nm_ant = ant[0]
            self.act_presentes(nm_ant, True)

        self.hist.append([nm, ip])
        self.act_presentes(nm, False)
        self.act_top()

    def recuperar_ip(self, nombre) -> str | None:
        """Busca la IP de un nombre en la cache.

        Solo responde si el nombre está entre los 3 más consultados; en ese
        caso retorna la IP registrada en el historial.

        Args:
            nombre: Nombre de dominio a buscar.

        Returns:
            La IP como string si está en la cache, o None en caso contrario.
        """
        nm = str(nombre)
        if nm in self.guardados:
            for consulta in self.hist:
                if consulta[0] == nm:
                    return consulta[1]
        return None
        

def send_DNS_query(mensaje: bytes, server_ip: str, server_port: int = 53) -> bytes:
    """Envía una consulta DNS por UDP a un servidor y retorna su respuesta.

    Crea un socket UDP efímero con timeout de 2 segundos, envía el mensaje a
    (server_ip, server_port), espera la respuesta y cierra el socket.

    Args:
        mensaje: Consulta DNS en bytes.
        server_ip: IP del servidor DNS al que se consulta.
        server_port: Puerto del servidor. Por defecto 53.

    Returns:
        Respuesta DNS en bytes.
    """
    #recordar que el mensaje de consulta es justamente el que recibo del cliente
    # ahora yo debo ser quien envia ese mensaje al sv para preguntar
    # para ello debo hacer otro socket para actuar como cliente
    # como es no orientado a conexion sera un efimero
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(2)
    # recuperamos el address a donde hay que mandar el mensaje
    address = (server_ip, server_port)
    client_socket.sendto(mensaje, address)
    resp, _ = client_socket.recvfrom(4096)
    client_socket.close()
    return resp


def retrieve_info(datos: dict) -> tuple[str| None, str| None]:
    """Extrae el nombre consultado y su IP desde un mensaje DNS parseado.

    Recorre la sección Answer buscando un registro A cuyo nombre coincida con
    el Qname. Si en vez de eso hay un CNAME, busca algún registro A que
    corresponde al alias.

    Args:
        datos: Diccionario con el formato que entrega parse_DNS_message.

    Returns:
        Tupla (qname, ip) como strings, o (None, None) si no hay IP asociada.
    """
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
            if QTYPE.get(record.rtype) == "CNAME":
                cname = str(record.rdata)
                for rec in datos["Answer"]:
                    if QTYPE.get(rec.rtype) == "A":
                        if str(rec.get_rname()) == cname:
                            ip = str(rec.rdata)
                            return (qname, ip)
    return (None, None)


def parse_DNS_message(dns_message: bytes) -> dict:
    """Parsea un mensaje DNS en bytes y extrae la información relevante.

    Usa dnslib para decodificar el mensaje y arma un diccionario con el nombre
    consultado, los contadores del header y las tres secciones de registros.

    Args:
        dns_message: Mensaje DNS en bytes.

    Returns:
        Diccionario con las llaves "Qname", "ANCOUNT", "NSCOUNT", "ARCOUNT",
        "Answer", "Authority" y "Additional".
    """
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