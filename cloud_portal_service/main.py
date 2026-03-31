import sys
import os
import threading
import logging
import requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox, QCheckBox, QGroupBox,
    QFormLayout, QMessageBox, QSystemTrayIcon, QMenu, QTextEdit,
    QTabWidget, QDialog, QDialogButtonBox, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, Slot
from PySide6.QtGui import QIcon, QAction
from werkzeug.serving import run_simple, make_server
from api_server import app
from config import config, DEFAULT_CONFIG, get_base_path
from network_utils import get_local_ips, check_network_connectivity

def get_log_file_path():
    return os.path.join(get_base_path(), 'service.log')

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(get_log_file_path(), encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

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
            self.started_signal.emit()
            self.server = make_server(self.host, self.port, app, threaded=True)
            self.server.serve_forever()
        except Exception as e:
            logger.error(f"Flask服务错误: {e}")
            self.error_signal.emit(str(e))
        finally:
            self._is_running = False
            self.stopped_signal.emit()
    
    def stop(self):
        self._is_running = False
        if self.server:
            self.server.shutdown()
        self.wait(3000)
        if self.isRunning():
            self.terminate()

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
        network_layout = QFormLayout(network_tab)
        
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("绑定到以太网网卡IP")
        network_layout.addRow("服务地址:", self.host_input)
        
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(9000)
        network_layout.addRow("服务端口:", self.port_input)
        
        local_ips = get_local_ips()
        ip_label = QLabel(f"本机IP: {', '.join(local_ips) if local_ips else '未检测到'}")
        ip_label.setWordWrap(True)
        network_layout.addRow("", ip_label)
        
        self.ethernet_ip_input = QLineEdit()
        self.ethernet_ip_input.setPlaceholderText("以太网IP (业务网络)")
        network_layout.addRow("以太网IP:", self.ethernet_ip_input)
        
        self.ethernet2_ip_input = QLineEdit()
        self.ethernet2_ip_input.setPlaceholderText("以太网2IP (云门户网络)")
        network_layout.addRow("以太网2IP:", self.ethernet2_ip_input)
        
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
    
    @Slot()
    def save_and_accept(self):
        config.set('gui_host', self.host_input.text())
        config.set('gui_port', self.port_input.value())
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
        
        QMessageBox.information(self, "成功", "配置已保存")
        self.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.flask_thread = None
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
        
        request_group = QGroupBox("请求信息")
        request_layout = QVBoxLayout(request_group)
        
        self.request_table = QTableWidget()
        self.request_table.setColumnCount(4)
        self.request_table.setHorizontalHeaderLabels(["时间", "方法", "路径", "状态码"])
        self.request_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.request_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.request_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.request_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.request_table.setColumnWidth(0, 80)
        self.request_table.setColumnWidth(1, 60)
        self.request_table.setColumnWidth(3, 60)
        self.request_table.setMaximumHeight(150)
        self.request_table.setAlternatingRowColors(True)
        request_layout.addWidget(self.request_table)
        
        clear_request_btn = QPushButton("清空请求记录")
        clear_request_btn.clicked.connect(self.clear_request_table)
        request_layout.addWidget(clear_request_btn)
        
        layout.addWidget(request_group)
        
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
    
    def clear_request_table(self):
        self.request_table.setRowCount(0)
    
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
            self.flask_thread = FlaskThread(config.GUI_HOST, config.GUI_PORT)
            self.flask_thread.started_signal.connect(self.on_service_started)
            self.flask_thread.stopped_signal.connect(self.on_service_stopped)
            self.flask_thread.error_signal.connect(self.on_service_error)
            self.flask_thread.start()
            
            self.log_message(f"正在启动服务 {config.GUI_HOST}:{config.GUI_PORT}...")
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
        self.url_label.setText(f"访问地址: http://{config.GUI_HOST}:{config.GUI_PORT}")
        self.log_message("服务启动成功")
        
        self.request_log_timer = QTimer(self)
        self.request_log_timer.timeout.connect(self.fetch_request_logs)
        self.request_log_timer.start(2000)
    
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
    
    def fetch_request_logs(self):
        try:
            response = requests.get(
                f"http://{config.GUI_HOST}:{config.GUI_PORT}/api/portal/request-logs",
                timeout=2
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200:
                    logs = data.get('data', [])
                    self.update_request_table(logs)
        except:
            pass
    
    def update_request_table(self, logs):
        current_count = self.request_table.rowCount()
        new_logs = logs[current_count:] if len(logs) > current_count else []
        
        for log in new_logs:
            row = self.request_table.rowCount()
            self.request_table.insertRow(row)
            self.request_table.setItem(row, 0, QTableWidgetItem(log.get('time', '')))
            self.request_table.setItem(row, 1, QTableWidgetItem(log.get('method', '')))
            self.request_table.setItem(row, 2, QTableWidgetItem(log.get('path', '')))
            
            status_code = log.get('response_code', '')
            status_item = QTableWidgetItem(str(status_code))
            if status_code == 200:
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif status_code >= 400:
                status_item.setForeground(Qt.GlobalColor.red)
            self.request_table.setItem(row, 3, status_item)
            
            self.request_table.scrollToBottom()
    
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
