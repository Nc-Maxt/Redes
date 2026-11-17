# Test del paso 1
from router import * 

r1 = Router("127.0.0.1", 8881, "rutas_R1_v3_mtu.txt")

IP_packet_v1 = b'\x7f\x00\x00\x01"\xb1\x0d\x00\x00\x00\x06\x00\x01\x00\x00\x00\x00\x00omg hi'
parsed_IP_packet = r1.parse_packet(IP_packet_v1)
IP_packet_v2 = r1.create_packet(parsed_IP_packet)
print("IP_packet_v1 == IP_packet_v2 ? {}".format(IP_packet_v1 == IP_packet_v2))
print("el paquete parseado: ", parsed_IP_packet)


# Test del paso 5 para el fragmentador y reensamblador
IP_packet_v1 = b'\x7f\x00\x00\x01"\xb1\x0d\x00\x00\x00\x34\x00\x01\x00\x00\x00\x00\x00omg hi, so long without seen yuh. How have you been?'

parsed_IP_packet = r1.parse_packet(IP_packet_v1)
fragment_list = fragment_IP_packet(parsed_IP_packet, 24)
IP_packet_v2 = reassemble_IP_packet(fragment_list)
print("el paquete reensamblado: ", IP_packet_v2)
print("IP_packet_v1 = IP_packet_v2 ? {}".format(parsed_IP_packet == IP_packet_v2))

print(len(b"Como decir paralelepipedo sin decir bipedo ni niptero?. O bien como se dice hipopotomonstrosesquipedaliofobia sin fobia, sin hipopotamo, ni monstruo? "))