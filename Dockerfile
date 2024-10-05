# Usar una imagen base de Python 3 slim
FROM python:3-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /programas/api-trymicro3

# Instalar las dependencias necesarias: Flask, pymongo y requests
RUN pip3 install flask pymongo requests

# Copiar todos los archivos de la aplicación al contenedor
COPY . .

# Exponer el puerto 8003 para Flask
EXPOSE 8003

# Definir el comando que ejecutará el contenedor
CMD [ "python3", "./microservicio3.py" ]
