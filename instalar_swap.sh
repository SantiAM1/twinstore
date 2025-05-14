#!/bin/bash

# Crear archivo swap de 1GB
sudo fallocate -l 1G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=1024

# Asignar permisos correctos
sudo chmod 600 /swapfile

# Marcarlo como espacio swap
sudo mkswap /swapfile

# Activarlo
sudo swapon /swapfile

# Verificar que esté activo
sudo swapon --show

# Agregar entrada a /etc/fstab para persistencia tras reinicio
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Ajustar uso de swap (menos agresivo)
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

echo "✅ Swap de 1GB activado y configurado correctamente."
