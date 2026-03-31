from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QMessageBox, QSpinBox, QComboBox
)
from PyQt6.QtCore import Qt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vue-element-plus-admin-master" / "backend"))

from utils.api_client import api_client


class ConfigWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        remote_group = QGroupBox("远程数据库配置")
        remote_layout = QFormLayout()
        
        self.remote_host = QLineEdit()
        self.remote_host.setPlaceholderText("例如: 10.143.163.38")
        remote_layout.addRow("主机地址:", self.remote_host)
        
        self.remote_port = QSpinBox()
        self.remote_port.setRange(1, 65535)
        self.remote_port.setValue(3306)
        remote_layout.addRow("端口:", self.remote_port)
        
        self.remote_user = QLineEdit()
        remote_layout.addRow("用户名:", self.remote_user)
        
        self.remote_password = QLineEdit()
        self.remote_password.setEchoMode(QLineEdit.EchoMode.Password)
        remote_layout.addRow("密码:", self.remote_password)
        
        self.remote_db = QLineEdit()
        self.remote_db.setPlaceholderText("数据库名称")
        remote_layout.addRow("数据库:", self.remote_db)
        
        remote_group.setLayout(remote_layout)
        layout.addWidget(remote_group)
        
        local_group = QGroupBox("本地数据库配置")
        local_layout = QFormLayout()
        
        self.local_host = QLineEdit()
        self.local_host.setText("127.0.0.1")
        local_layout.addRow("主机地址:", self.local_host)
        
        self.local_port = QSpinBox()
        self.local_port.setRange(1, 65535)
        self.local_port.setValue(3306)
        local_layout.addRow("端口:", self.local_port)
        
        self.local_user = QLineEdit()
        self.local_user.setText("root")
        local_layout.addRow("用户名:", self.local_user)
        
        self.local_password = QLineEdit()
        self.local_password.setEchoMode(QLineEdit.EchoMode.Password)
        local_layout.addRow("密码:", self.local_password)
        
        self.local_db = QLineEdit()
        self.local_db.setText("system_db")
        local_layout.addRow("数据库:", self.local_db)
        
        local_group.setLayout(local_layout)
        layout.addWidget(local_group)
        
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("保存配置")
        save_btn.clicked.connect(self.save_config)
        btn_layout.addWidget(save_btn)
        
        test_remote_btn = QPushButton("测试远程连接")
        test_remote_btn.clicked.connect(self.test_remote)
        btn_layout.addWidget(test_remote_btn)
        
        test_local_btn = QPushButton("测试本地连接")
        test_local_btn.clicked.connect(self.test_local)
        btn_layout.addWidget(test_local_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        layout.addStretch()
    
    def load_config(self):
        result = api_client.get("/api/config/")
        if result.get("code") == 200:
            config = result.get("data", {})
            
            remote = config.get("REMOTE_DB", {})
            self.remote_host.setText(remote.get("host", ""))
            self.remote_port.setValue(remote.get("port", 3306))
            self.remote_user.setText(remote.get("user", ""))
            self.remote_password.setText(remote.get("password", ""))
            self.remote_db.setText(remote.get("database", ""))
            
            local = config.get("USER_DB", {})
            self.local_host.setText(local.get("host", "127.0.0.1"))
            self.local_port.setValue(local.get("port", 3306))
            self.local_user.setText(local.get("user", "root"))
            self.local_password.setText(local.get("password", ""))
            self.local_db.setText(local.get("database", "system_db"))
    
    def save_config(self):
        config = {
            "REMOTE_DB": {
                "host": self.remote_host.text(),
                "port": self.remote_port.value(),
                "user": self.remote_user.text(),
                "password": self.remote_password.text(),
                "database": self.remote_db.text()
            },
            "USER_DB": {
                "host": self.local_host.text(),
                "port": self.local_port.value(),
                "user": self.local_user.text(),
                "password": self.local_password.text(),
                "database": self.local_db.text()
            }
        }
        
        result = api_client.post("/api/config/", config)
        if result.get("code") == 200:
            QMessageBox.information(self, "成功", "配置保存成功")
        else:
            QMessageBox.warning(self, "错误", f"保存失败: {result.get('message', '未知错误')}")
    
    def test_remote(self):
        result = api_client.post("/api/config/test-remote/", {
            "host": self.remote_host.text(),
            "port": self.remote_port.value(),
            "user": self.remote_user.text(),
            "password": self.remote_password.text(),
            "database": self.remote_db.text()
        })
        
        if result.get("code") == 200:
            QMessageBox.information(self, "成功", "远程数据库连接成功")
        else:
            QMessageBox.warning(self, "失败", f"连接失败: {result.get('message', '未知错误')}")
    
    def test_local(self):
        result = api_client.post("/api/config/test-local/", {
            "host": self.local_host.text(),
            "port": self.local_port.value(),
            "user": self.local_user.text(),
            "password": self.local_password.text(),
            "database": self.local_db.text()
        })
        
        if result.get("code") == 200:
            QMessageBox.information(self, "成功", "本地数据库连接成功")
        else:
            QMessageBox.warning(self, "失败", f"连接失败: {result.get('message', '未知错误')}")
    
    def refresh(self):
        self.load_config()
