import sys
import perdidas
import SocketTCP

print('Creando socket - Cliente')

#si queremos simular perdidas, lo activamos manualmente
if "--perdidas" in sys.argv:
    perdidas.activar()
MODE = "go_back_n" if "--gbn" in sys.argv else "stop_and_wait"

# armamos el socket usando nuestra clase SocketTCP  
client_socketTCP = SocketTCP.SocketTCP()

if "--debug" in sys.argv:
    client_socketTCP.debug = True

# Como queremos hacer un socket TCP debemos hacer el 3 way handshake
# la direccion del servidor se pasa como argumento
address = (sys.argv[1], int(sys.argv[2]))
client_socketTCP.connect(address)
n_address = client_socketTCP.connection

# la direccion del archivo a enviar se pasa como argumento usando > asi que llega por entrada estandar
# buffer lo lee como bytes
send_message = sys.stdin.buffer.read()

client_socketTCP.send(send_message, MODE) #enviamos el mensaje

print("... Mensaje enviado")

client_socketTCP.close()
