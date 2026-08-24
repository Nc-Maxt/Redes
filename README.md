# Redes

## Cómo correr el servidor en la VM (VirtualBox)

Para que el servidor sea alcanzable desde fuera de la VM (por ejemplo desde el navegador del host), la VM necesita estar en modo Adaptador Puente, no NAT.

1. Apaga la VM.
2. En VirtualBox ve a Configuración de la VM, luego Red, luego Adaptador 1, y en "Conectado a" elige Adaptador puente. Selecciona tu interfaz de red física (WiFi o Ethernet).
3. Enciende la VM.
4. Dentro de la VM abre una terminal y corre `ip a` para ver tu IP. Busca la interfaz que no sea `lo` (normalmente `enp0s3`), y anota la IP que aparece ahí, por ejemplo `192.168.1.50`. Esta es la IP_VM.
5. Corre el servidor con `python3 servidor_HTTP.py` y cuando pida el host, ingresa la IP_VM que anotaste.
6. Desde el navegador de tu máquina host, entra a `http://IP_VM:8000` reemplazando IP_VM por la IP real.
