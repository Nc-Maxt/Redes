import sys
import SocketTCP
import perdidas


#si queremos simular perdidas, lo activamos manualmente
if "--perdidas" in sys.argv:
    perdidas.activar()
MODE = "go_back_n" if "--gbn" in sys.argv else "stop_and_wait"

server_socket_address = ('localhost', 8000)
buff_size = 1024

print('Creando socket - Servidor')
# armamos el socket con nuestra clase
server_socket = SocketTCP.SocketTCP()

if "--debug" in sys.argv:
    server_socket.debug = True

# ESTO ABRE EL SOCKET PARA QUE PUEDA RECIBIR DATOS EN LA DIRECCION Y PUERTO INDICADOS
server_socket.bind(server_socket_address)

# nos quedamos esperando a que llegue un mensaje
print('... Esperando clientes')
while True:
    # Aquí como queremos hacer hacer TCP debemos dejarlo en aceptar conexiones
    new_socket, new_socket_address = server_socket.accept()
    
    message_received = b""

    #recibimos los mensajes en partes
    while True:
        chunk_i = new_socket.recv(buff_size, MODE)
        #si el chunk llega vacio es porque terminamos
        if chunk_i is None: 
            break
        message_received += chunk_i

    print('Message received :', message_received)