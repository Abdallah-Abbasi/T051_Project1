
from socket import gethostbyname, socket, AF_INET, SOCK_STREAM, gethostname

mainAddress = (gethostbyname(gethostname()), 9991)

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(mainAddress)
serverSocket.listen()

print("The server is up!")
print(f"Listening to http://{mainAddress[0]}:{mainAddress[1]}")

def notFoundHtmlText(file, addr):
    return f"""
            <html>
                <head><title>Error 404</title></head>
                <body>
                    <h1 style='color: red;'>The file "{file}" is not found</h1>
                    <p><b>1192316 - Jamal Shehadeh<br />1232951 - Abdallah Ababsi</p>
                    <p>Client IP: {addr[0]}</p>
                    <p>Client Port: {addr[1]}</p>
                </body>
            </html>
        """

def HttpResponse(code, status, type, body):
    return (f"HTTP/1.1 {code} {status}\r\n"
        f"Content-Type: {type}; charset=utf-8\r\n"
        f"Content-Length: {len(body)}\r\n\r\n").encode() + body

def readFile(filePath, connectionSocket, addr):
    try:
        file = open(f"static/{filePath}", "rb")
        return file.read()
    except OSError:
        ext = filePath.lower().split('.')[-1]
        if ext in ('png', 'jpg', 'jpeg', 'gif'):
            url = f"https://www.google.com/search?q={filePath}&tbm=isch"
            connectionSocket.send(
                f"HTTP/1.1 307 Temporary Redirect\r\nLocation: {url}\r\n\r\n".encode()
            )
            print("→ 307 Temporary Redirect")
        elif ext in ('mp4', 'webm'):
            url = f"https://www.google.com/search?q={filePath}&tbm=vid"
            connectionSocket.send(
                f"HTTP/1.1 307 Temporary Redirect\r\nLocation: {url}\r\n\r\n".encode()
            )
            print("→ 307 Temporary Redirect")
        else:
            connectionSocket.send(
                HttpResponse(404, "Not Found", "text/html",
                notFoundHtmlText(filePath, addr).encode())
            )
            print("→ 404 Not Found")
        return

while True:
    try:
        connectionSocket, addr = serverSocket.accept()
        request = connectionSocket.recv(2048).decode()

        if not request or len(request) == 0:
            print("Heartbeating....")
            continue

        print("----------------------------------------------")
        print("Request From " + str(addr))
        print(request)

        lines = request.split("\r\n")

        requestLine = lines[0].strip()
        method, fullPath, version = requestLine.split(" ")

        pathParts = fullPath.split("?")
        hasQueryParams = len(pathParts) != 1
        path = pathParts[0] if hasQueryParams else fullPath

        path = path[:-1] if path.endswith("/") and len(path) != 1 else path

        if path == '/' or path.startswith(('/index.html', '/en')):
            htmlText = readFile("main_en.html", connectionSocket, addr)
            if htmlText:
                connectionSocket.send(HttpResponse(200, "OK", "text/html", htmlText))
                print("→ 200 OK")

        elif path.startswith('/ar'):
            htmlText = readFile("main_ar.html", connectionSocket, addr)
            if htmlText:
                connectionSocket.send(HttpResponse(200, "OK", "text/html", htmlText))
                print("→ 200 OK")

        elif path.startswith("/so"):
            connectionSocket.send("HTTP/1.1 307 Temporary Redirect\r\nLocation: https://stackoverflow.com\r\n\r\n".encode())
            print("→ 307 Temporary Redirect")

        elif path.startswith("/itc"):
            connectionSocket.send("HTTP/1.1 307 Temporary Redirect\r\nLocation: https://itc.birzeit.edu\r\n\r\n".encode())
            print("→ 307 Temporary Redirect")

        elif path.startswith("/getImage") and hasQueryParams:
            params = {}
            keys_values = pathParts[1].split('&')
            for key_value in keys_values:
                if '=' in key_value:
                    key, value = key_value.split('=')
                    params[key] = value

            ImageName = params["imageName"] if "imageName" in params.keys() else pathParts[1]
            connectionSocket.send(f"HTTP/1.1 307 Temporary Redirect\r\nLocation: /{ImageName}\r\n\r\n".encode())
            print("→ 307 Temporary Redirect")

        else:
            fileName = path[1:]
            
            file = readFile(fileName, connectionSocket, addr)
            if file:
                parts = fileName.split(".")

                type = "text"
                fileExtension = "plain"

                if len(parts) >= 2:
                    fileExtension = parts[-1]

                    if fileExtension in ('png', 'jpg', 'jpeg'):
                        type = "image"
                        
                        if fileExtension == "jpg":
                            fileExtension = "jpeg"
                    
                connectionSocket.send(HttpResponse(200, "OK", f"{type}/{fileExtension}", file))
                print("→ 200 OK")
    except OSError:
        print ("IO error")
        connectionSocket.send(HttpResponse(404, "Not Found", "text/html", notFoundHtmlText(path, addr).encode()))
        print("→ 404 Not Found")
    except:
        print("Some Internal Error")
        connectionSocket.send(HttpResponse(500, "Internal Server Error", "text/html", "Internal Server Error".encode()))
    else:
        connectionSocket.close()
        print ("Responded Successfully!")
        print("----------------------------------------------")