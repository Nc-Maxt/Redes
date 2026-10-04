# ===== [PERDIDAS] (ver perdidas.py) =====
# python3 t_sv.py --perdidas  → activa pérdidas aleatorias (ambas direcciones si cliente y servidor lo usan)
# python3 t_sv.py             → funcionamiento normal, sin pérdidas
import sys
import SocketTCP
import perdidas

if "--perdidas" in sys.argv:
    perdidas.activar()
# ===== [PERDIDAS] fin =====

address = ("localhost", 5000)

# SERVER
server_socketTCP = SocketTCP.SocketTCP()
server_socketTCP.bind(address)
connection_socketTCP, new_address = server_socketTCP.accept()

# test 1
buff_size = 16
full_message = connection_socketTCP.recv(buff_size)
print("Test 1 received:", full_message)
if full_message == "Mensje de len=16".encode(): print("Test 1: Passed")
else: print("Test 1: Failed")

# test 2
print("Test 2: Receiving message of length 19")
buff_size = 19
print("Esperamos el mensaje de largo 19")
full_message = connection_socketTCP.recv(buff_size)
print("Test 2 received:", full_message)
if full_message == "Mensaje de largo 19".encode(): print("Test 2: Passed")
else: print("Test 2: Failed")

# test 3
buff_size = 14
message_part_1 = connection_socketTCP.recv(buff_size)
print("Test 3 received:", message_part_1)
message_part_2 = connection_socketTCP.recv(buff_size)
print("Test 3 received:", message_part_2)
print("Test 3 received:", message_part_1 + message_part_2)
if (message_part_1 + message_part_2) == "Mensaje de largo 19".encode(): print("Test 3: Passed")
else: print("Test 3: Failed")

# test 4
buff_size = 32
full_message = connection_socketTCP.recv(buff_size)
if full_message is None: print("Test 4: Passed")
else: print("Test 4: Failed")