NOTE: This project is partially a test of ChatGPT+AutoGPT.

# DBTS-Agent

The DBTS (Deer Brook Technical Services) Agent is a simple Python-based client-server system that enables the execution of tasks on connected clients. The server keeps track of clients' check-ins and task statuses, while the clients check in periodically to receive tasks.

## Features

- Centralized server for managing client check-ins and tasks
- SQLite3 database for storing client and task information
- Simple JSON-based messaging system for communication between clients and the server
- Lightweight and easy-to-understand codebase

## Prerequisites

- Python 3.9+

## Installation

1. Clone the repository:
```
git clone https://github.com/zwatkins15/dbts-mon.git
cd dbts-mon
```
2. (Optional) Set up a virtual environment to isolate dependencies:
```
python -m venv venv
source venv/bin/activate # On Windows, use venv\Scripts\activate
```

## Usage

1. Run the server script:
```
python server.py
```
This will start the server and create an SQLite3 database file if it doesn't already exist.

2. In a separate terminal, run the client script:
```
python client.py
```
This will make the client check in with the server and receive any pending tasks.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
