import sys
import time
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

# con --cc se activa el control de congestión en Go-Back-N
if "--cc" in sys.argv:
    client_socketTCP.set_congestion_control(True)

# Como queremos hacer un socket TCP debemos hacer el 3 way handshake
# la direccion del servidor se pasa como argumento
address = (sys.argv[1], int(sys.argv[2]))
client_socketTCP.connect(address)
n_address = client_socketTCP.connection

# la direccion del archivo a enviar se pasa como argumento usando > asi que llega por entrada estandar
# buffer lo lee como bytes
send_message = sys.stdin.buffer.read()

inicio = time.time()
client_socketTCP.send(send_message, MODE) #enviamos el mensaje
duracion = time.time() - inicio

print("... Mensaje enviado")
# métricas para comparar Go-Back-N con y sin control de congestión
print(f"Tiempo de envío: {duracion:.3f} s")
if MODE == "go_back_n":
    print(f"Segmentos de datos enviados: {client_socketTCP.number_of_sent_segments}")

client_socketTCP.close()
