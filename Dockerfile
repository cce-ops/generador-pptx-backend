# Backend de compilación LaTeX + Python para Render
FROM python:3.11-slim

# Instalar dependencias del sistema: XeLaTeX + fuentes + python-pptx deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-xetex \
    texlive-fonts-recommended \
    texlive-lang-spanish \
    fonts-noto \
    fonts-dejavu \
    latexmk \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la API
COPY app.py .

# Puerto que expone Render
EXPOSE 10000

# Comando de inicio con gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--workers", "2", "--timeout", "300", "app:app"]