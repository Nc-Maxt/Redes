# Test del paso 3
import router

r1 = router.Router("127.0.0.1", 8881, "rutas_R1_v3_mtu.txt")

IP_packet_v1 = b'\x7f\x00\x00\x01"\xb1\x0d\x00\x00\x00\x06\x00\x01\x00\x00\x00\x00\x00omg hi'

print("el paquete parseado: ", r1.parse_packet(IP_packet_v1))

fragment = router.fragment_IP_packet(r1.parse_packet(IP_packet_v1), 30)

fragments = router.fragment_IP_packet(r1.parse_packet(IP_packet_v1), 20)

print("MTU es más grande: ", fragment)
print("MTU es más pequeño: ", fragments)
