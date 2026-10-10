#!/usr/bin/env python3
"""
Hub de Iniciativas Digitais — Servidor Local
=============================================
Execute este script para abrir o hub no navegador:
    python3 iniciar_hub.py

O servidor roda em http://localhost:8080 e recarrega o CSV
automaticamente a cada acesso — sem precisar reiniciar.
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import threading
import time

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def log_message(self, format, *args):
        # Mensagem amigável no terminal
        if "200" in str(args):
            print(f"  ✓ {args[0]}")
        elif "404" in str(args):
            print(f"  ✗ Não encontrado: {args[0]}")


def abrir_browser():
    time.sleep(0.8)
    url = f"http://localhost:{PORT}/hub_de_iniciativas_digitais.html"
    webbrowser.open(url)
    print(f"\n  🌐 Abrindo: {url}")


if __name__ == "__main__":
    os.chdir(DIRECTORY)

    print("\n" + "=" * 55)
    print("  HUB DE INICIATIVAS DIGITAIS — Servidor Local")
    print("=" * 55)
    print(f"\n  📂 Pasta: {DIRECTORY}")
    print(f"  🔗 URL:   http://localhost:{PORT}/hub_de_iniciativas_digitais.html")
    print(f"\n  Pressione Ctrl+C para encerrar.\n")

    threading.Thread(target=abrir_browser, daemon=True).start()

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n  ✋ Servidor encerrado. Até logo!\n")
            sys.exit(0)
