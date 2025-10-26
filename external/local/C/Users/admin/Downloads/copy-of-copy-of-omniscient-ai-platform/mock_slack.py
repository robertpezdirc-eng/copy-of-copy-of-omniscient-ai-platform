import http.server
import socketserver

class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', '0'))
        body = self.rfile.read(length)
        print("=== Mock Slack webhook received ===")
        print(body.decode('utf-8'))
        try:
            with open("/data/mock_slack.log", "ab") as f:
                f.write(b"=== Mock Slack webhook received ===\n")
                f.write(body)
                f.write(b"\n")
        except Exception as e:
            print(f"Failed to write log: {e}")
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"ok": true}')
    def log_message(self, fmt, *args):
        # Suppress default HTTP server logging to keep output clean
        return

if __name__ == "__main__":
    with socketserver.TCPServer(("", 9001), Handler) as httpd:
        print("Mock Slack webhook listening on :9001")
        httpd.serve_forever()