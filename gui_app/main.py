import sys
import os
import threading
import subprocess
import webbrowser
import time
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QToolBar, QStatusBar, QLabel, QPushButton,
    QTabWidget, QMessageBox, QProgressBar, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QAction, QIcon, QFont

sys.path.insert(0, str(Path(__file__).parent.parent / "vue-element-plus-admin-master" / "backend"))
import uvicorn
from main import app


class BackendThread(QThread):
    status_signal = pyqtSignal(str)
    
    def __init__(self, host="0.0.0.0", port=8000):
        super().__init__()
        self.host = host
        self.port = port
        self.running = True
    
    def run(self):
        self.status_signal.emit(f"后端服务启动中... http://{self.host}:{self.port}")
        config = uvicorn.Config(
            app,
            host=self.host,
            port=self.port,
            log_level="info",
            access_log=False
        )
        server = uvicorn.Server(config)
        server.run()
    
    def stop(self):
        self.running = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.backend_thread = None
        self.backend_running = False
        self.init_ui()
        self.start_backend()
    
    def init_ui(self):
        self.setWindowTitle("数据管理系统 - 桌面版")
        self.setGeometry(100, 100, 1400, 900)
        
        self.create_menu_bar()
        self.create_tool_bar()
        self.create_status_bar()
        self.create_central_widget()
    
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("文件(&F)")
        
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        system_menu = menubar.addMenu("系统管理(&S)")
        
        config_action = QAction("系统配置(&C)", self)
        config_action.triggered.connect(self.show_config)
        system_menu.addAction(config_action)
        
        db_test_action = QAction("数据库连接测试(&D)", self)
        db_test_action.triggered.connect(self.test_database)
        system_menu.addAction(db_test_action)
        
        user_menu = menubar.addMenu("用户管理(&U)")
        
        user_list_action = QAction("用户列表(&L)", self)
        user_list_action.triggered.connect(self.show_user_list)
        user_menu.addAction(user_list_action)
        
        role_action = QAction("角色管理(&R)", self)
        role_action.triggered.connect(self.show_role_list)
        user_menu.addAction(role_action)
        
        menu_action = QAction("菜单管理(&M)", self)
        menu_action.triggered.connect(self.show_menu_list)
        user_menu.addAction(menu_action)
        
        perm_action = QAction("权限管理(&P)", self)
        perm_action.triggered.connect(self.show_permission_list)
        user_menu.addAction(perm_action)
        
        data_menu = menubar.addMenu("数据管理(&D)")
        
        sync_action = QAction("数据同步(&S)", self)
        sync_action.triggered.connect(self.show_sync)
        data_menu.addAction(sync_action)
        
        split_action = QAction("拆分匹配(&M)", self)
        split_action.triggered.connect(self.show_split_match)
        data_menu.addAction(split_action)
        
        detail_action = QAction("详单查询(&Q)", self)
        detail_action.triggered.connect(self.show_detail_query)
        data_menu.addAction(detail_action)
        
        path_action = QAction("路径匹配(&P)", self)
        path_action.triggered.connect(self.show_path_match)
        data_menu.addAction(path_action)
        
        record_menu = menubar.addMenu("记录管理(&R)")
        
        special_action = QAction("特情记录(&S)", self)
        special_action.triggered.connect(self.show_special_records)
        record_menu.addAction(special_action)
        
        schedule_action = QAction("排班管理(&C)", self)
        schedule_action.triggered.connect(self.show_scheduling)
        record_menu.addAction(schedule_action)
        
        task_menu = menubar.addMenu("任务管理(&T)")
        
        task_list_action = QAction("定时任务(&T)", self)
        task_list_action.triggered.connect(self.show_scheduled_tasks)
        task_menu.addAction(task_list_action)
        
        history_action = QAction("执行历史(&H)", self)
        history_action.triggered.connect(self.show_task_history)
        task_menu.addAction(history_action)
        
        help_menu = menubar.addMenu("帮助(&H)")
        
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_tool_bar(self):
        toolbar = self.addToolBar("主工具栏")
        toolbar.setMovable(False)
        
        refresh_action = QAction("刷新", self)
        refresh_action.triggered.connect(self.refresh_current_tab)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        self.backend_status_label = QLabel("后端服务: 未启动")
        self.backend_status_label.setStyleSheet("color: gray; padding: 5px;")
        toolbar.addWidget(self.backend_status_label)
        
        toolbar.addSeparator()
        
        open_browser_action = QAction("打开浏览器", self)
        open_browser_action.triggered.connect(self.open_browser)
        toolbar.addAction(open_browser_action)
    
    def create_status_bar(self):
        self.statusBar().showMessage("就绪")
    
    def create_central_widget(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        layout.addWidget(self.tab_widget)
    
    def start_backend(self):
        self.backend_thread = BackendThread()
        self.backend_thread.status_signal.connect(self.update_backend_status)
        self.backend_thread.start()
        self.backend_running = True
    
    def update_backend_status(self, message):
        self.backend_status_label.setText(f"后端服务: {message}")
        self.backend_status_label.setStyleSheet("color: green; padding: 5px;")
        self.statusBar().showMessage(message)
    
    def open_browser(self):
        webbrowser.open("http://localhost:8000/docs")
    
    def add_tab(self, widget, title):
        index = self.tab_widget.addTab(widget, title)
        self.tab_widget.setCurrentIndex(index)
        return index
    
    def close_tab(self, index):
        if self.tab_widget.count() > 0:
            self.tab_widget.removeTab(index)
    
    def refresh_current_tab(self):
        current_widget = self.tab_widget.currentWidget()
        if current_widget and hasattr(current_widget, 'refresh'):
            current_widget.refresh()
    
    def show_config(self):
        from modules.config import ConfigWidget
        self.add_tab(ConfigWidget(), "系统配置")
    
    def test_database(self):
        from modules.database_test import DatabaseTestWidget
        self.add_tab(DatabaseTestWidget(), "数据库连接测试")
    
    def show_user_list(self):
        from modules.users import UserListWidget
        self.add_tab(UserListWidget(), "用户列表")
    
    def show_role_list(self):
        from modules.roles import RoleListWidget
        self.add_tab(RoleListWidget(), "角色管理")
    
    def show_menu_list(self):
        from modules.menus import MenuListWidget
        self.add_tab(MenuListWidget(), "菜单管理")
    
    def show_permission_list(self):
        from modules.permissions import PermissionListWidget
        self.add_tab(PermissionListWidget(), "权限管理")
    
    def show_sync(self):
        from modules.sync import SyncWidget
        self.add_tab(SyncWidget(), "数据同步")
    
    def show_split_match(self):
        from modules.split_match import SplitMatchWidget
        self.add_tab(SplitMatchWidget(), "拆分匹配")
    
    def show_detail_query(self):
        from modules.detail_query import DetailQueryWidget
        self.add_tab(DetailQueryWidget(), "详单查询")
    
    def show_path_match(self):
        from modules.path_match import PathMatchWidget
        self.add_tab(PathMatchWidget(), "路径匹配")
    
    def show_special_records(self):
        from modules.special_records import SpecialRecordsWidget
        self.add_tab(SpecialRecordsWidget(), "特情记录")
    
    def show_scheduling(self):
        from modules.scheduling import SchedulingWidget
        self.add_tab(SchedulingWidget(), "排班管理")
    
    def show_scheduled_tasks(self):
        from modules.scheduled_tasks import ScheduledTasksWidget
        self.add_tab(ScheduledTasksWidget(), "定时任务")
    
    def show_task_history(self):
        from modules.task_history import TaskHistoryWidget
        self.add_tab(TaskHistoryWidget(), "执行历史")
    
    def show_about(self):
        QMessageBox.about(
            self,
            "关于",
            "数据管理系统 - 桌面版\n\n"
            "版本: 1.0.0\n\n"
            "功能模块:\n"
            "- 系统配置与数据库管理\n"
            "- 用户权限管理\n"
            "- 数据同步与拆分匹配\n"
            "- 详单查询与路径匹配\n"
            "- 特情记录与排班管理\n"
            "- 定时任务管理\n\n"
            "© 2026 数据管理系统"
        )
    
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要退出程序吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.backend_thread:
                self.backend_thread.terminate()
            event.accept()
        else:
            event.ignore()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
