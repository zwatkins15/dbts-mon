import sqlite3
import socket
import json
import threading
import time
import signal
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

# Define constants
DATABASE_NAME = 'clients.db'
SERVER_PORT = 1234
WEB_PORT = 8080
LOG_FILE = 'server.log'

# Initialize log file
def initialize_log():
    with open(LOG_FILE, 'a') as f:
        f.write('--- Server Log ---\n')

# Write log message
def log(message):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    log_message = '[{}] {}\n'.format(timestamp, message)
    print(log_message, end='')
    with open(LOG_FILE, 'a') as f:
        f.write(log_message)

# Create database tables
def initialize_database(db):
    c = db.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clients
                 (id INTEGER PRIMARY KEY, ip_address TEXT, last_check_in INTEGER, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY, client_id INTEGER, command TEXT, arguments TEXT, status TEXT)''')
    db.commit()
    log('Database created')

def handle_client(client_sock, client_addr):
    try:
        log('Client connected from {}'.format(client_addr))

        # Receive check-in message
        data = client_sock.recv(1024)
        if not data:
            log('Client connection closed unexpectedly')
            return

        message = json.loads(data.decode())
        log('Received check-in message from client {}: {}'.format(client_addr, message))
        if message['type'] == 'check_in':
            # Create database connection
            conn = sqlite3.connect(DATABASE_NAME)
            c = conn.cursor()

            # Update client check-in time
            c.execute('SELECT * FROM clients WHERE ip_address = ?', (message['ip_address'],))
            result = c.fetchone()
            if result is None:
                c.execute('INSERT INTO clients (ip_address, last_check_in, status) VALUES (?, ?, ?)', (message['ip_address'], int(time.time()), 'active'))
                log('New client added with IP address {}'.format(message['ip_address']))
                # Get the client ID
                c.execute('SELECT * FROM clients WHERE ip_address = ?', (message['ip_address'],))
                result = c.fetchone()
            else:
                c.execute('UPDATE clients SET last_check_in = ? WHERE id = ?', (int(time.time()), result[0]))
                log('Client ID {} updated with check-in time {}'.format(result[0], int(time.time())))

            conn.commit()

            # Send tasks to client
            c.execute('SELECT * FROM tasks WHERE status = ? AND client_id = ?', ('pending', result[0]))
            tasks = c.fetchall()
            if len(tasks) == 0:
                client_sock.sendall('no tasks available'.encode())  # send a message indicating no tasks
            else:
                tasks_json = json.dumps([{'id': task[0], 'command': task[2], 'arguments': task[3]} for task in tasks])
                client_sock.sendall(tasks_json.encode())
                log('Sent tasks to client {}: {}'.format(client_addr, tasks_json))
                log('Tasks sent to client')

            # Close database connection
            conn.close()

        # Receive completion message
        data = client_sock.recv(1024)
        if not data:
            log('Client connection closed unexpectedly')
            return

        message = json.loads(data.decode())
        if message['type'] == 'completion':
            # Create database connection
            conn = sqlite3.connect(DATABASE_NAME)
            c = conn.cursor()

            # Update task status
            c.execute('UPDATE tasks SET status = ? WHERE id = ?', ('completed', message['task_id']))
            conn.commit()
            log('Task {} marked as completed'.format(message['task_id']))

            # Close database connection
            conn.close()
        elif message['type'] == 'check_in_complete':
            log('Client {} check-in complete'.format(client_addr))

        log('Client connection closed')

    except Exception as e:
        log('Error: {}'.format(e))
        log('Client connection closed with error')
    finally:
        client_sock.close()

# Serve web page
class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Serve web page with client and task information
            conn = sqlite3.connect(DATABASE_NAME)
            c = conn.cursor()
            c.execute('SELECT * FROM clients')
            clients = c.fetchall()
            c.execute('SELECT * FROM tasks')
            tasks = c.fetchall()
            conn.close()
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            content = '<html><body><h1>Clients</h1><table><tr><th>ID</th><th>IP Address</th><th>Last Check-in</th><th>Status</th></tr>'
            for client in clients:
                content += '<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(client[0], client[1], time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(client[2])), client[3])
            content += '</table><h1>Tasks</h1><table><tr><th>ID</th><th>Client ID</th><th>Command</th><th>Arguments</th><th>Status</th></tr>'
            for task in tasks:
                content += '<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(task[0], task[1], task[2], task[3], task[4])
            content += '</table></body></html>'
            self.wfile.write(content.encode())
            log('Web page served')

        except Exception as e:
            log('Error: {}'.format(e))
            self.send_error(500)

def start_server():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(('0.0.0.0', SERVER_PORT))
    server_sock.listen()
    log('Server started on port {}'.format(SERVER_PORT))

    # Start web server
    web_server = HTTPServer(('0.0.0.0', WEB_PORT), MyHandler)
    web_thread = threading.Thread(target=web_server.serve_forever)
    web_thread.daemon = True
    web_thread.start()
    log('Web server started on port {}'.format(WEB_PORT))

    return server_sock

# Main function
def main():
    # Initialize database
    db = sqlite3.connect(DATABASE_NAME)
    initialize_database(db)

    # Start server socket
    server_sock = start_server()

    # Handle incoming client connections
    while True:
        try:
            client_sock, client_addr = server_sock.accept()
            log('Client connection accepted from {}'.format(client_addr))
            threading.Thread(target=handle_client, args=(client_sock, client_addr)).start()

        except KeyboardInterrupt:
            log('Server shutting down...')
            server_sock.close()
            sys.exit(0)

if __name__ == '__main__':
    main()
