#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer

class HIDGatewayRequestHandler(BaseHTTPRequestHandler):
  def do_GET(self):
    self.send_response(404)
    self.send_header('Content-Type', 'text/html; charset=utf8')
    self.end_headers()
    message = '404 Not Found\n'
    self.wfile.write(bytes(message, 'utf8'))


def main():
  print('Zero HID Gateway by Kenneth Falck <kennu@iki.fi> 2019')
  server_address = ('0.0.0.0', 8088)
  server = HTTPServer(server_address, HIDGatewayRequestHandler)
  server.serve_forever()

if __name__ == '__main__':
  main()
