import socket
from protocolos import *

root_ip = "198.41.0.4"
cache = Cache()

def resolver(mensaje_consulta: bytes, ip_addr: str = root_ip, debug: bool = True) -> bytes:

    #tengo el mensaje, lo reviso en cache
    nombre = DNSRecord.parse(mensaje_consulta).questions[0].get_qname()
    if debug:
        pass
        #print(f"(debug) Buscando la ip de {nombre}")
    ip_answer = cache.recuperar_ip(nombre)
    if ip_answer is not None:
        if(debug):
            print(f"(debug) Consulta exitosa en cache {nombre} -> {ip_answer}")
        q = DNSRecord.parse(mensaje_consulta)
        q.add_answer(*RR.fromZone("{} A {}".format(nombre, ip_answer)))
        dns_q = q.pack()
        return dns_q

    resp = send_DNS_query(mensaje_consulta, ip_addr)

    datos = parse_DNS_message(resp)
    buscado = datos["Qname"]
    #print(datos)

    nombre = "."
    n_ip = ip_addr
    if debug:
        print("(debug) Entrando al caso de answer")
    if datos["ANCOUNT"] > 0:
        for record in datos["Answer"]:
            if QTYPE.get(record.rtype) == "A":
                if debug:
                    print("(debug) Consulta resuelta.")
                return resp
    if debug:
        print("(debug) Entrando al caso de nameserver")
    if datos["NSCOUNT"]>0:
        for record in datos["Additional"]:
            if QTYPE.get(record.rtype) == "A":
                n_ip = str(record.rdata)
                nombre = record.get_rname()
                if debug:
                    print(f"(debug) Consultando '{buscado}' a '{nombre}' con dirección IP '{n_ip}'")
                valor = resolver(mensaje_consulta, n_ip, debug)
                if valor is not None:
                    return valor    
        if debug:
            print("(debug) Buscando en opciones extra")                    
        for record in datos["Authority"]:
            if QTYPE.get(record.rtype) == "NS":
                ns = record
                buscar = ns.rdata
                if debug:
                    print(f"(Debug) Consultando por la ip de  {buscar}")
                q = DNSRecord.question(str(buscar))
                info = resolver(bytes(q.pack()), debug=debug)
                if info is not None:
                    parseado = parse_DNS_message(info)
                    for record in parseado["Answer"]:
                        if QTYPE.get(record.rtype) == "A":
                            n_ip = record.rdata
                            nombre = record.get_rname()
                            if debug:
                                print(f"(debug) Consultando '{buscado}' a '{nombre}' con dirección IP '{n_ip}'")
                            valor = resolver(mensaje_consulta, str(n_ip), debug)
                            if valor is not None:
                                return valor
        if debug:
            print("(debug) No es uno de los casos a estudiar.")
            return None
    else:
        if debug:
            print("(debug) No es uno de los casos a estudiar.")
        return None

print('Creando socket - resolver')

# armamos el socket, los parámetros que recibe el socket indican el tipo de conexión
# socket.SOCK_DGRAM = socket NO orientado a conexión
resolver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Como buscamos ver mensajes DNS necesitamos un socket NO orientado a conexión 
address = ('localhost', 8000)

# ESTO ABRE EL SOCKET PARA QUE PUEDA RECIBIR DATOS EN LA DIRECCION Y PUERTO INDICADOS
resolver_socket.bind(address)
buffer_size = 4096

# nos quedamos esperando a que llegue un mensaje
print('... Esperando clientes')
while True:
    # En vez de aceptar una conexión, recibimos un mensaje desde el socket
    # la función recvfrom entrega una tupla con el mensaje y la dirección del cliente
    recv_message, client_address = resolver_socket.recvfrom(buffer_size)
    print(f' -> Se ha recibido el siguiente mensaje: {recv_message}')

    info = resolver(recv_message)
    #print(parse_DNS_message(info))
    puntuales = retrieve_info(parse_DNS_message(info))
    #print(f"guardando en cache {puntuales}")
    if puntuales[0] is not None:
        
        cache.actualizar_20(puntuales)
    if info is not None:
        #print("mensaje para enviar devuelta al cliente es")
        #print(info)
        resolver_socket.sendto(info, client_address)
    