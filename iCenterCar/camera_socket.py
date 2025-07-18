from maix import camera, time, display
import socket
import gc
import threading

cam = camera.Camera(512, 320)
disp = display.Display()

INDEX_HTML = """HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Connection: close

<html>
  <head><meta charset="utf-8"><title>MaixCam Stream</title></head>
  <body>
    <h3>实时视频</h3>
    <img src="/stream" width="512" height="320">
  </body>
</html>
"""

def handle_client(conn, addr):
    try:
        req = conn.recv(1024).decode('utf-8')
        print(f"[{addr}] Request: {req.splitlines()[0]}")

        if "GET /stream " in req:
            # MJPEG 视频流响应
            conn.send(b"HTTP/1.1 200 OK\r\n")
            conn.send(b"Content-Type: multipart/x-mixed-replace; boundary=maix_frame\r\n\r\n")

            while True:
                try:
                    img = cam.read()
                    disp.show(img)

                    jpeg = img.compress(quality=70)
                    # 如果compress返回的是Image对象，转成bytes
                    if hasattr(jpeg, "to_bytes"):
                        jpeg = jpeg.to_bytes()

                    if not jpeg:
                        print("Error: JPEG compression failed")
                        break

                    header = (
                        b"--maix_frame\r\n"
                        b"Content-Type: image/jpeg\r\n"
                        b"Content-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n"
                    )
                    conn.sendall(header)
                    conn.sendall(jpeg)
                    conn.sendall(b"\r\n")

                    time.sleep_ms(33)  # ~30 FPS
                    gc.collect()
                except Exception as e:
                    print(f"Stream error: {e}")
                    break

        elif "GET / " in req:
            # 返回 HTML 页面
            conn.send(INDEX_HTML.encode('utf-8'))

        else:
            # 404 Not Found
            conn.send(b"HTTP/1.1 404 Not Found\r\n\r\n")

    except Exception as e:
        print(f"Client error: {str(e)}")
    finally:
        print(f"Closing connection from {addr}")
        conn.close()

HOST, PORT = "0.0.0.0", 8080
srv = socket.socket()
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind((HOST, PORT))
srv.listen(5)
print(f"HTTP/MJPEG server running at http://{HOST}:{PORT}/")

while True:
    conn, addr = srv.accept()
    print(f"Client connected: {addr}")
    t = threading.Thread(target=handle_client, args=(conn, addr))
    t.daemon = True
    t.start()