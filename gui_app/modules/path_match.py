from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QMessageBox, QTableWidget, QTableWidgetItem,
    QComboBox, QHeaderView, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vue-element-plus-admin-master" / "backend"))

from utils.api_client import api_client


class PathMatchWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_tables()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        config_group = QGroupBox("查询配置")
        config_layout = QFormLayout()
        
        self.table_select = QComboBox()
        config_layout.addRow("数据表:", self.table_select)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        filter_group = QGroupBox("筛选条件")
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("车牌号:"))
        self.plate_input = QLineEdit()
        filter_layout.addWidget(self.plate_input)
        
        filter_layout.addWidget(QLabel("省份:"))
        self.province_input = QLineEdit()
        filter_layout.addWidget(self.province_input)
        
        search_btn = QPushButton("查询")
        search_btn.clicked.connect(self.search)
        filter_layout.addWidget(search_btn)
        
        filter_layout.addStretch()
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "序号", "车牌号", "入口站", "出口站", "入口时间",
            "出口站时间", "行驶路径", "匹配状态"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
    
    def load_tables(self):
        result = api_client.get("/api/path-match/tables/")
        
        if result.get("code") == 200:
            tables = result.get("data", [])
            self.table_select.clear()
            for table in tables:
                self.table_select.addItem(table)
    
    def search(self):
        table_name = self.table_select.currentText()
        
        if not table_name:
            QMessageBox.warning(self, "提示", "请选择数据表")
            return
        
        result = api_client.post("/api/path-match/search/", {
            "table": table_name,
            "plate": self.plate_input.text(),
            "province": self.province_input.text()
        })
        
        if result.get("code") == 200:
            data = result.get("data", [])
            self.table.setRowCount(len(data))
            
            for row, item in enumerate(data):
                self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
                self.table.setItem(row, 1, QTableWidgetItem(item.get("plate", "")))
                self.table.setItem(row, 2, QTableWidgetItem(item.get("entry_station", "")))
                self.table.setItem(row, 3, QTableWidgetItem(item.get("exit_station", "")))
                self.table.setItem(row, 4, QTableWidgetItem(item.get("entry_time", "")))
                self.table.setItem(row, 5, QTableWidgetItem(item.get("exit_time", "")))
                self.table.setItem(row, 6, QTableWidgetItem(item.get("path", "")))
                self.table.setItem(row, 7, QTableWidgetItem(item.get("match_status", "")))
        else:
            QMessageBox.warning(self, "错误", f"查询失败: {result.get('message', '未知错误')}")
    
    def refresh(self):
        self.load_tables()
