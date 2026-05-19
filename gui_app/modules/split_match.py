from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QMessageBox, QTableWidget, QTableWidgetItem,
    QComboBox, QHeaderView, QTextEdit, QProgressBar,
    QFileDialog
)
from PyQt6.QtCore import Qt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vue-element-plus-admin-master" / "backend"))

from utils.api_client import api_client


class SplitMatchWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_databases()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        config_group = QGroupBox("查询配置")
        config_layout = QFormLayout()
        
        self.db_select = QComboBox()
        self.db_select.currentTextChanged.connect(self.load_tables)
        config_layout.addRow("数据库:", self.db_select)
        
        self.table_select = QComboBox()
        config_layout.addRow("数据表:", self.table_select)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        filter_group = QGroupBox("筛选条件")
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("车牌号:"))
        self.plate_input = QLineEdit()
        filter_layout.addWidget(self.plate_input)
        
        search_btn = QPushButton("查询")
        search_btn.clicked.connect(self.search_data)
        filter_layout.addWidget(search_btn)
        
        export_btn = QPushButton("导出")
        export_btn.clicked.connect(self.export_data)
        filter_layout.addWidget(export_btn)
        
        filter_layout.addStretch()
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "车牌号", "入口站", "出口站", "入口时间",
            "出口时间", "金额", "车型", "介质类型", "状态"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
    
    def load_databases(self):
        result = api_client.get("/api/split-match/databases/")
        
        if result.get("code") == 200:
            databases = result.get("data", [])
            self.db_select.clear()
            for db in databases:
                self.db_select.addItem(db)
    
    def load_tables(self):
        db_name = self.db_select.currentText()
        if not db_name:
            return
        
        result = api_client.get("/api/split-match/tables/", {"database": db_name})
        
        if result.get("code") == 200:
            tables = result.get("data", [])
            self.table_select.clear()
            for table in tables:
                self.table_select.addItem(table)
    
    def search_data(self):
        db_name = self.db_select.currentText()
        table_name = self.table_select.currentText()
        
        if not db_name or not table_name:
            QMessageBox.warning(self, "提示", "请选择数据库和数据表")
            return
        
        result = api_client.get("/api/split-match/data/", {
            "database": db_name,
            "table": table_name,
            "plate": self.plate_input.text()
        })
        
        if result.get("code") == 200:
            data = result.get("data", [])
            self.table.setRowCount(len(data))
            
            for row, item in enumerate(data):
                self.table.setItem(row, 0, QTableWidgetItem(str(item.get("id", ""))))
                self.table.setItem(row, 1, QTableWidgetItem(item.get("plate", "")))
                self.table.setItem(row, 2, QTableWidgetItem(item.get("entry_station", "")))
                self.table.setItem(row, 3, QTableWidgetItem(item.get("exit_station", "")))
                self.table.setItem(row, 4, QTableWidgetItem(item.get("entry_time", "")))
                self.table.setItem(row, 5, QTableWidgetItem(item.get("exit_time", "")))
                self.table.setItem(row, 6, QTableWidgetItem(str(item.get("amount", ""))))
                self.table.setItem(row, 7, QTableWidgetItem(item.get("vehicle_type", "")))
                self.table.setItem(row, 8, QTableWidgetItem(item.get("media_type", "")))
                self.table.setItem(row, 9, QTableWidgetItem(item.get("status", "")))
        else:
            QMessageBox.warning(self, "错误", f"查询失败: {result.get('message', '未知错误')}")
    
    def export_data(self):
        db_name = self.db_select.currentText()
        table_name = self.table_select.currentText()
        
        if not db_name or not table_name:
            QMessageBox.warning(self, "提示", "请选择数据库和数据表")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", f"{table_name}.xlsx", "Excel文件 (*.xlsx)"
        )
        
        if file_path:
            result = api_client.download(
                f"/api/split-match/export/?database={db_name}&table={table_name}",
                file_path
            )
            if result:
                QMessageBox.information(self, "成功", f"数据已导出到: {file_path}")
            else:
                QMessageBox.warning(self, "错误", "导出失败")
    
    def refresh(self):
        self.load_databases()
