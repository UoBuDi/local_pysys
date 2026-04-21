import sys
import os
import json
import subprocess
import threading
import time
import re
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QProgressBar, QTextEdit, QTabWidget,
    QCheckBox, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, Slot, QMutex, QMutexLocker
from PySide6.QtGui import QColor, QFont

VERSION = "1.1.0"

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "backend": {
        "dir": r"D:\local_pysys\vue-element-plus-admin-master\backend",
        "port": 8000,
        "command": "python main.py",
        "health_check_url": "/api/health"
    },
    "frontend": {
        "dir": r"D:\local_pysys\vue-element-plus-admin-master",
        "port": 4000,
        "command": "pnpm dev",
        "health_check_url": "/"
    },
    "monitor": {
        "interval": 3,
        "health_check_timeout": 5
    },
    "service": {
        "auto_stop_on_exit": False,
        "restart_delay": 2,
        "backend_startup_delay": 3
    }
}


class Config:
    _instance = None
    _mutex = QMutex()
    
    def __new__(cls):
        if cls._instance is None:
            with QMutexLocker(cls._mutex):
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._config = None
        return cls._instance
    
    def load(self) -> Dict[str, Any]:
        if self._config is not None:
            return self._config
        
        config_path = Path(__file__).parent / CONFIG_FILE
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                    self._merge_with_defaults()
            except Exception as e:
                print(f"加载配置文件失败: {e}，使用默认配置")
                self._config = DEFAULT_CONFIG.copy()
        else:
            self._config = DEFAULT_CONFIG.copy()
            self.save()
        
        return self._config
    
    def _merge_with_defaults(self):
        for key, value in DEFAULT_CONFIG.items():
            if key not in self._config:
                self._config[key] = value
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if sub_key not in self._config[key]:
                        self._config[key][sub_key] = sub_value
    
    def save(self):
        config_path = Path(__file__).parent / CONFIG_FILE
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    @property
    def backend_dir(self) -> str:
        return self._config["backend"]["dir"]
    
    @property
    def backend_port(self) -> int:
        return self._config["backend"]["port"]
    
    @property
    def backend_command(self) -> str:
        return self._config["backend"]["command"]
    
    @property
    def backend_health_url(self) -> str:
        return self._config["backend"]["health_check_url"]
    
    @property
    def frontend_dir(self) -> str:
        return self._config["frontend"]["dir"]
    
    @property
    def frontend_port(self) -> int:
        return self._config["frontend"]["port"]
    
    @property
    def frontend_command(self) -> str:
        return self._config["frontend"]["command"]
    
    @property
    def frontend_health_url(self) -> str:
        return self._config["frontend"]["health_check_url"]
    
    @property
    def monitor_interval(self) -> int:
        return self._config["monitor"]["interval"]
    
    @property
    def health_check_timeout(self) -> int:
        return self._config["monitor"]["health_check_timeout"]
    
    @property
    def auto_stop_on_exit(self) -> bool:
        return self._config["service"]["auto_stop_on_exit"]
    
    @auto_stop_on_exit.setter
    def auto_stop_on_exit(self, value: bool):
        self._config["service"]["auto_stop_on_exit"] = value
        self.save()
    
    @property
    def restart_delay(self) -> int:
        return self._config["service"]["restart_delay"]
    
    @property
    def backend_startup_delay(self) -> int:
        return self._config["service"]["backend_startup_delay"]


class ProcessInfo:
    def __init__(self, pid: int, port: int, name: str = "", command: str = ""):
        self.pid = pid
        self.port = port
        self.name = name
        self.command = command


class LogReaderThread(QThread):
    log_signal = Signal(str, str)
    
    def __init__(self, service_type: str, stream):
        super().__init__()
        self.service_type = service_type
        self.stream = stream
        self._is_running = True
    
    def run(self):
        while self._is_running:
            try:
                line = self.stream.readline()
                if line:
                    self.log_signal.emit(self.service_type, line.strip())
                elif self.stream.closed:
                    break
            except Exception:
                break
            time.sleep(0.05)
    
    def stop(self):
        self._is_running = False


