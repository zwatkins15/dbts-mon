import socket
import json
import subprocess
import os
import sys

# Define constants
SERVER_IP = '127.0.0.1'  # Change this to the IP address of the server
SERVER_PORT = 1234

def execute_task(task):
    try:
        if 'arguments' in task and task['arguments'] is not None:
            arguments = json.loads(task['arguments'])
            result = subprocess.run([task['command']] + arguments, capture_output=True)
        else:
            result = subprocess.run([task['command']], capture_output=True)

        print('Task {} completed'.format(task['id']))
        return True
    except Exception as e:
        print('Error executing task {}: {}'.format(task['id'], e))
        return False

def main():
    try:
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_sock.connect((SERVER_IP, SERVER_PORT))

        # Send check-in message
        check_in_message = json.dumps({'type': 'check_in', 'ip_address': client_sock.getsockname()[0]})
        client_sock.sendall(check_in_message.encode())

        # Receive tasks
        data = client_sock.recv(1024)
        if not data:
            print('Server connection closed unexpectedly')
            sys.exit(1)

        tasks_str = data.decode()
        if tasks_str == 'no tasks available':
            print('No tasks available')
        else:
            tasks = json.loads(tasks_str)
            print('Received tasks: {}'.format(tasks))

            # Execute tasks
            for task in tasks:
                if execute_task(task):
                    # Send completion message
                    completion_message = json.dumps({'type': 'completion', 'task_id': task['id']})
                    client_sock.sendall(completion_message.encode())

        # Send check-in complete message
        check_in_complete_msg = {'type': 'check_in_complete'}
        client_sock.sendall(json.dumps(check_in_complete_msg).encode())

        client_sock.close()

    except Exception as e:
        print('Error: {}'.format(e))

if __name__ == '__main__':
    main()
