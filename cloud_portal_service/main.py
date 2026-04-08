import sys
import os
import socket
import time
import threading
import logging
import json
import uuid
import websocket
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox, QCheckBox, QGroupBox,
    QFormLayout, QMessageBox, QSystemTrayIcon, QMenu,
    QTabWidget, QDialog, QDialogButtonBox, QComboBox, QGridLayout
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, Slot
from PySide6.QtGui import QIcon, QAction
from werkzeug.serving import run_simple, make_server
from config import config, DEFAULT_CONFIG, get_base_path
from network_utils import get_local_ips, check_network_connectivity

def get_log_file_path():
    log_dir = get_base_path()
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, 'service.log')

def setup_logging():
    log_file = get_log_file_path()
    
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception as e:
            print(f"无法创建日志目录 {log_dir}: {e}")
    
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            pass
    except Exception as e:
        print(f"无法写入日志文件 {log_file}: {e}")
        log_file = os.path.join(os.getcwd(), 'service.log')
        print(f"回退到当前工作目录: {log_file}")
    
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
    
    return logger, file_handler

logger, log_file_handler = setup_logging()

from api_server import app

logger.info("="*80)
logger.info("CloudPortalService 启动")
logger.info(f"版本: {config.VERSION}")
logger.info(f"sys.frozen: {getattr(sys, 'frozen', 'Not set')}")
logger.info(f"__compiled__: {'__compiled__' in globals()}")
logger.info(f"sys.executable: {sys.executable}")
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
            try:
                self.server.shutdown()
            except Exception:
                pass
            self.server = None

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
        self._ws = None
        self._last_status = None
        self._heartbeat_thread = None
        self._reconnect_delay = 5
        self._max_reconnect_delay = 30
    
    def run(self):
        self._is_running = True
        ws_url = f"{self.backend_url}/ws/status/gui/{self.client_id}"
        
        while self._is_running:
            try:
                logger.info(f"WebSocket连接: {ws_url}")
                log_file_handler.flush()
                
                self._ws = websocket.WebSocketApp(
                    ws_url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close
                )
                
                self._ws.run_forever()
                
                if self._is_running:
                    logger.info(f"WebSocket断开，{self._reconnect_delay}秒后重连...")
                    time.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
                    
            except Exception as e:
                error_msg = f"WebSocket客户端错误: {e}"
                logger.error(error_msg)
                log_file_handler.flush()
                self.error_signal.emit(str(e))
                self.disconnected_signal.emit()
                
                if self._is_running:
                    time.sleep(self._reconnect_delay)
    
    def _on_open(self, ws):
        logger.info("WebSocket已连接")
        self.connected_signal.emit()
        self._reconnect_delay = 5
        
        self._heartbeat_thread = threading.Thread(target=self._send_heartbeat, daemon=True)
        self._heartbeat_thread.start()
    
    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
            self.message_received.emit(data)
            
            if data.get("type") == "status_update":
                self._last_status = data.get("data", {})
                self.status_updated.emit(self._last_status)
            elif data.get("type") == "heartbeat_ack":
                logger.debug(f"收到心跳响应: {data.get('timestamp')}")
        except json.JSONDecodeError:
            logger.warning(f"无效的JSON消息: {message}")
    
    def _on_error(self, ws, error):
        if isinstance(error, Exception):
            error_msg = f"WebSocket错误: {type(error).__name__}: {error}"
        else:
            error_msg = f"WebSocket错误: {error}"
        logger.error(error_msg)
        self.error_signal.emit(error_msg)
    
    def _on_close(self, ws, close_status_code, close_msg):
        logger.info(f"WebSocket关闭: {close_status_code} - {close_msg}")
        self.disconnected_signal.emit()
    
    def _send_heartbeat(self):
        time.sleep(2)
        while self._is_running:
            try:
                if self._ws and self._ws.sock:
                    self._ws.send(json.dumps({
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat()
                    }))
                time.sleep(30)
            except Exception as e:
                logger.warning(f"心跳发送失败: {e}")
                break
    
    def stop(self):
        self._is_running = False
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
            self._ws = None
    
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
        
        gui_group = QGroupBox("GUI监听配置")
        gui_layout = QFormLayout(gui_group)
        
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("绑定到以太网网卡IP")
        gui_layout.addRow("服务地址:", self.host_input)
        
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(9000)
        gui_layout.addRow("服务端口:", self.port_input)
        
        network_layout.addWidget(gui_group)
        
        backend_group = QGroupBox("WebSocket配置")
        backend_layout = QFormLayout(backend_group)
        
        self.backend_host_input = QLineEdit()
        self.backend_host_input.setPlaceholderText("0.0.0.0 (监听所有接口) 或指定IP")
        backend_layout.addRow("绑定地址:", self.backend_host_input)
        
        self.backend_port_input = QSpinBox()
        self.backend_port_input.setRange(1, 65535)
        self.backend_port_input.setValue(8000)
        backend_layout.addRow("监听端口:", self.backend_port_input)
        
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
        self.ethernet_ip_input.setText(config.ETHERNET_IP)
        self.ethernet2_ip_input.setText(config.ETHERNET2_IP)
        self.portal_base_url_input.setText(config.PORTAL_BASE_URL)
        self.portal_sso_url_input.setText(config.PORTAL_SSO_URL)
        self.portal_home_url_input.setText(config.PORTAL_HOME_URL)
        self.client_id_input.setText(config.CLIENT_ID)
        self.session_timeout_input.setValue(config.SESSION_TIMEOUT)
        self.auto_start_checkbox.setChecked(config.AUTO_START)
        
        log_level = config.LOG_LEVEL
        index = self.log_level_combo.findText(log_level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)
    
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
            'port': self.backend_port_input.value()
        }
        config.set('backend', backend_config)
        
        config.set('auto_start', self.auto_start_checkbox.isChecked())
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
        
        if self.parent():
            self.parent().update_connection_info()
            
            backend_changed = (old_backend_host != config.BACKEND_HOST or 
                              old_backend_port != config.BACKEND_PORT)
            if backend_changed and self.parent().is_service_running:
                self.parent().restart_websocket_client()
        
        QMessageBox.information(self, "成功", "配置已保存并立即生效")
        self.accept()
    
    def _validate_config(self):
        """验证配置有效性"""
        host = self.backend_host_input.text().strip()
        
        if not host:
            QMessageBox.warning(self, "验证失败", "后端绑定地址不能为空")
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
        
        if host == "0.0.0.0" or host == "127.0.0.1":
            local_ips = get_local_ips()
            test_host = local_ips[0] if local_ips else "127.0.0.1"
        else:
            test_host = host
        test_url = f"http://{test_host}:{port}"
        
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
        self.setMinimumSize(900, 650)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f7fa;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #dcdfe6;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #303133;
            }
            QPushButton {
                background-color: #409EFF;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
            QPushButton:pressed {
                background-color: #3a8ee6;
            }
            QPushButton:disabled {
                background-color: #a0cfff;
            }
            QLabel {
                color: #606266;
                font-size: 13px;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        status_group = QGroupBox("服务状态")
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(12)
        
        status_row = QHBoxLayout()
        status_row.setSpacing(20)
        
        status_info_layout = QVBoxLayout()
        status_info_layout.setSpacing(8)
        
        self.status_label = QLabel("● 服务状态: 未启动")
        self.status_label.setStyleSheet("""
            font-weight: bold; 
            font-size: 15px; 
            color: #909399;
            background-color: #f4f4f5;
            padding: 4px 8px;
            border-radius: 4px;
        """)
        status_info_layout.addWidget(self.status_label)
        
        self.ws_status_label = QLabel("● WebSocket: 未连接")
        self.ws_status_label.setStyleSheet("""
            font-weight: bold; 
            font-size: 13px; 
            color: #909399;
            background-color: #f4f4f5;
            padding: 4px 8px;
            border-radius: 4px;
        """)
        status_info_layout.addWidget(self.ws_status_label)
        
        self.url_label = QLabel()
        self.url_label.setStyleSheet("color: #909399; font-size: 12px;")
        status_info_layout.addWidget(self.url_label)
        
        status_row.addLayout(status_info_layout)
        status_row.addStretch()
        
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)
        
        self.start_btn = QPushButton("启动服务")
        self.start_btn.clicked.connect(self.toggle_service)
        self.start_btn.setMinimumWidth(140)
        self.start_btn.setMinimumHeight(40)
        btn_layout.addWidget(self.start_btn)
        
        config_btn = QPushButton("服务配置")
        config_btn.clicked.connect(self.show_config)
        config_btn.setStyleSheet("""
            QPushButton {
                background-color: #67C23A;
            }
            QPushButton:hover {
                background-color: #85ce61;
            }
            QPushButton:pressed {
                background-color: #5daf34;
            }
        """)
        config_btn.setMinimumWidth(140)
        config_btn.setMinimumHeight(40)
        btn_layout.addWidget(config_btn)
        
        status_row.addLayout(btn_layout)
        status_layout.addLayout(status_row)
        
        layout.addWidget(status_group)
        
        info_group = QGroupBox("连接信息")
        info_layout = QGridLayout(info_group)
        info_layout.setSpacing(12)
        
        info_layout.addWidget(QLabel("GUI监听地址:"), 0, 0)
        self.gui_addr_label = QLabel(f"{config.GUI_HOST}:{config.GUI_PORT}")
        self.gui_addr_label.setStyleSheet("color: #409EFF; font-weight: bold;")
        info_layout.addWidget(self.gui_addr_label, 0, 1)
        
        info_layout.addWidget(QLabel("WebSocket地址:"), 0, 2)
        self.ws_addr_label = QLabel(f"{config.BACKEND_HOST}:{config.BACKEND_PORT}")
        self.ws_addr_label.setStyleSheet("color: #67C23A; font-weight: bold;")
        info_layout.addWidget(self.ws_addr_label, 0, 3)
        
        info_layout.addWidget(QLabel("本机IP:"), 1, 0)
        local_ips = get_local_ips()
        ip_text = ', '.join(local_ips) if local_ips else '未检测到'
        self.local_ip_label = QLabel(ip_text)
        self.local_ip_label.setStyleSheet("color: #E6A23C; font-weight: bold;")
        info_layout.addWidget(self.local_ip_label, 1, 1)
        
        info_layout.addWidget(QLabel("以太网IP:"), 1, 2)
        self.ethernet_ip_label = QLabel(config.ETHERNET_IP)
        self.ethernet_ip_label.setStyleSheet("color: #909399;")
        info_layout.addWidget(self.ethernet_ip_label, 1, 3)
        
        info_layout.setColumnStretch(1, 1)
        info_layout.setColumnStretch(3, 1)
        
        layout.addWidget(info_group)
        
        status_detail_group = QGroupBox("状态详情")
        status_detail_layout = QGridLayout(status_detail_group)
        status_detail_layout.setSpacing(12)
        
        status_detail_layout.addWidget(QLabel("前端在线:"), 0, 0)
        self.frontend_count_label = QLabel("0")
        self.frontend_count_label.setStyleSheet("color: #409EFF; font-weight: bold; font-size: 14px;")
        status_detail_layout.addWidget(self.frontend_count_label, 0, 1)
        
        status_detail_layout.addWidget(QLabel("GUI在线:"), 0, 2)
        self.gui_count_label = QLabel("0")
        self.gui_count_label.setStyleSheet("color: #67C23A; font-weight: bold; font-size: 14px;")
        status_detail_layout.addWidget(self.gui_count_label, 0, 3)
        
        status_detail_layout.addWidget(QLabel("心跳状态:"), 0, 4)
        self.heartbeat_status_label = QLabel("成功: 0 / 失败: 0")
        self.heartbeat_status_label.setStyleSheet("color: #909399; font-weight: bold; font-size: 12px;")
        status_detail_layout.addWidget(self.heartbeat_status_label, 0, 5)
        
        status_detail_layout.addWidget(QLabel("请求数量:"), 1, 0)
        self.request_count_label = QLabel("0")
        self.request_count_label.setStyleSheet("color: #E6A23C; font-weight: bold; font-size: 14px;")
        status_detail_layout.addWidget(self.request_count_label, 1, 1)
        
        status_detail_layout.addWidget(QLabel("空闲倒计时:"), 1, 2)
        self.idle_countdown_label = QLabel("--:--")
        self.idle_countdown_label.setStyleSheet("color: #409EFF; font-weight: bold; font-size: 14px;")
        status_detail_layout.addWidget(self.idle_countdown_label, 1, 3)
        
        status_detail_layout.addWidget(QLabel("最近状态:"), 2, 0)
        self.last_status_label = QLabel("等待更新...")
        self.last_status_label.setStyleSheet("color: #909399; font-size: 12px;")
        status_detail_layout.addWidget(self.last_status_label, 2, 1, 1, 5)
        
        status_detail_layout.setColumnStretch(1, 1)
        status_detail_layout.setColumnStretch(3, 1)
        status_detail_layout.setColumnStretch(5, 1)
        
        layout.addWidget(status_detail_group)
    
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
        
        from session_manager import session_manager
        expired_count = session_manager.cleanup_expired_sessions()
        if expired_count > 0:
            self.log_message(f"已清理 {expired_count} 个过期会话")
        
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
            
            from session_manager import session_manager
            session_manager.cleanup_all_sessions()
            self.log_message("已清理所有会话")
    
    @Slot()
    def on_service_started(self):
        self.is_service_running = True
        self.status_label.setText("● 服务状态: 运行中")
        self.status_label.setStyleSheet("""
            font-weight: bold; 
            font-size: 15px; 
            color: #67C23A;
            background-color: #f0f9eb;
            padding: 4px 8px;
            border-radius: 4px;
        """)
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
    
    def restart_websocket_client(self):
        self.log_message("正在重启WebSocket客户端...")
        self.stop_websocket_client()
        QTimer.singleShot(500, self.start_websocket_client)
    
    def update_connection_info(self):
        self.gui_addr_label.setText(f"{config.GUI_HOST}:{config.GUI_PORT}")
        self.ws_addr_label.setText(f"{config.BACKEND_HOST}:{config.BACKEND_PORT}")
        self.ethernet_ip_label.setText(config.ETHERNET_IP)
        self.log_message("连接信息已更新")
    
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
        self.frontend_count_label.setText(str(frontend_count))
        self.gui_count_label.setText(str(gui_count))
        self.log_message(f"状态更新: 前端在线 {frontend_count}, GUI在线 {gui_count}")
    
    @Slot(str)
    def on_ws_error(self, error):
        self.log_message(f"WebSocket错误: {error}")
    
    def update_ws_status_display(self, connected: bool):
        if connected:
            self.ws_status_label.setText("● WebSocket: 已连接")
            self.ws_status_label.setStyleSheet("""
                font-weight: bold; 
                font-size: 13px; 
                color: #67C23A;
                background-color: #f0f9eb;
                padding: 4px 8px;
                border-radius: 4px;
            """)
        else:
            self.ws_status_label.setText("● WebSocket: 未连接")
            self.ws_status_label.setStyleSheet("""
                font-weight: bold; 
                font-size: 13px; 
                color: #F56C6C;
                background-color: #fef0f0;
                padding: 4px 8px;
                border-radius: 4px;
            """)
    
    @Slot()
    def on_service_stopped(self):
        self.is_service_running = False
        self.status_label.setText("● 服务状态: 已停止")
        self.status_label.setStyleSheet("""
            font-weight: bold; 
            font-size: 15px; 
            color: #F56C6C;
            background-color: #fef0f0;
            padding: 4px 8px;
            border-radius: 4px;
        """)
        self.start_btn.setText("启动服务")
        self.tray_start_action.setText("启动服务")
        self.url_label.setText("")
        self.log_message("服务已停止")
        
        if self.request_log_timer:
            self.request_log_timer.stop()
            self.request_log_timer = None
        
        self.stop_websocket_client()
    
    def fetch_request_logs(self):
        from session_manager import session_manager
        from api_server import request_log
        import time
        
        success = session_manager.heartbeat_success_count
        failure = session_manager.heartbeat_failure_count
        self.heartbeat_status_label.setText(f"成功: {success} / 失败: {failure}")
        
        if success + failure > 0:
            success_rate = success / (success + failure) * 100
            if success_rate >= 80:
                self.heartbeat_status_label.setStyleSheet("color: #67C23A; font-weight: bold; font-size: 12px;")
            elif success_rate >= 50:
                self.heartbeat_status_label.setStyleSheet("color: #E6A23C; font-weight: bold; font-size: 12px;")
            else:
                self.heartbeat_status_label.setStyleSheet("color: #F56C6C; font-weight: bold; font-size: 12px;")
        
        self.request_count_label.setText(str(len(request_log)))
        
        elapsed = int(time.time() - session_manager.last_request_time)
        remaining = session_manager.idle_threshold - elapsed
        
        if remaining > 0:
            minutes = remaining // 60
            seconds = remaining % 60
            self.idle_countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
            self.idle_countdown_label.setStyleSheet("color: #409EFF; font-weight: bold; font-size: 14px;")
        else:
            self.idle_countdown_label.setText("空闲中")
            self.idle_countdown_label.setStyleSheet("color: #67C23A; font-weight: bold; font-size: 14px;")
    
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
        self.last_status_label.setText(f"[{timestamp}] {message}")
    
    def closeEvent(self, event):
        event.ignore()
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
        
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        
        QApplication.quit()

def main():
    try:
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(True)
        
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec())
    except Exception as e:
        import traceback
        error_msg = f"程序启动失败:\n{str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        try:
            error_log_path = os.path.join(get_base_path(), 'error.log')
            with open(error_log_path, 'w', encoding='utf-8') as f:
                f.write(error_msg)
        except:
            pass
        raise

if __name__ == '__main__':
    main()
