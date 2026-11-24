"""Local test server with the right file types for WebAssembly.
Run inside the offline_app folder:  python serve.py
Open:  http://localhost:8080
"""
import mimetypes
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

mimetypes.add_type("application/wasm", ".wasm")
mimetypes.add_type("text/javascript", ".mjs")
mimetypes.add_type("application/manifest+json", ".webmanifest")

class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

if __name__ == "__main__":
    print("Serving on http://localhost:8080  (Ctrl+C to stop)")
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
