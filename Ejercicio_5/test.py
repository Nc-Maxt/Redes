import router

IP_packet_v1 = b"127.0.0.18882hola"
parsed_IP_packet = router.parse_packet(IP_packet_v1)
IP_packet_v2 = router.create_packet(parsed_IP_packet)
print("IP_packet_v1 == IP_packet_v2 ? {}".format(IP_packet_v1 == IP_packet_v2))
