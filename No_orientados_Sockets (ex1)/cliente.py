import socket

print('Creando socket - Cliente')

# armamos el socket, los parámetros que recibe el socket indican el tipo de conexión
# socket.SOCK_DGRAM = socket NO orientado a conexión
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Como es un socket NO orientado a conexión no necesitamos conectarlo a una dirección específica
address = ('localhost', 5000)
# address = input("Escribe la direccion y puerto para copnectar: ")
# print(f"Escribiste: {address}")

# Definimos un mensaje y una secuencia indicando el fin del mensaje (parte de nuestro protocolo inventado)
#message = "Hola, este es un mensaje de prueba"
message = input("Escribe algo y presiona Enter para enviar el mensaje: ")
print(f"Escribiste: {message}")
end_of_message = "\n"

# Armamos el mensaje final a enviar y lo pasamos a bytes con encode
send_message = (message + end_of_message).encode()

# enviamos el mensaje a través del socket
print(f"... Mandando el mensaje: {send_message.decode()}")
client_socket.sendto(send_message, address)

print("... Mensaje enviado")

# Finalmente esperamos una respuesta
# Para ello debemos definir el tamaño del buffer de recepción
buffer_size = 1024
message, server_address = client_socket.recvfrom(buffer_size)

# Pasamos el mensaje de bytes a string
decoded_message = message.decode()

print(f' -> Respuesta del servidor: {decoded_message}')

# cerramos la conexión
print(f"conexión con {client_socket.getsockname()}")
client_socket.close()
print("ha sido cerrada")
