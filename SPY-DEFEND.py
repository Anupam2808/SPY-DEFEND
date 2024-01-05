import tkinter as tk
from tkinter import ttk
import asyncio
import psutil
import subprocess

async def get_process_name_by_port(port):
    try:
        connections = psutil.net_connections(kind='inet')
        for conn in connections:
            if conn.laddr.port == port and conn.status == 'LISTEN':
                process = psutil.Process(conn.pid)
                return process.name()
    except Exception as e:
        print(f"Error getting process name: {e}")
    return "Unknown Process"

async def get_connection_info_by_port(port):
    try:
        connections = psutil.net_connections(kind='inet')
        for conn in connections:
            if conn.laddr.port == port:
                return conn.status, conn.raddr.ip if conn.raddr else "Unknown", conn.raddr.port if conn.raddr else "Unknown"
    except Exception as e:
        print(f"Error getting connection info: {e}")
    return "Unknown Status", "Unknown IP/Domain", "Unknown Port"

async def check_port(port, app):
    try:
        reader, writer = await asyncio.open_connection('127.0.0.1', port)
        process_name = await get_process_name_by_port(port)
        connection_status, connected_to, connected_port = await get_connection_info_by_port(port)
        print(f"Port {port} is open. Process: {process_name}, Connection Status: {connection_status}, Connected To: {connected_to}:{connected_port}")
        app.update_table(port, "Open", process_name, connection_status, f"{connected_to}:{connected_port}")
        
    except Exception as e:
        app.update_table(port, "Closed", "", "Unknown Status", "Unknown IP/Domain")

async def stop_port(port):
    try:
        command = f"netstat -ano | findstr LISTENING | findstr :{port}"
        process_info = subprocess.check_output(command, shell=True, text=True).strip()

        if process_info:
            pid = process_info.split()[-1]
            try:
                subprocess.run(f"taskkill /F /PID {pid}", shell=True, check=True)
                print(f"Process with PID {pid} terminated.")
            except subprocess.CalledProcessError:
                print(f"Failed to terminate process with PID {pid}.")
        else:
            print(f"No processes found on port {port}.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

async def scan_ports(start_port, end_port, app):
    tasks = [check_port(port, app) for port in range(start_port, end_port + 1)]
    await asyncio.gather(*tasks)

async def continuous_port_monitoring(start_port, end_port, app):
    while True:
        await scan_ports(start_port, end_port, app)
        break

async def non_continuous_port_monitoring(start_port, end_port, app):
    await scan_ports(start_port, end_port, app)

class PortScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Port Scanner")
        self.root.geometry("900x400")  # Adjusted the size to fit the new column
        self.root.resizable(True, True)

        self.create_widgets()

    def create_widgets(self):
        # Table view with scrollbar
        columns = ("Port", "Status", "Process Name", "Connection Status", "Connected To")  # Added new columns
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)  # Adjusted the width of the columns
        self.tree.pack(pady=10, expand=True, fill="both")

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Buttons
        scan_button = tk.Button(self.root, text="Scan Ports", command=self.scan_ports)
        scan_button.pack(side=tk.LEFT, padx=10)

        stop_button = tk.Button(self.root, text="Force Stop Service", command=self.stop_selected_port)
        stop_button.pack(side=tk.LEFT, padx=10)

        #non_continuous_scan_button = tk.Button(self.root, text="Non-Continuous Scan", command=self.non_continuous_scan_ports)
        #non_continuous_scan_button.pack(side=tk.LEFT, padx=10)

        # Event binding
        self.tree.bind("<ButtonRelease-1>", self.on_tree_click)

    def clear_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def update_table(self, port, status, process_name="", connection_status="", connected_to=""):
        if status == "Open":
            self.tree.insert("", "end", values=(port, status, process_name, connection_status, connected_to))

    def stop_selected_port(self):
        selected_item = self.tree.selection()
        if selected_item:
            port = self.tree.item(selected_item, "values")[0]
            asyncio.run(stop_port(port))

    def on_tree_click(self, event):
        item = self.tree.identify_row(event.y)
        self.tree.selection_set(item)

    def scan_ports(self):
        self.clear_table()
        start_port = 1
        end_port = 9999
        asyncio.run(continuous_port_monitoring(start_port, end_port, self))

    def non_continuous_scan_ports(self):
        self.clear_table()
        start_port = 1
        end_port = 9999
        asyncio.run(non_continuous_port_monitoring(start_port, end_port, self))

if __name__ == "__main__":
    root = tk.Tk()
    app = PortScannerApp(root)
    root.mainloop()
