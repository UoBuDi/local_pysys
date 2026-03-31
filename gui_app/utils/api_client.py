import requests
import json
from typing import Optional, Dict, Any, List
from PyQt6.QtCore import QObject, pyqtSignal


class APIClient(QObject):
    error_signal = pyqtSignal(str)
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        super().__init__()
        self.base_url = base_url
        self.token: Optional[str] = None
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def set_token(self, token: str):
        self.token = token
        self.session.headers.update({
            "Authorization": f"Bearer {token}"
        })
    
    def clear_token(self):
        self.token = None
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        try:
            response = self.session.post(
                f"{self.base_url}/api/login/",
                json={"username": username, "password": password}
            )
            result = response.json()
            if result.get("code") == 200 and result.get("data", {}).get("token"):
                self.set_token(result["data"]["token"])
            return result
        except Exception as e:
            self.error_signal.emit(f"登录失败: {str(e)}")
            return {"code": 500, "message": str(e)}
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        try:
            response = self.session.get(
                f"{self.base_url}{endpoint}",
                params=params
            )
            return response.json()
        except Exception as e:
            self.error_signal.emit(f"GET请求失败: {str(e)}")
            return {"code": 500, "message": str(e)}
    
    def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        try:
            response = self.session.post(
                f"{self.base_url}{endpoint}",
                json=data
            )
            return response.json()
        except Exception as e:
            self.error_signal.emit(f"POST请求失败: {str(e)}")
            return {"code": 500, "message": str(e)}
    
    def put(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        try:
            response = self.session.put(
                f"{self.base_url}{endpoint}",
                json=data
            )
            return response.json()
        except Exception as e:
            self.error_signal.emit(f"PUT请求失败: {str(e)}")
            return {"code": 500, "message": str(e)}
    
    def delete(self, endpoint: str) -> Dict[str, Any]:
        try:
            response = self.session.delete(
                f"{self.base_url}{endpoint}"
            )
            return response.json()
        except Exception as e:
            self.error_signal.emit(f"DELETE请求失败: {str(e)}")
            return {"code": 500, "message": str(e)}
    
    def download(self, endpoint: str, save_path: str) -> bool:
        try:
            response = self.session.get(
                f"{self.base_url}{endpoint}",
                stream=True
            )
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            return False
        except Exception as e:
            self.error_signal.emit(f"下载失败: {str(e)}")
            return False
    
    def upload(self, endpoint: str, file_path: str) -> Dict[str, Any]:
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                headers = self.session.headers.copy()
                if "Content-Type" in headers:
                    del headers["Content-Type"]
                response = requests.post(
                    f"{self.base_url}{endpoint}",
                    files=files,
                    headers=headers
                )
            return response.json()
        except Exception as e:
            self.error_signal.emit(f"上传失败: {str(e)}")
            return {"code": 500, "message": str(e)}


api_client = APIClient()
