# python3 t_client.py --perdidas  #activa pérdidas aleatorias
# python3 t_client.py #funcionamiento normal, sin pérdidas
import sys
import SocketTCP
import perdidas

if "--perdidas" in sys.argv:
    perdidas.activar()

address = ("localhost", 5000)

# CLIENT
client_socketTCP = SocketTCP.SocketTCP()
client_socketTCP.connect(address)
# test 1
print("Test 1: Sending message of length 16")
message = "Mensje de len=16".encode()
client_socketTCP.send(message)
# test 2
print("Test 2: Sending message of length 19")
message = "Mensaje de largo 19".encode()
client_socketTCP.send(message)

# test 3
print("Test 3: Sending message of length 19")
message = "Mensaje de largo 19".encode()
client_socketTCP.send(message)

#test 4
print("Test 4: Closing connection")
client_socketTCP.close()