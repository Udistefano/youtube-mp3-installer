from flask import Flask, request, send_file, jsonify, render_template
import yt_dlp
import os
import tempfile
import re

app = Flask(__name__)

# HELPERS

#Verifica que la URL sea de YouTube antes de intentar descargar algo.
def es_url_de_youtube_valida(url):
    patron = r'(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w\-]+'
    return bool(re.match(patron, url))


# lee el JSON que manda el navegador y extrae el campo 'url'.
def obtener_url_del_body():
    datos = request.get_json()
    return datos.get('url', '').strip()


# RUTAS

@app.route('/')
def pagina_principal():
    return render_template('index.html')


# recibe la URL del video, obtiene sus metadatos y se los devuelve al navegador.
@app.route('/info', methods=['POST'])
def obtener_info_del_video():
    url = obtener_url_del_body()

    if not url or not es_url_de_youtube_valida(url):
        return jsonify({'error': 'URL de YouTube inválida.'}), 400

    opciones = {
        'quiet': True,        # no imprime logs en la terminal
        'no_warnings': True,  # tampoco advertencias
    }

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            # download=False → solo trae metadatos, no descarga el video
            info = ydl.extract_info(url, download=False)

        return jsonify({
            'title':     info.get('title',    'Sin título'),
            'channel':   info.get('uploader', 'Desconocido'),
            'thumbnail': info.get('thumbnail', ''),
            'duration':  info.get('duration',  0),
        })

    except Exception as error:
        return jsonify({'error': str(error)}), 500


# descarga el audio del video, lo convierte a MP3 y se lo envía al navegador para que lo descargue.
@app.route('/download', methods=['POST'])
def descargar_como_mp3():
    url = obtener_url_del_body()

    if not url or not es_url_de_youtube_valida(url):
        return jsonify({'error': 'URL de YouTube inválida.'}), 400

    # Creamos una carpeta temporal para guardar el MP3 mientras lo procesamos
    carpeta_temporal = tempfile.mkdtemp()

    opciones_descarga = {
        # Descarga solo el audio en la mejor calidad disponible
        'format': 'bestaudio/best',

        # Nombre del archivo de salida: usa el título del video
        'outtmpl': os.path.join(carpeta_temporal, '%(title)s.%(ext)s'),

        'quiet': True,
        'no_warnings': True,

        # Le pedimos a ffmpeg que convierta el audio a MP3 a 192kbps
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(opciones_descarga) as ydl:
            # download=True → esta vez sí descarga y convierte el archivo
            info = ydl.extract_info(url, download=True)
            titulo = info.get('title', 'audio')

        # Buscamos el archivo .mp3 que generó ffmpeg en la carpeta temporal
        archivo_mp3 = next(
            (os.path.join(carpeta_temporal, archivo)
             for archivo in os.listdir(carpeta_temporal)
             if archivo.endswith('.mp3')),
            None  # si no encuentra nada, devuelve None
        )

        if not archivo_mp3:
            return jsonify({'error': 'No se pudo generar el archivo MP3.'}), 500

        # Mandamos el archivo al navegador como descarga
        return send_file(
            archivo_mp3,
            as_attachment=True,          
            download_name=f"{titulo}.mp3",
            mimetype='audio/mpeg'
        )

    except Exception as error:
        return jsonify({'error': str(error)}), 500


if __name__ == '__main__':
    app.run(debug=True)