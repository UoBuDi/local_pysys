import sys
import os
import socket
import time
import threading
import logging
import requests
import json
import uuid
import asyncio
import websockets
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox, QCheckBox, QGroupBox,
    QFormLayout, QMessageBox, QSystemTrayIcon, QMenu, QTextEdit,
    QTabWidget, QDialog, QDialogButtonBox, QComboBox
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, Slot
from PySide6.QtGui import QIcon, QAction
from werkzeug.serving import run_simple, make_server
from api_server import app
from config import config, DEFAULT_CONFIG, get_base_path
from network_utils import get_local_ips, check_network_connectivity

def get_log_file_path():
    log_dir = get_base_path()
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, 'service.log')

def setup_logging():
    log_file = get_log_file_path()
    
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.LOG_LEVEL, logging.INFO))
    
    formatter = logging.Formatter(
        '%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='a')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    if logger.handlers:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    return logger

logger = setup_logging()

logger.info("="*80)
logger.info("CloudPortalService 启动")
logger.info(f"版本: {config.VERSION}")
logger.info(f"运行目录: {get_base_path()}")
logger.info(f"日志文件: {get_log_file_path()}")
logger.info(f"GUI服务地址: {config.GUI_HOST}:{config.GUI_PORT}")
logger.info(f"后端WebSocket地址: {config.BACKEND_URL}")
logger.info(f"云门户地址: {config.PORTAL_BASE_URL}")
logger.info(f"源IP配置: ethernet_ip={config.ETHERNET_IP}, ethernet2_ip={config.ETHERNET2_IP}")
logger.info("="*80)

class FlaskThread(QThread):
    started_signal = Signal()
    stopped_signal = Signal()
    error_signal = Signal(str)
    
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self._is_running = False
        self.server = None
    
    def run(self):
        self._is_running = True
        try:
            logger.info(f"Flask服务启动: {self.host}:{self.port}")
            
            self.server = make_server(self.host, self.port, app, threaded=True)
            self.server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.started_signal.emit()
            
            logger.info(f"Flask服务成功监听: {self.host}:{self.port}")
            self.server.serve_forever()
            
        except OSError as e:
            error_msg = str(e)
            logger.error(f"Flask服务绑定失败: {error_msg}")
            
            if "10049" in error_msg or "requested address" in error_msg.lower():
                user_msg = (
                    f"无法绑定到IP地址 {self.host}\n\n"
                    f"可能原因:\n"
                    f"1. 该IP地址不存在于本机\n"
                    f"2. 网卡未启用或IP已变更\n\n"
                    f"建议操作:\n"
                    f"- 检查'服务配置'中的'服务地址'是否正确\n"
                    f"- 或改为 '0.0.0.0' 监听所有接口"
                )
            elif "10048" in error_msg or "already in use" in error_msg.lower():
                user_msg = f"端口 {self.port} 已被其他程序占用"
            else:
                user_msg = f"服务启动失败: {error_msg}"
                
            self.error_signal.emit(user_msg)
            
        except Exception as e:
            logger.error(f"Flask服务未知错误: {e}")
            self.error_signal.emit(f"服务异常: {str(e)}")
            
        finally:
            self._is_running = False
            self.stopped_signal.emit()
    
    def stop(self):
        self._is_running = False
        if self.server:
            self.server.shutdown()
            self.server = None
        self.wait(3000)
        if self.isRunning():
            self.terminate()
        time.sleep(0.5)

class WebSocketClientThread(QThread):
    connected_signal = Signal()
    disconnected_signal = Signal()
    message_received = Signal(dict)
    error_signal = Signal(str)
    status_updated = Signal(dict)
    
    def __init__(self, backend_url: str, client_id: str = None):
        super().__init__()
        self.backend_url = backend_url
        self.client_id = client_id or f"gui_{uuid.uuid4().hex[:8]}"
        self._is_running = False
        self._websocket = None
        self._loop = None
        self._last_status = None
    
    def run(self):
        self._is_running = True
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            self._loop.run_until_complete(self._connect_and_listen())
        except Exception as e:
            logger.error(f"WebSocket客户端错误: {e}")
            self.error_signal.emit(str(e))
        finally:
            self._loop.close()
    
    async def _connect_and_listen(self):
        ws_url = f"{self.backend_url}/ws/status/gui/{self.client_id}"
        
        while self._is_running:
            try:
                logger.info(f"WebSocket连接: {ws_url}")
                async with websockets.connect(ws_url) as websocket:
                    self._websocket = websocket
                    self.connected_signal.emit()
                    logger.info("WebSocket已连接")
                    
                    heartbeat_task = asyncio.create_task(self._send_heartbeat())
                    
                    try:
                        async for message in websocket:
                            if not self._is_running:
                                break
                            try:
                                data = json.loads(message)
                                self.message_received.emit(data)
                                
                                if data.get("type") == "status_update":
                                    self._last_status = data.get("data", {})
                                    self.status_updated.emit(self._last_status)
                            except json.JSONDecodeError:
                                logger.warning(f"无效的JSON消息: {message}")
                    finally:
                        heartbeat_task.cancel()
                        self._websocket = None
                        
            except Exception as e:
                logger.warning(f"WebSocket连接断开: {e}")
                self.disconnected_signal.emit()
                
                if self._is_running:
                    await asyncio.sleep(5)
    
    async def _send_heartbeat(self):
        while self._is_running and self._websocket:
            try:
                await self._websocket.send(json.dumps({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                }))
                await asyncio.sleep(30)
            except Exception as e:
                logger.warning(f"心跳发送失败: {e}")
                break
    
    def stop(self):
        self._is_running = False
        if self._websocket:
            asyncio.run_coroutine_threadsafe(
                self._websocket.close(),
                self._loop
            )
        self.wait(3000)
        if self.isRunning():
            self.terminate()
    
    def get_last_status(self):
        return self._last_status

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("服务配置")
        self.setMinimumWidth(500)
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        tab_widget = QTabWidget()
        
        network_tab = QWidget()
        network_layout = QVBoxLayout(network_tab)
        
        gui_group = QGroupBox("GUI服务配置")
        gui_layout = QFormLayout(gui_group)
        
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("绑定到以太网网卡IP")
        gui_layout.addRow("服务地址:", self.host_input)
        
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(9000)
        gui_layout.addRow("服务端口:", self.port_input)
        
        network_layout.addWidget(gui_group)
        
        backend_group = QGroupBox("后端服务配置")
        backend_layout = QFormLayout(backend_group)
        
        self.backend_host_input = QLineEdit()
        self.backend_host_input.setPlaceholderText("0.0.0.0 (监听所有接口) 或指定IP")
        backend_layout.addRow("绑定地址:", self.backend_host_input)
        
        self.backend_port_input = QSpinBox()
        self.backend_port_input.setRange(1, 65535)
        self.backend_port_input.setValue(8000)
        backend_layout.addRow("监听端口:", self.backend_port_input)
        
        self.auto_generate_url_checkbox = QCheckBox("自动生成访问URL")
        self.auto_generate_url_checkbox.setChecked(True)
        self.auto_generate_url_checkbox.stateChanged.connect(self._on_auto_generate_url_changed)
        backend_layout.addRow("", self.auto_generate_url_checkbox)
        
        self.backend_url_input = QLineEdit()
        self.backend_url_input.setPlaceholderText("http://172.32.48.239:8000 或自定义URL")
        backend_layout.addRow("访问URL:", self.backend_url_input)
        
        test_connection_layout = QHBoxLayout()
        self.test_connection_btn = QPushButton("测试连接")
        self.test_connection_btn.clicked.connect(self._test_backend_connection)
        self.test_connection_result_label = QLabel()
        self.test_connection_result_label.setStyleSheet("color: gray;")
        test_connection_layout.addWidget(self.test_connection_btn)
        test_connection_layout.addWidget(self.test_connection_result_label)
        test_connection_layout.addStretch()
        backend_layout.addRow("", test_connection_layout)
        
        network_layout.addWidget(backend_group)
        
        network_group = QGroupBox("网络接口")
        network_interface_layout = QFormLayout(network_group)
        
        local_ips = get_local_ips()
        ip_label = QLabel(f"本机IP: {', '.join(local_ips) if local_ips else '未检测到'}")
        ip_label.setWordWrap(True)
        network_interface_layout.addRow("", ip_label)
        
        self.ethernet_ip_input = QLineEdit()
        self.ethernet_ip_input.setPlaceholderText("以太网IP (业务网络)")
        network_interface_layout.addRow("以太网IP:", self.ethernet_ip_input)
        
        self.ethernet2_ip_input = QLineEdit()
        self.ethernet2_ip_input.setPlaceholderText("以太网2IP (云门户网络)")
        network_interface_layout.addRow("以太网2IP:", self.ethernet2_ip_input)
        
        network_layout.addWidget(network_group)
        
        tab_widget.addTab(network_tab, "网络配置")
        
        portal_tab = QWidget()
        portal_layout = QFormLayout(portal_tab)
        
        self.portal_base_url_input = QLineEdit()
        self.portal_base_url_input.setPlaceholderText("http://api.hngsetc.com")
        portal_layout.addRow("门户基础URL:", self.portal_base_url_input)
        
        self.portal_sso_url_input = QLineEdit()
        self.portal_sso_url_input.setPlaceholderText("http://sso.hngsetc.com")
        portal_layout.addRow("SSO URL:", self.portal_sso_url_input)
        
        self.portal_home_url_input = QLineEdit()
        self.portal_home_url_input.setPlaceholderText("http://home.hngsetc.com")
        portal_layout.addRow("门户主页URL:", self.portal_home_url_input)
        
        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("客户端ID")
        portal_layout.addRow("客户端ID:", self.client_id_input)
        
        self.session_timeout_input = QSpinBox()
        self.session_timeout_input.setRange(300, 86400)
        self.session_timeout_input.setValue(3600)
        self.session_timeout_input.setSuffix(" 秒")
        portal_layout.addRow("会话超时:", self.session_timeout_input)
        
        tab_widget.addTab(portal_tab, "门户配置")
        
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)
        
        self.auto_start_checkbox = QCheckBox("启动时自动开始服务")
        general_layout.addRow("", self.auto_start_checkbox)
        
        self.minimize_checkbox = QCheckBox("启动时最小化到系统托盘")
        general_layout.addRow("", self.minimize_checkbox)
        
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(log_levels)
        general_layout.addRow("日志级别:", self.log_level_combo)
        
        tab_widget.addTab(general_tab, "常规配置")
        
        layout.addWidget(tab_widget)
        
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.save_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_config(self):
        self.host_input.setText(config.GUI_HOST)
        self.port_input.setValue(config.GUI_PORT)
        self.backend_host_input.setText(config.BACKEND_HOST)
        self.backend_port_input.setValue(config.BACKEND_PORT)
        self.auto_generate_url_checkbox.setChecked(config.BACKEND_AUTO_GENERATE_URL)
        self.backend_url_input.setText(config.BACKEND_URL if not config.BACKEND_AUTO_GENERATE_URL else "")
        self._on_auto_generate_url_changed(self.auto_generate_url_checkbox.checkState())
        self.ethernet_ip_input.setText(config.ETHERNET_IP)
        self.ethernet2_ip_input.setText(config.ETHERNET2_IP)
        self.portal_base_url_input.setText(config.PORTAL_BASE_URL)
        self.portal_sso_url_input.setText(config.PORTAL_SSO_URL)
        self.portal_home_url_input.setText(config.PORTAL_HOME_URL)
        self.client_id_input.setText(config.CLIENT_ID)
        self.session_timeout_input.setValue(config.SESSION_TIMEOUT)
        self.auto_start_checkbox.setChecked(config.AUTO_START)
        self.minimize_checkbox.setChecked(config.MINIMIZE_TO_TRAY)
        
        log_level = config.LOG_LEVEL
        index = self.log_level_combo.findText(log_level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)
    
    @Slot(int)
    def _on_auto_generate_url_changed(self, state):
        is_checked = state == Qt.CheckState.Checked.value
        self.backend_url_input.setEnabled(not is_checked)
        if is_checked:
            self.backend_url_input.setPlaceholderText("自动生成 (基于绑定地址和端口)")
            host = self.backend_host_input.text() or "0.0.0.0"
            port = self.backend_port_input.value()
            if host == "0.0.0.0" or host == "127.0.0.1":
                local_ips = get_local_ips()
                if local_ips:
                    host = local_ips[0]
                else:
                    host = "127.0.0.1"
            preview_url = f"http://{host}:{port}"
            self.backend_url_input.setToolTip(f"预览: {preview_url}")
        else:
            self.backend_url_input.setPlaceholderText("http://172.32.48.239:8000 或自定义URL")
            self.backend_url_input.setToolTip("")
    
    @Slot()
    def save_and_accept(self):
        if not self._validate_config():
            return
        
        if not self._check_port_available():
            return
        
        old_backend_host = config.BACKEND_HOST
        old_backend_port = config.BACKEND_PORT
        old_gui_host = config.GUI_HOST
        old_gui_port = config.GUI_PORT
        
        config.set('gui_host', self.host_input.text())
        config.set('gui_port', self.port_input.value())
        
        backend_config = {
            'host': self.backend_host_input.text(),
            'port': self.backend_port_input.value(),
            'auto_generate_url': self.auto_generate_url_checkbox.isChecked(),
            'url': self.backend_url_input.text() if not self.auto_generate_url_checkbox.isChecked() else ""
        }
        config.set('backend', backend_config)
        
        config.set('auto_start', self.auto_start_checkbox.isChecked())
        config.set('minimize_to_tray', self.minimize_checkbox.isChecked())
        config.set('portal_base_url', self.portal_base_url_input.text())
        config.set('portal_sso_url', self.portal_sso_url_input.text())
        config.set('portal_home_url', self.portal_home_url_input.text())
        config.set('client_id', self.client_id_input.text())
        config.set('session_timeout', self.session_timeout_input.value())
        config.set('log_level', self.log_level_combo.currentText())
        
        network_config = {
            'ethernet_ip': self.ethernet_ip_input.text(),
            'ethernet2_ip': self.ethernet2_ip_input.text(),
            'use_ethernet2_for_portal': True
        }
        config.set('network', network_config)
        
        requires_restart = (
            old_backend_host != config.BACKEND_HOST or
            old_backend_port != config.BACKEND_PORT or
            old_gui_host != config.GUI_HOST or
            old_gui_port != config.GUI_PORT
        )
        
        if requires_restart:
            reply = QMessageBox.question(
                self, "配置已保存",
                "配置已成功保存！\n\n"
                "检测到网络配置已更改，需要重启服务才能生效。\n\n"
                "是否现在重启服务？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                QMessageBox.information(self, "提示", "请手动重启服务以应用新配置")
            else:
                QMessageBox.information(self, "提示", "配置已保存，将在下次启动时生效")
        else:
            QMessageBox.information(self, "成功", "配置已保存")
        
        self.accept()
    
    def _validate_config(self):
        """验证配置有效性"""
        host = self.backend_host_input.text().strip()
        port = self.backend_port_input.value()
        
        if not host:
            QMessageBox.warning(self, "验证失败", "后端绑定地址不能为空")
            return False
        
        if host != "0.0.0.0" and host != "127.0.0.1":
            import socket
            try:
                socket.inet_aton(host)
            except socket.error:
                QMessageBox.warning(self, "验证失败", f"无效的IP地址格式: {host}")
                return False
        
        if not self.auto_generate_url_checkbox.isChecked():
            url = self.backend_url_input.text().strip()
            if url:
                if not (url.startswith("http://") or url.startswith("https://")):
                    QMessageBox.warning(self, "验证失败", "访问URL必须以 http:// 或 https:// 开头")
                    return False
        
        return True
    
    @Slot()
    def _test_backend_connection(self):
        """测试后端连接"""
        self.test_connection_btn.setEnabled(False)
        self.test_connection_result_label.setText("正在测试连接...")
        self.test_connection_result_label.setStyleSheet("color: blue;")
        
        host = self.backend_host_input.text().strip() or "0.0.0.0"
        port = self.backend_port_input.value()
        
        if self.auto_generate_url_checkbox.isChecked():
            if host == "0.0.0.0" or host == "127.0.0.1":
                local_ips = get_local_ips()
                test_host = local_ips[0] if local_ips else "127.0.0.1"
            else:
                test_host = host
            test_url = f"http://{test_host}:{port}"
        else:
            test_url = self.backend_url_input.text().strip()
            if not test_url:
                self._show_connection_result(False, "请输入访问URL")
                return
        
        import threading
        def do_test():
            import requests
            try:
                response = requests.get(f"{test_url}/api/portal/health", timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    if status == 'ok':
                        self._show_connection_result(True, f"✓ 连接成功 - 服务运行正常 (响应时间: {response.elapsed.total_seconds()*1000:.0f}ms)")
                    else:
                        self._show_connection_result(False, f"✗ 服务异常 - 状态: {status}")
                else:
                    self._show_connection_result(False, f"✗ HTTP错误 - 状态码: {response.status_code}")
            except requests.exceptions.ConnectionError:
                self._show_connection_result(False, "✗ 无法连接 - 请检查地址和端口是否正确，或服务是否已启动")
            except requests.exceptions.Timeout:
                self._show_connection_result(False, "✗ 连接超时 - 响应时间超过3秒")
            except Exception as e:
                self._show_connection_result(False, f"✗ 测试失败 - {str(e)}")
        
        thread = threading.Thread(target=do_test, daemon=True)
        thread.start()
    
    def _show_connection_result(self, success: bool, message: str):
        """显示连接测试结果"""
        self.test_connection_btn.setEnabled(True)
        self.test_connection_result_label.setText(message)
        if success:
            self.test_connection_result_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.test_connection_result_label.setStyleSheet("color: red; font-weight: bold;")
    
    def _check_port_available(self):
        """检查端口是否可用"""
        import socket
        
        backend_port = self.backend_port_input.value()
        gui_port = self.port_input.value()
        
        ports_to_check = []
        if backend_port == gui_port:
            ports_to_check.append(("后端/GUI服务", backend_port))
        else:
            ports_to_check.append(("后端服务", backend_port))
            ports_to_check.append(("GUI服务", gui_port))
        
        for service_name, port in ports_to_check:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('0.0.0.0', port))
                except OSError:
                    reply = QMessageBox.critical(
                        self, "端口占用",
                        f"端口 {port} 已被占用（{service_name}）。\n\n"
                        "请选择其他端口或关闭占用该端口的程序。",
                        QMessageBox.StandardButton.Abort | QMessageBox.StandardButton.Ignore,
                        QMessageBox.StandardButton.Abort
                    )
                    return reply == QMessageBox.StandardButton.Ignore
        
        return True

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.flask_thread = None
        self.websocket_thread = None
        self.is_service_running = False
        self.request_log_timer = None
        self.init_ui()
        self.setup_tray()
        
        if config.AUTO_START:
            QTimer.singleShot(500, self.start_service)
    
    def init_ui(self):
        self.setWindowTitle(f"云门户查询服务 v{config.VERSION}")
        self.setMinimumSize(800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        status_group = QGroupBox("服务状态")
        status_layout = QVBoxLayout(status_group)
        
        status_row = QHBoxLayout()
        self.status_label = QLabel("服务状态: 未启动")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        
        self.ws_status_label = QLabel("WebSocket: 未连接")
        self.ws_status_label.setStyleSheet("font-weight: bold; font-size: 12px; color: gray;")
        status_row.addWidget(self.ws_status_label)
        status_row.addStretch()
        
        version_label = QLabel(f"v{config.VERSION}")
        version_label.setStyleSheet("color: #409EFF; font-weight: bold;")
        status_row.addWidget(version_label)
        status_row.addStretch()
        
        self.start_btn = QPushButton("启动服务")
        self.start_btn.clicked.connect(self.toggle_service)
        self.start_btn.setMinimumWidth(120)
        status_row.addWidget(self.start_btn)
        
        status_layout.addLayout(status_row)
        
        self.url_label = QLabel()
        self.url_label.setStyleSheet("color: gray;")
        status_layout.addWidget(self.url_label)
        
        layout.addWidget(status_group)
        
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        clear_log_btn = QPushButton("清空日志")
        clear_log_btn.clicked.connect(self.log_text.clear)
        log_layout.addWidget(clear_log_btn)
        
        layout.addWidget(log_group)
        
        info_group = QGroupBox("网络信息")
        info_layout = QFormLayout(info_group)
        
        local_ips = get_local_ips()
        ip_text = ', '.join(local_ips) if local_ips else '未检测到'
        info_layout.addRow("本机IP:", QLabel(ip_text))
        
        info_layout.addRow("以太网IP:", QLabel(config.ETHERNET_IP))
        info_layout.addRow("以太网2IP:", QLabel(config.ETHERNET2_IP))
        
        layout.addWidget(info_group)
        
        btn_layout = QHBoxLayout()
        
        config_btn = QPushButton("配置")
        config_btn.clicked.connect(self.show_config)
        btn_layout.addWidget(config_btn)
        
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
    
    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        icon_path = os.path.join(get_base_path(), 'icon.png')
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(
                self.style().StandardPixmap.SP_ComputerIcon
            ))
        
        self.tray_icon.setToolTip("云门户查询服务")
        
        tray_menu = QMenu()
        
        self.tray_start_action = QAction("启动服务", self)
        self.tray_start_action.triggered.connect(self.toggle_service)
        tray_menu.addAction(self.tray_start_action)
        
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show_and_activate)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()
    
    @Slot(QSystemTrayIcon.ActivationReason)
    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_and_activate()
    
    def show_and_activate(self):
        self.show()
        self.activateWindow()
        self.raise_()
    
    @Slot()
    def toggle_service(self):
        if self.is_service_running:
            self.stop_service()
        else:
            self.start_service()
    
    def start_service(self):
        if self.is_service_running:
            return
        
        try:
            gui_host = config.GUI_HOST
            gui_port = config.GUI_PORT
            
            self.flask_thread = FlaskThread(gui_host, gui_port)
            self.flask_thread.started_signal.connect(self.on_service_started)
            self.flask_thread.stopped_signal.connect(self.on_service_stopped)
            self.flask_thread.error_signal.connect(self.on_service_error)
            self.flask_thread.start()
            
            self.log_message(f"正在启动GUI服务 {gui_host}:{gui_port}...")
        except Exception as e:
            self.log_message(f"启动服务失败: {e}")
            QMessageBox.critical(self, "错误", f"启动服务失败: {e}")
    
    def stop_service(self):
        if self.flask_thread and self.is_service_running:
            self.log_message("正在停止服务...")
            self.flask_thread.stop()
            self.flask_thread = None
    
    @Slot()
    def on_service_started(self):
        self.is_service_running = True
        self.status_label.setText("服务状态: 运行中")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: green;")
        self.start_btn.setText("停止服务")
        self.tray_start_action.setText("停止服务")
        
        gui_url = f"http://{config.GUI_HOST}:{config.GUI_PORT}"
        self.url_label.setText(f"GUI服务地址: {gui_url}")
        self.log_message(f"GUI服务启动成功 - {gui_url}")
        
        self.request_log_timer = QTimer(self)
        self.request_log_timer.timeout.connect(self.fetch_request_logs)
        self.request_log_timer.start(2000)
        
        self.start_websocket_client()
    
    def start_websocket_client(self):
        if self.websocket_thread is None or not self.websocket_thread.isRunning():
            backend_url = config.BACKEND_URL.replace("http://", "ws://").replace("https://", "wss://")
            self.websocket_thread = WebSocketClientThread(backend_url)
            self.websocket_thread.connected_signal.connect(self.on_ws_connected)
            self.websocket_thread.disconnected_signal.connect(self.on_ws_disconnected)
            self.websocket_thread.status_updated.connect(self.on_ws_status_updated)
            self.websocket_thread.error_signal.connect(self.on_ws_error)
            self.websocket_thread.start()
            self.log_message(f"WebSocket客户端启动中... (连接到 {backend_url})")
    
    def stop_websocket_client(self):
        if self.websocket_thread and self.websocket_thread.isRunning():
            self.websocket_thread.stop()
            self.websocket_thread = None
            self.log_message("WebSocket客户端已停止")
    
    @Slot()
    def on_ws_connected(self):
        self.log_message("WebSocket已连接到后端")
        self.update_ws_status_display(connected=True)
    
    @Slot()
    def on_ws_disconnected(self):
        self.log_message("WebSocket与后端断开")
        self.update_ws_status_display(connected=False)
    
    @Slot(dict)
    def on_ws_status_updated(self, status):
        frontend_count = status.get("frontend_count", 0)
        gui_count = status.get("gui_count", 0)
        self.log_message(f"状态更新: 前端在线 {frontend_count}, GUI在线 {gui_count}")
    
    @Slot(str)
    def on_ws_error(self, error):
        self.log_message(f"WebSocket错误: {error}")
    
    def update_ws_status_display(self, connected: bool):
        if connected:
            self.ws_status_label.setText("WebSocket: 已连接")
            self.ws_status_label.setStyleSheet("font-weight: bold; font-size: 12px; color: green;")
        else:
            self.ws_status_label.setText("WebSocket: 未连接")
            self.ws_status_label.setStyleSheet("font-weight: bold; font-size: 12px; color: red;")
    
    @Slot()
    def on_service_stopped(self):
        self.is_service_running = False
        self.status_label.setText("服务状态: 已停止")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: red;")
        self.start_btn.setText("启动服务")
        self.tray_start_action.setText("启动服务")
        self.url_label.setText("")
        self.log_message("服务已停止")
        
        if self.request_log_timer:
            self.request_log_timer.stop()
            self.request_log_timer = None
        
        self.stop_websocket_client()
    
    def fetch_request_logs(self):
        pass
    
    @Slot(str)
    def on_service_error(self, error):
        self.log_message(f"服务错误: {error}")
        QMessageBox.critical(self, "错误", f"服务错误: {error}")
    
    @Slot()
    def show_config(self):
        dialog = ConfigDialog(self)
        dialog.exec()
    
    def log_message(self, message):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def closeEvent(self, event):
        if config.MINIMIZE_TO_TRAY:
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "云门户查询服务",
                "程序已最小化到系统托盘",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
        else:
            self.quit_app()
    
    @Slot()
    def quit_app(self):
        self.stop_websocket_client()
        
        if hasattr(self, 'request_log_timer') and self.request_log_timer:
            self.request_log_timer.stop()
            self.request_log_timer = None
        
        if self.is_service_running:
            reply = QMessageBox.question(
                self,
                "确认退出",
                "服务正在运行，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
            
            self.stop_service()
        
        self.tray_icon.hide()
        
        QApplication.processEvents()
        time.sleep(0.3)
        
        QApplication.quit()

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    window = MainWindow()
    
    if not config.MINIMIZE_TO_TRAY:
        window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