class PortMonitorThread(QThread):
    port_status_signal = Signal(int, bool, list)
    health_status_signal = Signal(int, bool)
    
    def __init__(self, config: Config):
        super().__init__()
        self._config = config
        self._is_running = True
    
    def run(self):
        while self._is_running:
            backend_port = self._config.backend_port
            frontend_port = self._config.frontend_port
            
            backend_processes = self.get_port_processes(backend_port)
            frontend_processes = self.get_port_processes(frontend_port)
            
            backend_in_use = len(backend_processes) > 0
            frontend_in_use = len(frontend_processes) > 0
            
            self.port_status_signal.emit(backend_port, backend_in_use, backend_processes)
            self.port_status_signal.emit(frontend_port, frontend_in_use, frontend_processes)
            
            if backend_in_use:
                backend_healthy = self.check_service_health(backend_port, self._config.backend_health_url)
                self.health_status_signal.emit(backend_port, backend_healthy)
            
            if frontend_in_use:
                frontend_healthy = self.check_service_health(frontend_port, self._config.frontend_health_url)
                self.health_status_signal.emit(frontend_port, frontend_healthy)
            
            time.sleep(self._config.monitor_interval)
    
    def get_port_processes(self, port: int) -> List[ProcessInfo]:
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
    
    def check_service_health(self, port: int, health_path: str) -> bool:
        try:
            url = f"http://localhost:{port}{health_path}"
            req = urllib.request.Request(url, method='GET')
            req.add_header('Connection', 'close')
            
            with urllib.request.urlopen(req, timeout=self._config.health_check_timeout) as response:
                return response.status == 200
        except Exception:
            return False
    
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
        self.stdout_reader = None
        self.stderr_reader = None
    
    def run(self):
        self._is_running = True
        try:
            self.log_signal.emit(self.service_type, f"正在启动{self.service_type}服务...")
            self.log_signal.emit(self.service_type, f"工作目录: {self.work_dir}")
            self.log_signal.emit(self.service_type, f"执行命令: {self.command}")
            
            self.process = subprocess.Popen(
                self.command,
                cwd=self.work_dir,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            self.stdout_reader = LogReaderThread(self.service_type, self.process.stdout)
            self.stdout_reader.log_signal.connect(self.log_signal)
            self.stdout_reader.start()
            
            self.stderr_reader = LogReaderThread(self.service_type, self.process.stderr)
            self.stderr_reader.log_signal.connect(self.log_signal)
            self.stderr_reader.start()
            
            self.started_signal.emit(self.service_type)
            self.log_signal.emit(self.service_type, f"{self.service_type}服务已启动 (PID: {self.process.pid})")
            
            while self._is_running and self.process.poll() is None:
                time.sleep(0.5)
            
            if self.process.poll() is not None:
                self.stopped_signal.emit(self.service_type)
                self.log_signal.emit(self.service_type, f"{self.service_type}服务已停止 (退出码: {self.process.poll()})")
        except Exception as e:
            self.error_signal.emit(self.service_type, str(e))
            self.log_signal.emit(self.service_type, f"启动失败: {e}")
    
    def stop(self):
        self._is_running = False
        
        if self.stdout_reader:
            self.stdout_reader.stop()
            self.stdout_reader.wait(1000)
        
        if self.stderr_reader:
            self.stderr_reader.stop()
            self.stderr_reader.wait(1000)
        
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    self.process.kill()
                    self.process.wait(timeout=2)
                except Exception:
                    pass
            except Exception:
                pass
        
        self.wait(3000)
        if self.isRunning():
            self.terminate()


class ExitConfirmDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("确认退出")
        self.setMinimumWidth(350)
        self._auto_stop = False
        
        layout = QVBoxLayout(self)
        
        label = QLabel("确定要退出服务管理工具吗？")
        label.setStyleSheet("font-size: 14px;")
        layout.addWidget(label)
        
        self.checkbox = QCheckBox("退出时停止所有服务")
        self.checkbox.setStyleSheet("font-size: 12px; margin-top: 10px;")
        layout.addWidget(self.checkbox)
        
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_auto_stop(self) -> bool:
        return self.checkbox.isChecked()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._config = Config()
        self._config.load()
        
        self.backend_thread = None
        self.frontend_thread = None
        self.port_monitor = None
        self.backend_running = False
        self.frontend_running = False
        self.backend_healthy = False
        self.frontend_healthy = False
        
        self.init_ui()
        self.start_port_monitor()
    
    def init_ui(self):
        self.setWindowTitle(f"服务管理工具 v{VERSION}")
        self.setMinimumSize(950, 750)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        title_label = QLabel(f"前后端服务管理工具 v{VERSION}")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #409EFF; padding: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        config_group = QGroupBox("配置信息")
        config_layout = QVBoxLayout(config_group)
        
        config_info = QLabel(
            f"后端目录: {self._config.backend_dir}\n"
            f"前端目录: {self._config.frontend_dir}\n"
            f"后端端口: {self._config.backend_port} | 前端端口: {self._config.frontend_port}"
        )
        config_info.setStyleSheet("font-size: 11px; color: #606266;")
        config_layout.addWidget(config_info)
        
        self.auto_stop_checkbox = QCheckBox("退出时自动停止所有服务")
        self.auto_stop_checkbox.setChecked(self._config.auto_stop_on_exit)
        self.auto_stop_checkbox.stateChanged.connect(self._on_auto_stop_changed)
        config_layout.addWidget(self.auto_stop_checkbox)
        
        layout.addWidget(config_group)
        
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
        self.status_table.setColumnCount(6)
        self.status_table.setHorizontalHeaderLabels(["端口", "状态", "健康检查", "进程ID", "进程名称", "操作"])
        self.status_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.status_table.setMinimumHeight(180)
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
    
    def _on_auto_stop_changed(self, state):
        self._config.auto_stop_on_exit = state == Qt.Checked
    
    def start_port_monitor(self):
        self.port_monitor = PortMonitorThread(self._config)
        self.port_monitor.port_status_signal.connect(self.update_port_status)
        self.port_monitor.health_status_signal.connect(self.update_health_status)
        self.port_monitor.start()
    
    @Slot(int, bool)
    def update_health_status(self, port: int, healthy: bool):
        if port == self._config.backend_port:
            self.backend_healthy = healthy
        elif port == self._config.frontend_port:
            self.frontend_healthy = healthy
        
        for row in range(self.status_table.rowCount()):
            port_item = self.status_table.item(row, 0)
            if port_item and int(port_item.text()) == port:
                health_item = self.status_table.item(row, 2)
                if health_item:
                    if healthy:
                        health_item.setText("正常")
                        health_item.setBackground(QColor("#67C23A"))
                        health_item.setForeground(QColor("white"))
                    else:
                        health_item.setText("异常")
                        health_item.setBackground(QColor("#F56C6C"))
                        health_item.setForeground(QColor("white"))
                break
    
    @Slot(int, bool, list)
    def update_port_status(self, port: int, in_use: bool, processes: list):
        all_processes = []
        
        for row in range(self.status_table.rowCount()):
            port_item = self.status_table.item(row, 0)
            if port_item:
                existing_port = int(port_item.text())
                if existing_port != port:
                    pid_item = self.status_table.item(row, 3)
                    health_item = self.status_table.item(row, 2)
                    if pid_item:
                        all_processes.append({
                            'port': existing_port,
                            'pid': int(pid_item.text()) if pid_item.text() != '-' else 0,
                            'name': self.status_table.item(row, 4).text() if self.status_table.item(row, 4) else '',
                            'in_use': self.status_table.item(row, 1).text() == '使用中',
                            'healthy': health_item.text() if health_item else '-'
                        })
        
        for proc in processes:
            healthy = "-"
            if port == self._config.backend_port:
                healthy = "正常" if self.backend_healthy else "异常" if in_use else "-"
            elif port == self._config.frontend_port:
                healthy = "正常" if self.frontend_healthy else "异常" if in_use else "-"
            
            all_processes.append({
                'port': port,
                'pid': proc.pid,
                'name': proc.name,
                'in_use': in_use,
                'healthy': healthy
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
            
            health_item = QTableWidgetItem(str(proc['healthy']))
            health_item.setTextAlignment(Qt.AlignCenter)
            if proc['healthy'] == "正常":
                health_item.setBackground(QColor("#67C23A"))
                health_item.setForeground(QColor("white"))
            elif proc['healthy'] == "异常":
                health_item.setBackground(QColor("#F56C6C"))
                health_item.setForeground(QColor("white"))
            self.status_table.setItem(row, 2, health_item)
            
            pid_item = QTableWidgetItem(str(proc['pid']) if proc['pid'] > 0 else "-")
            pid_item.setTextAlignment(Qt.AlignCenter)
            self.status_table.setItem(row, 3, pid_item)
            
            name_item = QTableWidgetItem(proc['name'] if proc['name'] else "-")
            self.status_table.setItem(row, 4, name_item)
            
            if proc['pid'] > 0:
                kill_btn = QPushButton("结束进程")
                kill_btn.setStyleSheet("background-color: #F56C6C; color: white;")
                kill_btn.clicked.connect(lambda checked, p=proc['pid']: self.kill_process(p))
                self.status_table.setCellWidget(row, 5, kill_btn)
            else:
                self.status_table.setItem(row, 5, QTableWidgetItem("-"))
        
        if port == self._config.backend_port:
            self.backend_running = in_use
            self.update_backend_button()
        elif port == self._config.frontend_port:
            self.frontend_running = in_use
            self.update_frontend_button()
    
    def update_backend_button(self):
        if self.backend_running:
            health_status = " (正常)" if self.backend_healthy else " (异常)"
            self.backend_btn.setText(f"停止后端服务{health_status}")
            self.backend_btn.setStyleSheet("font-size: 14px; font-weight: bold; background-color: #F56C6C;")
        else:
            self.backend_btn.setText("启动后端服务")
            self.backend_btn.setStyleSheet("font-size: 14px; font-weight: bold; background-color: #67C23A;")
    
    def update_frontend_button(self):
        if self.frontend_running:
            health_status = " (正常)" if self.frontend_healthy else " (异常)"
            self.frontend_btn.setText(f"停止前端服务{health_status}")
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
            self.add_log("后端", "后端服务已在运行中")
            return
        
        self.backend_thread = ServiceThread(
            "后端",
            self._config.backend_dir,
            self._config.backend_command
        )
        self.backend_thread.log_signal.connect(self.add_log)
        self.backend_thread.start()
    
    def stop_backend_service(self):
        if self.backend_thread:
            self.backend_thread.stop()
            self.backend_thread = None
        
        self.kill_port_processes(self._config.backend_port)
        self.add_log("后端", "后端服务已停止")
    
    def start_frontend_service(self):
        if self.frontend_thread and self.frontend_thread.isRunning():
            self.add_log("前端", "前端服务已在运行中")
            return
        
        self.frontend_thread = ServiceThread(
            "前端",
            self._config.frontend_dir,
            self._config.frontend_command
        )
        self.frontend_thread.log_signal.connect(self.add_log)
        self.frontend_thread.start()
    
    def stop_frontend_service(self):
        if self.frontend_thread:
            self.frontend_thread.stop()
            self.frontend_thread = None
        
        self.kill_port_processes(self._config.frontend_port)
        self.add_log("前端", "前端服务已停止")
    
    def restart_all_services(self):
        self.stop_all_services()
        time.sleep(self._config.restart_delay)
        self.start_backend_service()
        time.sleep(self._config.backend_startup_delay)
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
            self.add_log("后端", f"已结束进程 PID: {pid}")
            self.add_log("前端", f"已结束进程 PID: {pid}")
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
        dialog = ExitConfirmDialog(self)
        dialog.checkbox.setChecked(self._config.auto_stop_on_exit)
        
        result = dialog.exec()
        
        if result == QDialog.Accepted:
            auto_stop = dialog.get_auto_stop()
            self._config.auto_stop_on_exit = auto_stop
            
            if auto_stop:
                self.add_log("后端", "正在停止所有服务...")
                self.add_log("前端", "正在停止所有服务...")
                self.stop_all_services()
                time.sleep(1)
            
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
