"""
API de compilación para Generador PPTX
- POST /compile/latex  -> compila .tex a PDF (XeLaTeX)
- POST /compile/python -> ejecuta .py y devuelve .pptx (python-pptx)
- GET  /health         -> health check
"""
import io
import os
import tempfile
import subprocess
import shutil
from pathlib import Path
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "generador-pptx-compiler"})

@app.route('/compile/latex', methods=['POST'])
def compile_latex():
    """
    Recibe: { "latex": "código latex...", "filename": "presentacion" }
    Devuelve: PDF binario
    """
    data = request.get_json()
    if not data or 'latex' not in data:
        return jsonify({"error": "Falta campo 'latex'"}), 400

    latex_code = data['latex']
    filename = data.get('filename', 'presentacion')

    # Crear directorio temporal
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        tex_file = tmpdir / f"{filename}.tex"
        pdf_file = tmpdir / f"{filename}.pdf"

        # Escribir archivo .tex
        tex_file.write_text(latex_code, encoding='utf-8')

        # Compilar con XeLaTeX (2 pasadas para referencias/TOC)
        for pass_num in range(2):
            result = subprocess.run(
                ['xelatex', '-interaction=nonstopmode', '-output-directory', str(tmpdir), str(tex_file)],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode != 0:
                # Log para debug
                log_file = tmpdir / f"{filename}.log"
                log_content = log_file.read_text(encoding='utf-8', errors='ignore') if log_file.exists() else result.stderr
                return jsonify({
                    "error": "Error compilando LaTeX",
                    "details": log_content[-3000:]  # últimos 3000 chars
                }), 500

        # Verificar que se generó el PDF
        if not pdf_file.exists():
            return jsonify({"error": "No se generó el PDF"}), 500

        # Leer y devolver PDF
        pdf_data = pdf_file.read_bytes()
        return send_file(
            io.BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{filename}.pdf"
        )

@app.route('/compile/python', methods=['POST'])
def compile_python():
    """
    Recibe: { "python": "código python...", "filename": "presentacion" }
    Devuelve: .pptx binario
    """
    data = request.get_json()
    if not data or 'python' not in data:
        return jsonify({"error": "Falta campo 'python'"}), 400

    python_code = data['python']
    filename = data.get('filename', 'presentacion')

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        py_file = tmpdir / f"{filename}.py"
        pptx_file = tmpdir / f"{filename}.pptx"

        # Escribir archivo .py
        py_file.write_text(python_code, encoding='utf-8')

        # Ejecutar Python
        result = subprocess.run(
            ['python', str(py_file)],
            cwd=str(tmpdir),
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            return jsonify({
                "error": "Error ejecutando Python",
                "details": result.stderr[-3000:]
            }), 500

        # Verificar que se generó el PPTX
        if not pptx_file.exists():
            # Buscar cualquier .pptx en el directorio
            pptx_files = list(tmpdir.glob('*.pptx'))
            if not pptx_files:
                return jsonify({"error": "No se generó el .pptx", "stdout": result.stdout}), 500
            pptx_file = pptx_files[0]

        # Leer y devolver PPTX
        pptx_data = pptx_file.read_bytes()
        return send_file(
            io.BytesIO(pptx_data),
            mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
            as_attachment=True,
            download_name=f"{filename}.pptx"
        )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)