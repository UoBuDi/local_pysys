import sys
import os
import subprocess
import threading
import time
import re
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QProgressBar, QTextEdit, QTabWidget
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, Slot
from PySide6.QtGui import QColor, QFont

VERSION = "1.0.0"

BACKEND_PORT = 8000
FRONTEND_PORT = 4000
BACKEND_DIR = r"D:\local_pysys\vue-element-plus-admin-master\backend"
FRONTEND_DIR = r"D:\local_pysys\vue-element-plus-admin-master"


class ProcessInfo:
    def __init__(self, pid: int, port: int, name: str = "", command: str = ""):
        self.pid = pid
        self.port = port
        self.name = name
        self.command = command


class PortMonitorThread(QThread):
    port_status_signal = Signal(int, bool, list)
    
    def __init__(self):
        super().__init__()
        self._is_running = True
    
    def run(self):
        while self._is_running:
            backend_processes = self.get_port_processes(BACKEND_PORT)
            frontend_processes = self.get_port_processes(FRONTEND_PORT)
            
            backend_in_use = len(backend_processes) > 0
            frontend_in_use = len(frontend_processes) > 0
            
            self.port_status_signal.emit(BACKEND_PORT, backend_in_use, backend_processes)
            self.port_status_signal.emit(FRONTEND_PORT, frontend_in_use, frontend_processes)
            
            time.sleep(3)
    
    def get_port_processes(self, port: int) -> list:
        processes = []
        try:
            result = subprocess.run(
                f'netstat -ano | findstr ":{port}" | findstr "LISTENING"',
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                pids = set()
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 5:
                            try:
                                pid = int(parts[-1])
                                pids.add(pid)
                            except ValueError:
                                continue
                
                for pid in pids:
                    process_info = self.get_process_details(pid, port)
                    processes.append(process_info)
        except Exception as e:
            print(f"获取端口{port}进程失败: {e}")
        
        return processes
    
    def get_process_details(self, pid: int, port: int) -> ProcessInfo:
        name = ""
        command = ""
        try:
            result = subprocess.run(
                f'wmic process where ProcessId={pid} get Name,CommandLine /format:list',
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('Name='):
                        name = line.split('=', 1)[1]
                    elif line.startswith('CommandLine='):
                        command = line.split('=', 1)[1]
        except Exception:
            name = "Unknown"
        
        return ProcessInfo(pid, port, name, command)
    
    def stop(self):
        self._is_running = False


class ServiceThread(QThread):
    started_signal = Signal(str)
    stopped_signal = Signal(str)
    error_signal = Signal(str, str)
    log_signal = Signal(str, str)
    
    def __init__(self, service_type: str, work_dir: str, command: str):
        super().__init__()
        self.service_type = service_type
        self.work_dir = work_dir
        self.command = command
        self._is_running = False
        self.process = None
    
    def run(self):
        self._is_running = True
        try:
            self.log_signal.emit(self.service_type, f"正在启动{self.service_type}服务...")
            self.process = subprocess.Popen(
                self.command,
                cwd=self.work_dir,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.started_signal.emit(self.service_type)
            self.log_signal.emit(self.service_type, f"{self.service_type}服务已启动 (PID: {self.process.pid})")
            
            while self._is_running and self.process.poll() is None:
                time.sleep(0.5)
            
            if self.process.poll() is not None:
                self.stopped_signal.emit(self.service_type)
                self.log_signal.emit(self.service_type, f"{self.service_type}服务已停止")
        except Exception as e:
            self.error_signal.emit(self.service_type, str(e))
            self.log_signal.emit(self.service_type, f"启动失败: {e}")
    
    def stop(self):
        self._is_running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                try:
                    self.process.kill()
                except:
                    pass
        self.wait(3000)
        if self.isRunning():
            self.terminate()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.backend_thread = None
        self.frontend_thread = None
        self.port_monitor = None
        self.backend_running = False
        self.frontend_running = False
        self.init_ui()
        self.start_port_monitor()
    
    def init_ui(self):
        self.setWindowTitle(f"服务管理工具 v{VERSION}")
        self.setMinimumSize(900, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        title_label = QLabel(f"前后端服务管理工具 v{VERSION}")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #409EFF; padding: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        control_group = QGroupBox("服务控制")
        control_layout = QHBoxLayout(control_group)
        
        self.backend_btn = QPushButton("启动后端服务")
        self.backend_btn.setMinimumHeight(50)
        self.backend_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.backend_btn.clicked.connect(self.toggle_backend_service)
        control_layout.addWidget(self.backend_btn)
        
        self.frontend_btn = QPushButton("启动前端服务")
        self.frontend_btn.setMinimumHeight(50)
        self.frontend_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.frontend_btn.clicked.connect(self.toggle_frontend_service)
        control_layout.addWidget(self.frontend_btn)
        
        self.restart_all_btn = QPushButton("重启所有服务")
        self.restart_all_btn.setMinimumHeight(50)
        self.restart_all_btn.setStyleSheet("font-size: 14px; font-weight: bold; background-color: #E6A23C;")
        self.restart_all_btn.clicked.connect(self.restart_all_services)
        control_layout.addWidget(self.restart_all_btn)
        
        self.stop_all_btn = QPushButton("停止所有服务")
        self.stop_all_btn.setMinimumHeight(50)
        self.stop_all_btn.setStyleSheet("font-size: 14px; font-weight: bold; background-color: #F56C6C;")
        self.stop_all_btn.clicked.connect(self.stop_all_services)
        control_layout.addWidget(self.stop_all_btn)
        
        layout.addWidget(control_group)
        
        status_group = QGroupBox("端口状态监控")
        status_layout = QVBoxLayout(status_group)
        
        self.status_table = QTableWidget()
        self.status_table.setColumnCount(5)
        self.status_table.setHorizontalHeaderLabels(["端口", "状态", "进程ID", "进程名称", "操作"])
        self.status_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.status_table.setMinimumHeight(200)
        status_layout.addWidget(self.status_table)
        
        refresh_btn = QPushButton("刷新端口状态")
        refresh_btn.clicked.connect(self.refresh_port_status)
        status_layout.addWidget(refresh_btn)
        
        layout.addWidget(status_group)
        
        log_group = QGroupBox("服务日志")
        log_layout = QVBoxLayout(log_group)
        
        tab_widget = QTabWidget()
        
        self.backend_log = QTextEdit()
        self.backend_log.setReadOnly(True)
        self.backend_log.setStyleSheet("font-family: Consolas, monospace; font-size: 12px;")
        tab_widget.addTab(self.backend_log, "后端日志")
        
        self.frontend_log = QTextEdit()
        self.frontend_log.setReadOnly(True)
        self.frontend_log.setStyleSheet("font-family: Consolas, monospace; font-size: 12px;")
        tab_widget.addTab(self.frontend_log, "前端日志")
        
        log_layout.addWidget(tab_widget)
        
        clear_log_btn = QPushButton("清空日志")
        clear_log_btn.clicked.connect(self.clear_logs)
        log_layout.addWidget(clear_log_btn)
        
        layout.addWidget(log_group)
    
    def start_port_monitor(self):
        self.port_monitor = PortMonitorThread()
        self.port_monitor.port_status_signal.connect(self.update_port_status)
        self.port_monitor.start()
    
    @Slot(int, bool, list)
    def update_port_status(self, port: int, in_use: bool, processes: list):
        all_processes = []
        
        for row in range(self.status_table.rowCount()):
            port_item = self.status_table.item(row, 0)
            if port_item:
                existing_port = int(port_item.text())
                if existing_port != port:
                    pid_item = self.status_table.item(row, 2)
                    if pid_item:
                        all_processes.append({
                            'port': existing_port,
                            'pid': int(pid_item.text()) if pid_item.text() != '-' else 0,
                            'name': self.status_table.item(row, 3).text() if self.status_table.item(row, 3) else '',
                            'in_use': self.status_table.item(row, 1).text() == '使用中'
                        })
        
        for proc in processes:
            all_processes.append({
                'port': port,
                'pid': proc.pid,
                'name': proc.name,
                'in_use': in_use
            })
        
        self.status_table.setRowCount(len(all_processes))
        
        for row, proc in enumerate(all_processes):
            port_item = QTableWidgetItem(str(proc['port']))
            port_item.setTextAlignment(Qt.AlignCenter)
            self.status_table.setItem(row, 0, port_item)
            
            status_item = QTableWidgetItem("使用中" if proc['in_use'] else "空闲")
            status_item.setTextAlignment(Qt.AlignCenter)
            if proc['in_use']:
                status_item.setBackground(QColor("#F56C6C"))
                status_item.setForeground(QColor("white"))
            else:
                status_item.setBackground(QColor("#67C23A"))
                status_item.setForeground(QColor("white"))
            self.status_table.setItem(row, 1, status_item)
            
            pid_item = QTableWidgetItem(str(proc['pid']) if proc['pid'] > 0 else "-")
            pid_item.setTextAlignment(Qt.AlignCenter)
            self.status_table.setItem(row, 2, pid_item)
            
            name_item = QTableWidgetItem(proc['name'] if proc['name'] else "-")
            self.status_table.setItem(row, 3, name_item)
            
            if proc['pid'] > 0:
                kill_btn = QPushButton("结束进程")
                kill_btn.setStyleSheet("background-color: #F56C6C; color: white;")
                kill_btn.clicked.connect(lambda checked, p=proc['pid']: self.kill_process(p))
                self.status_table.setCellWidget(row, 4, kill_btn)
            else:
                self.status_table.setItem(row, 4, QTableWidgetItem("-"))
        
        if port == BACKEND_PORT:
            self.backend_running = in_use
            self.update_backend_button()
        elif port == FRONTEND_PORT:
            self.frontend_running = in_use
            self.update_frontend_button()
    
    def update_backend_button(self):
        if self.backend_running:
            self.backend_btn.setText("停止后端服务")
            self.backend_btn.setStyleSheet("font-size: 14px; font-weight: bold; background-color: #F56C6C;")
        else:
            self.backend_btn.setText("启动后端服务")
            self.backend_btn.setStyleSheet("font-size: 14px; font-weight: bold; background-color: #67C23A;")
    
    def update_frontend_button(self):
        if self.frontend_running:
            self.frontend_btn.setText("停止前端服务")
            self.frontend_btn.setStyleSheet("font-size: 14px; font-weight: bold; background-color: #F56C6C;")
        else:
            self.frontend_btn.setText("启动前端服务")
            self.frontend_btn.setStyleSheet("font-size: 14px; font-weight: bold; background-color: #67C23A;")
    
    def toggle_backend_service(self):
        if self.backend_running:
            self.stop_backend_service()
        else:
            self.start_backend_service()
    
    def toggle_frontend_service(self):
        if self.frontend_running:
            self.stop_frontend_service()
        else:
            self.start_frontend_service()
    
    def start_backend_service(self):
        if self.backend_thread and self.backend_thread.isRunning():
            self.add_log("backend", "后端服务已在运行中")
            return
        
        self.backend_thread = ServiceThread(
            "后端",
            BACKEND_DIR,
            "python main.py"
        )
        self.backend_thread.log_signal.connect(self.add_log)
        self.backend_thread.start()
    
    def stop_backend_service(self):
        if self.backend_thread:
            self.backend_thread.stop()
            self.backend_thread = None
        
        self.kill_port_processes(BACKEND_PORT)
        self.add_log("backend", "后端服务已停止")
    
    def start_frontend_service(self):
        if self.frontend_thread and self.frontend_thread.isRunning():
            self.add_log("frontend", "前端服务已在运行中")
            return
        
        self.frontend_thread = ServiceThread(
            "前端",
            FRONTEND_DIR,
            "npm run dev"
        )
        self.frontend_thread.log_signal.connect(self.add_log)
        self.frontend_thread.start()
    
    def stop_frontend_service(self):
        if self.frontend_thread:
            self.frontend_thread.stop()
            self.frontend_thread = None
        
        self.kill_port_processes(FRONTEND_PORT)
        self.add_log("frontend", "前端服务已停止")
    
    def restart_all_services(self):
        self.stop_all_services()
        time.sleep(2)
        self.start_backend_service()
        time.sleep(3)
        self.start_frontend_service()
    
    def stop_all_services(self):
        self.stop_backend_service()
        self.stop_frontend_service()
    
    def kill_port_processes(self, port: int):
        try:
            result = subprocess.run(
                f'netstat -ano | findstr ":{port}" | findstr "LISTENING"',
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                pids = set()
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 5:
                            try:
                                pid = int(parts[-1])
                                pids.add(pid)
                            except ValueError:
                                continue
                
                for pid in pids:
                    self.kill_process(pid)
        except Exception as e:
            print(f"结束端口{port}进程失败: {e}")
    
    def kill_process(self, pid: int):
        try:
            subprocess.run(
                f'taskkill /F /PID {pid}',
                shell=True,
                capture_output=True,
                timeout=5
            )
            self.add_log("backend", f"已结束进程 PID: {pid}")
            self.add_log("frontend", f"已结束进程 PID: {pid}")
            self.refresh_port_status()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"结束进程失败: {e}")
    
    def refresh_port_status(self):
        if self.port_monitor:
            self.status_table.setRowCount(0)
    
    @Slot(str, str)
    def add_log(self, service_type: str, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        if service_type == "后端":
            self.backend_log.append(log_message)
        elif service_type == "前端":
            self.frontend_log.append(log_message)
    
    def clear_logs(self):
        self.backend_log.clear()
        self.frontend_log.clear()
    
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "确认退出",
            "退出程序不会停止已启动的服务，是否继续退出？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.port_monitor:
                self.port_monitor.stop()
                self.port_monitor.wait()
            event.accept()
        else:
            event.ignore()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
