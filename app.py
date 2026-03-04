from flask import Flask, request, send_file, jsonify, render_template
import subprocess
import os
import tempfile
import re

app = Flask(__name__)


# HELPERS

def es_url_de_youtube_valida(url):
    patron = r'(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w\-]+'
    return bool(re.match(patron, url))

def obtener_url_del_body():
    datos = request.get_json()
    return datos.get('url', '').strip()


# RUTAS

@app.route('/')
def pagina_principal():
    return render_template('index.html')


@app.route('/info', methods=['POST'])
def obtener_info_del_video():
    url = obtener_url_del_body()

    if not url or not es_url_de_youtube_valida(url):
        return jsonify({'error': 'URL de YouTube inválida.'}), 400

    try:
        # Llama a yt-dlp como comando del sistema para obtener el título
        resultado = subprocess.run(
            ['yt-dlp', '--get-title', '--get-thumbnail', url],
            capture_output=True, text=True, timeout=30
        )
        lineas = resultado.stdout.strip().split('\n')
        titulo    = lineas[0] if len(lineas) > 0 else 'Sin título'
        thumbnail = lineas[1] if len(lineas) > 1 else ''

        return jsonify({
            'title':     titulo,
            'thumbnail': thumbnail,
            'channel':   '',
            'duration':  0,
        })

    except Exception as error:
        return jsonify({'error': str(error)}), 500


@app.route('/download', methods=['POST'])
def descargar_como_mp3():
    url = obtener_url_del_body()

    if not url or not es_url_de_youtube_valida(url):
        return jsonify({'error': 'URL de YouTube inválida.'}), 400

    carpeta_temporal = tempfile.mkdtemp()

    try:
        # Llama a yt-dlp como comando del sistema
        subprocess.run([
            'yt-dlp',
            '-x',                            # extrae solo el audio
            '--audio-format', 'mp3',         # convierte a mp3
            '--audio-quality', '192K',       # calidad 192kbps
            '--geo-bypass',              # ignora restricciones geográficas
            '-o', os.path.join(carpeta_temporal, '%(title)s.%(ext)s'),  # carpeta de salida
            url
        ], check=True, timeout=300)          # espera hasta 5 minutos

        # Buscamos el archivo .mp3 generado
        archivo_mp3 = next(
            (os.path.join(carpeta_temporal, f)
             for f in os.listdir(carpeta_temporal)
             if f.endswith('.mp3')),
            None
        )

        if not archivo_mp3:
            return jsonify({'error': 'No se pudo generar el archivo MP3.'}), 500

        titulo = os.path.basename(archivo_mp3).replace('.mp3', '')

        # Manda el archivo al navegador como descarga
        return send_file(
            archivo_mp3,
            as_attachment=True,
            download_name=f"{titulo}.mp3",
            mimetype='audio/mpeg'
        )

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'La descarga tardó demasiado.'}), 500
    except subprocess.CalledProcessError as error:
        return jsonify({'error': f'Error al descargar: {str(error)}'}), 500
    except Exception as error:
        return jsonify({'error': str(error)}), 500



# ARRANCAR EL SERVIDOR

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, threaded=True, host='0.0.0.0', port=port)
