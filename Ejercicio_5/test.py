# Test del paso 4
import router

r1 = router.Router("127.0.0.1", 8881, "rutas_R1_v1.txt")

IP_packet_v1 = b'\x7f\x00\x00\x01"\xb1omg hi'
parsed_IP_packet = r1.parse_packet(IP_packet_v1)
IP_packet_v2 = r1.create_packet(parsed_IP_packet)
print("IP_packet_v1 == IP_packet_v2 ? {}".format(IP_packet_v1 == IP_packet_v2))
print("el paquete parseado: ", parsed_IP_packet)
