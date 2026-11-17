# Test del paso 3
from router import * 
import random

datos1 = Paquete(ip="127.0.0.1", puerto=8881, ttl=64, tamaño=69, Id=1, Offset=0, Flag=0, 
                 mensaje=b"hola las veces que se cuentan en la ola son muchas olas al decir hola")

datos2 = Paquete(ip="127.0.0.1", puerto=8881, ttl=64, tamaño=53, Id=2, Offset=0, Flag=0,
                 mensaje=b"como decir paralelepipedo sin decir bipedo ni niptero") 

#ordenadas
list1 = fragment_IP_packet(datos1, 35)
list2 = fragment_IP_packet(datos2, 30)

#desordenadas
l1_d = list1.copy()
l2_d = list2.copy()

random.seed(421231)
random.shuffle(l1_d)
random.shuffle(l2_d)

print(l1_d)
print(l2_d)


#intercaladas
l3 = []
for i in range(max(len(list1), len(list2))):
    if i < len(list1):
        l3.append(list1[i])

    if i < len(list2):
        l3.append(list2[i])

if __name__ == "__main__":
    router_dicc = {}
    addrs = "127.0.0.1"
    port = 8881
    router_address = (addrs, port)
    print("Veamos los casos ordenados")
    print("1")
    for data_packet in list1:
        destination_address: tuple[str, int] = (data_packet.ip, data_packet.puerto)

        if destination_address == router_address:
            if data_packet.Id not in router_dicc:
                router_dicc[data_packet.Id] = []
            
            router_dicc[data_packet.Id].append(data_packet)

            obtained = reassemble_IP_packet(router_dicc[data_packet.Id])
            if obtained is not None:
                print(f"Se reemsambló el paquete original a partir de {router_dicc[1]}")
                print("datos1 = reassembled1_ord ? {}".format(datos1 == obtained))
    # vemos si 2 funciona bien considerando que ya tiene a 1 entremedio
    print("2")
    for data_packet in list2:
        destination_address: tuple[str, int] = (data_packet.ip, data_packet.puerto)

        if destination_address == router_address:
            if data_packet.Id not in router_dicc:
                router_dicc[data_packet.Id] = []
            
            router_dicc[data_packet.Id].append(data_packet)

            obtained = reassemble_IP_packet(router_dicc[data_packet.Id])
            if obtained is not None:
                print(f"Se reemsambló el paquete original a partir de {router_dicc[2]}")
                print("datos2 = reassembled2_ord ? {}".format(datos2 == obtained))
    print("")
    print("")

    print("Veamos los casos desordenados")
    print("1")
    # ahora vamos con el desordenado
    router_dicc = {}
    for data_packet in l1_d:
        destination_address: tuple[str, int] = (data_packet.ip, data_packet.puerto)

        if destination_address == router_address:
            if data_packet.Id not in router_dicc:
                router_dicc[data_packet.Id] = []

            router_dicc[data_packet.Id].append(data_packet)

            obtained = reassemble_IP_packet(router_dicc[data_packet.Id])
            if obtained is not None:
                print(f"Se reemsambló el paquete original a partir de {l1_d}")
                print("datos1 = reassembled1_des ? {}".format(datos1 == obtained))
    print("2")
    # vemos si 2 funciona bien considerando que ya tiene a 1 entremedio desordenado
    for data_packet in l2_d:
        destination_address: tuple[str, int] = (data_packet.ip, data_packet.puerto)

        if destination_address == router_address:
            if data_packet.Id not in router_dicc:
                router_dicc[data_packet.Id] = []

            router_dicc[data_packet.Id].append(data_packet)

            obtained = reassemble_IP_packet(router_dicc[data_packet.Id])
            if obtained is not None:
                print(f"Se reemsambló el paquete original a partir de {l2_d}")
                print("datos2 = reassembled2_des ? {}".format(datos2 == obtained))
    print("")
    print("")
    print("Veamos el caso intercalado ordenado")
    router_dicc = {}
    a = [datos1, datos2]
    #finalmente vemos el intercalado
    for data_packet in l3:
        destination_address: tuple[str, int] = (data_packet.ip, data_packet.puerto)

        if destination_address == router_address:
            if data_packet.Id not in router_dicc:
                router_dicc[data_packet.Id] = []

            router_dicc[data_packet.Id].append(data_packet)
            #print(router_dicc[data_packet.Id])
            obtained = reassemble_IP_packet(router_dicc[data_packet.Id])
            if obtained is not None:
                print(f"Se reemsambló el paquete original{data_packet.Id} a partir de {l3}")
                print(f"datos{data_packet.Id} = reassembled_inter{data_packet.Id} ? {(a[data_packet.Id-1] == obtained)}")
                print("")


