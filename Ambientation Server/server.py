import socket
import threading
import subprocess
import time

HOST = '192.168.0.101'
PORT = 5000

clients = set()
CHUNK = 2048


def start_librespot():
    """Starts the librespot process with a pipe backend."""
    librespot_command = [
        "librespot",
        "--name", "Ambientation Server",
        "--backend", "pipe",
        "--bitrate", "320",
        "--device-type", "speaker"
    ]

    process = subprocess.Popen(
        librespot_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(10)
    return process


def handle_client(client_socket):
    """Handles communication with a connected client."""
    clients.add(client_socket)
    while True:
        try:
            time.sleep(1)
        except Exception as e:
            print(f"Error in client handling: {e}")
            cleanup_client(client_socket)
            break

    client_socket.close()


def cleanup_client(client_socket):
    if client_socket in clients:
        clients.remove(client_socket)
        client_socket.close()
        print(f"Client {client_socket.getpeername()} disconnected.")


def start_server():
    """Starts the audio streaming server."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f'Server is listening on {HOST}:{PORT}')

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f'New client connected from {client_address}')
            client_thread = threading.Thread(
                target=handle_client, args=(client_socket,))
            client_thread.start()
    except KeyboardInterrupt:
        print("Shutting down Ambientation Server")
    finally:
        server_socket.close()
        print("Ambientation Server closed")


def stream_audio(librespot_process):
    """Streams audio from the librespot process to connected clients."""
    while True:
        try:
            data = librespot_process.stdout.read(CHUNK)
            if not data:
                break

            for client in list(clients):
                try:
                    client.sendall(data)
                except Exception as e:
                    print(f"Error sending data to client: {e}")
                    cleanup_client(client)
        except Exception as e:
            print(f"Error reading from librespot: {e}")
            break


if __name__ == '__main__':
    librespot_process = start_librespot()

    threading.Thread(target=stream_audio, args=(
        librespot_process,), daemon=True).start()
    start_server()

    librespot_process.wait()
