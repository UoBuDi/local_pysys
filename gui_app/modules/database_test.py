from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QMessageBox, QTextEdit, QComboBox
)
from PyQt6.QtCore import Qt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vue-element-plus-admin-master" / "backend"))

from utils.api_client import api_client


class DatabaseTestWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        select_group = QGroupBox("数据库选择")
        select_layout = QHBoxLayout()
        
        select_layout.addWidget(QLabel("数据库类型:"))
        self.db_type = QComboBox()
        self.db_type.addItems(["本地数据库", "远程数据库"])
        select_layout.addWidget(self.db_type)
        
        load_tables_btn = QPushButton("加载表列表")
        load_tables_btn.clicked.connect(self.load_tables)
        select_layout.addWidget(load_tables_btn)
        
        select_layout.addStretch()
        select_group.setLayout(select_layout)
        layout.addWidget(select_group)
        
        tables_group = QGroupBox("数据表列表")
        tables_layout = QVBoxLayout()
        
        self.tables_output = QTextEdit()
        self.tables_output.setReadOnly(True)
        tables_layout.addWidget(self.tables_output)
        
        tables_group.setLayout(tables_layout)
        layout.addWidget(tables_group)
        
        layout.addStretch()
    
    def load_tables(self):
        db_type = self.db_type.currentText()
        
        if db_type == "远程数据库":
            result = api_client.get("/api/database/tables/remote/")
        else:
            result = api_client.get("/api/database/tables/local/")
        
        if result.get("code") == 200:
            tables = result.get("data", [])
            self.tables_output.clear()
            self.tables_output.append(f"数据库: {db_type}\n")
            self.tables_output.append(f"共 {len(tables)} 个表:\n\n")
            for table in tables:
                self.tables_output.append(f"  - {table}")
        else:
            QMessageBox.warning(self, "错误", f"获取表列表失败: {result.get('message', '未知错误')}")
    
    def refresh(self):
        pass
