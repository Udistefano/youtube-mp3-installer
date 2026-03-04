# Usamos Python 3.12 como base
FROM python:3.12-slim

# Instalamos ffmpeg y yt-dlp del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

# Creamos la carpeta de trabajo
WORKDIR /app

# Copiamos e instalamos las dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del proyecto
COPY . .

# Puerto que usa Flask
EXPOSE 5000

# Comando para arrancar la app
CMD ["python", "app.py"]