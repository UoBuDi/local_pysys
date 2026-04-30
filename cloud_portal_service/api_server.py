import logging
import uuid
import json
import time
import os
import threading
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from session_manager import session_manager
from config import config, get_base_path, Limits
from ai_audit_client import AIAuditClient
from captcha_ocr import captcha_ocr, is_ocr_available
from datetime import datetime
from collections import deque
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class RequestLogger:
    _instance: Optional['RequestLogger'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'RequestLogger':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._request_log: deque = deque(maxlen=Limits.REQUEST_LOG_SIZE)
        self._request_info_log: deque = deque(maxlen=Limits.REQUEST_INFO_SIZE)
        self._latest_response: Optional[Dict[str, Any]] = None
        self._log_lock = threading.Lock()
        
        log_dir = get_base_path()
        os.makedirs(log_dir, exist_ok=True)
        self._data_log_file = os.path.join(log_dir, 'data.log')
    
    def log_request(self, method: str, path: str, params: Optional[Dict] = None, response_code: Optional[int] = None) -> None:
        log_entry = {
            'time': datetime.now().strftime('%H:%M:%S'),
            'method': method,
            'path': path,
            'params': params,
            'response_code': response_code
        }
        with self._log_lock:
            self._request_log.append(log_entry)
        logger.info(f"请求: {method} {path} - {response_code}")
    
    def log_request_info(self, username: str, request_time: str, method: str, path: str, data: Optional[Dict] = None, source: str = 'backend') -> None:
        info_entry = {
            'id': str(uuid.uuid4())[:8],
            'username': username or '未知',
            'request_time': request_time or datetime.now().isoformat(),
            'method': method,
            'path': path,
            'data': data,
            'source': source,
            'display_time': datetime.now().strftime('%H:%M:%S')
        }
        with self._log_lock:
            self._request_info_log.append(info_entry)
        logger.info(f"[请求信息] {username} - {method} {path}")
    
    def log_to_file(self, method: str, path: str, data: Optional[Dict] = None, response: Optional[Dict] = None) -> None:
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            log_entry = {
                'timestamp': timestamp,
                'type': 'request',
                'method': method,
                'path': path,
                'data': data
            }
            with open(self._data_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            if response is not None:
                response_entry = {
                    'timestamp': timestamp,
                    'type': 'response',
                    'method': method,
                    'path': path,
                    'data': response
                }
                with open(self._data_log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(response_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"写入请求日志失败: {e}")
    
    def get_request_logs(self) -> List[Dict[str, Any]]:
        with self._log_lock:
            return list(self._request_log)
    
    def get_request_info_logs(self) -> List[Dict[str, Any]]:
        with self._log_lock:
            return list(self._request_info_log)
    
    def update_latest_response(self, response_data: Dict[str, Any]) -> None:
        with self._log_lock:
            self._latest_response = response_data
    
    def get_latest_response(self) -> Optional[Dict[str, Any]]:
        with self._log_lock:
            return self._latest_response


request_logger = RequestLogger()

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Forwarded-User", "X-Request-Time"]
    }
})


def get_request_logger() -> RequestLogger:
    return request_logger


@app.before_request
def before_request():
    g.forwarded_user = request.headers.get('X-Forwarded-User', '未知')
    g.request_time = request.headers.get('X-Request-Time', datetime.now().isoformat())


@app.route('/api/portal/health', methods=['GET'])
def health_check():
    get_request_logger().log_request('GET', '/api/portal/health', response_code=200)
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'status': 'healthy',
            'service': 'cloud-portal-service',
            'version': config.VERSION
        }
    })


@app.route('/api/portal/request-logs', methods=['GET'])
def get_logs():
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': get_request_logger().get_request_logs()
    })


@app.route('/api/portal/request-info', methods=['GET'])
def get_request_info():
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': get_request_logger().get_request_info_logs()
    })


@app.route('/api/portal/latest-response', methods=['GET'])
def get_latest_response():
    latest = get_request_logger().get_latest_response()
    if latest:
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': latest
        })
    else:
        return jsonify({
            'code': 404,
            'message': '暂无响应数据',
            'data': None
        })


@app.route('/api/portal/captcha', methods=['GET'])
def get_captcha():
    session_manager.update_activity()
    start_time = time.time()
    session_id = request.args.get('session_id')
    
    client_ip = request.remote_addr or 'unknown'
    allowed, remaining = session_manager.check_rate_limit(client_ip)
    if not allowed:
        logger.warning(f"[频率限制] 客户端 {client_ip} 验证码请求过于频繁")
        get_request_logger().log_request('GET', '/api/portal/captcha', {'session_id': session_id}, 429)
        return jsonify({
            'code': 429,
            'message': f'请求过于频繁，请稍后再试'
        }), 429
    
    get_request_logger().log_request_info(
        username=g.forwarded_user,
        request_time=g.request_time,
        method='GET',
        path='/api/portal/captcha',
        data={'session_id': session_id, 'remaining': remaining},
        source='backend'
    )
    
    logger.info(f"[验证码] 请求开始 - session_id: {session_id}, client_ip: {client_ip}, remaining: {remaining}")
    logger.info(f"[验证码] 配置信息 - PORTAL_BASE_URL: {config.PORTAL_BASE_URL}, ETHERNET2_IP: {config.ETHERNET2_IP}")
    
    if not session_id:
        session_id = str(uuid.uuid4())
    
    client = session_manager.get_session(session_id)
    if not client:
        logger.info(f"[验证码] 创建新会话 - session_id: {session_id}")
        client = session_manager.create_session(session_id)
    else:
        logger.info(f"[验证码] 使用已有会话 - session_id: {session_id}")
    
    try:
        logger.info(f"[验证码] 调用PortalClient.get_captcha() - 源IP: {client.source_ip or '默认'}")
        result = client.get_captcha()
        elapsed = time.time() - start_time
        logger.info(f"[验证码] PortalClient返回 - 耗时: {elapsed:.2f}s, 成功: {result['success']}")
        
        if result['success']:
            session_manager.store_captcha(session_id, result['uuid'])
            get_request_logger().log_request('GET', '/api/portal/captcha', {'session_id': session_id}, 200)
            logger.info(f"[验证码] 成功返回验证码 - 总耗时: {elapsed:.2f}s")
            response_data = {
                'code': 200,
                'message': 'success',
                'data': {
                    'session_id': session_id,
                    'img': result['img'][:100] + '...' if result['img'] else None,
                    'uuid': result['uuid']
                }
            }
            get_request_logger().log_to_file('GET', '/api/portal/captcha', {'session_id': session_id}, response_data)
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'session_id': session_id,
                    'img': result['img'],
                    'uuid': result['uuid']
                }
            })
        else:
            get_request_logger().log_request('GET', '/api/portal/captcha', {'session_id': session_id}, 500)
            logger.error(f"[验证码] 失败 - 错误: {result.get('error')}, 总耗时: {elapsed:.2f}s")
            response_data = {
                'code': 500,
                'message': result['error']
            }
            get_request_logger().log_to_file('GET', '/api/portal/captcha', {'session_id': session_id}, response_data)
            return jsonify(response_data), 500
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[验证码] 异常 - 错误: {e}, 总耗时: {elapsed:.2f}s", exc_info=True)
        get_request_logger().log_request('GET', '/api/portal/captcha', {'session_id': session_id}, 500)
        response_data = {
            'code': 500,
            'message': f'获取验证码异常: {str(e)}'
        }
        get_request_logger().log_to_file('GET', '/api/portal/captcha', {'session_id': session_id}, response_data)
        return jsonify(response_data), 500


@app.route('/api/portal/login', methods=['POST'])
def login():
    session_manager.update_activity()
    data = request.json
    
    get_request_logger().log_request_info(
        username=g.forwarded_user,
        request_time=g.request_time,
        method='POST',
        path='/api/portal/login',
        data={'session_id': data.get('session_id') if data else None},
        source='backend'
    )
    
    if not data:
        get_request_logger().log_request('POST', '/api/portal/login', None, 400)
        response_data = {'code': 400, 'message': '请求体不能为空'}
        get_request_logger().log_to_file('POST', '/api/portal/login', data, response_data)
        return jsonify(response_data), 400
    
    session_id = data.get('session_id')
    username = data.get('username')
    password = data.get('password')
    captcha = data.get('captcha')
    uuid_str = data.get('uuid')
    
    if not all([session_id, username, password, captcha, uuid_str]):
        get_request_logger().log_request('POST', '/api/portal/login', {'session_id': session_id}, 400)
        response_data = {'code': 400, 'message': '缺少必要参数'}
        get_request_logger().log_to_file('POST', '/api/portal/login', data, response_data)
        return jsonify(response_data), 400
    
    valid_captcha, captcha_error = session_manager.validate_captcha(session_id, uuid_str)
    if not valid_captcha:
        logger.warning(f"[登录] 验证码验证失败 - session: {session_id}, uuid: {uuid_str}, error: {captcha_error}")
        get_request_logger().log_request('POST', '/api/portal/login', {'session_id': session_id}, 400)
        response_data = {'code': 400, 'message': captcha_error}
        get_request_logger().log_to_file('POST', '/api/portal/login', data, response_data)
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    if not client:
        get_request_logger().log_request('POST', '/api/portal/login', {'session_id': session_id}, 401)
        response_data = {'code': 401, 'message': '会话已过期，请刷新验证码'}
        get_request_logger().log_to_file('POST', '/api/portal/login', data, response_data)
        return jsonify(response_data), 401
    
    result = client.login(username, password, captcha, uuid_str)
    
    if result['success']:
        client.set_owner(username)
        session_manager.update_timestamp(session_id)
        get_request_logger().log_request('POST', '/api/portal/login', {'session_id': session_id, 'username': username}, 200)
        response_data = {
            'code': 200,
            'message': '登录成功',
            'data': {
                'user_info': result['user_info'],
                'access_token': result.get('access_token'),
                'refresh_token': result.get('refresh_token'),
                'redirect_uri': result.get('redirect_uri')
            }
        }
        get_request_logger().log_to_file('POST', '/api/portal/login', data, response_data)
        return jsonify(response_data)
    else:
        get_request_logger().log_request('POST', '/api/portal/login', {'session_id': session_id, 'username': username}, 401)
        response_data = {'code': 401, 'message': result['error']}
        get_request_logger().log_to_file('POST', '/api/portal/login', data, response_data)
        return jsonify(response_data), 401


@app.route('/api/portal/query', methods=['POST'])
def query():
    session_manager.update_activity()
    data = request.json
    
    get_request_logger().log_request_info(
        username=g.forwarded_user,
        request_time=g.request_time,
        method='POST',
        path='/api/portal/query',
        data={'session_id': data.get('session_id') if data else None},
        source='backend'
    )
    
    if not data:
        get_request_logger().log_request('POST', '/api/portal/query', None, 400)
        response_data = {'code': 400, 'message': '请求体不能为空'}
        get_request_logger().log_to_file('POST', '/api/portal/query', data, response_data)
        return jsonify(response_data), 400
    
    session_id = data.get('session_id')
    query_params = data.get('query_params')
    
    if not session_id:
        get_request_logger().log_request('POST', '/api/portal/query', None, 400)
        response_data = {'code': 400, 'message': '缺少session_id'}
        get_request_logger().log_to_file('POST', '/api/portal/query', data, response_data)
        return jsonify(response_data), 400
    
    if not query_params:
        get_request_logger().log_request('POST', '/api/portal/query', {'session_id': session_id}, 400)
        response_data = {'code': 400, 'message': '缺少查询参数'}
        get_request_logger().log_to_file('POST', '/api/portal/query', data, response_data)
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    if not client:
        get_request_logger().log_request('POST', '/api/portal/query', {'session_id': session_id}, 401)
        response_data = {'code': 401, 'message': '未登录或会话已过期'}
        get_request_logger().log_to_file('POST', '/api/portal/query', data, response_data)
        return jsonify(response_data), 401
    
    result = client.query_pass_data(query_params)
    
    if result['success']:
        session_manager.update_timestamp(session_id)
        get_request_logger().log_request('POST', '/api/portal/query', {'session_id': session_id}, 200)
        response_data = {'code': 200, 'message': 'success', 'data': result['data']}
        get_request_logger().log_to_file('POST', '/api/portal/query', data, response_data)
        return jsonify(response_data)
    else:
        get_request_logger().log_request('POST', '/api/portal/query', {'session_id': session_id}, 500)
        response_data = {'code': 500, 'message': result['error']}
        get_request_logger().log_to_file('POST', '/api/portal/query', data, response_data)
        return jsonify(response_data), 500


@app.route('/api/portal/status', methods=['GET'])
def status():
    session_manager.update_activity()
    session_id = request.args.get('session_id')
    
    get_request_logger().log_request_info(
        username=g.forwarded_user,
        request_time=g.request_time,
        method='GET',
        path='/api/portal/status',
        data={'session_id': session_id},
        source='backend'
    )
    
    if not session_id:
        get_request_logger().log_request('GET', '/api/portal/status', None, 400)
        response_data = {'code': 400, 'message': '缺少session_id'}
        get_request_logger().log_to_file('GET', '/api/portal/status', {'session_id': session_id}, response_data)
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    
    if client and client.is_logged_in():
        status_data = client.get_status()
        get_request_logger().log_request('GET', '/api/portal/status', {'session_id': session_id}, 200)
        response_data = {
            'code': 200,
            'message': '已登录',
            'data': {
                'logged_in': True,
                'user_info': status_data['user_info'],
                'login_time': status_data['login_time'],
                'expires_at': status_data['expires_at'],
                'needs_relogin': status_data.get('needs_relogin', False),
                'relogin_reason': status_data.get('relogin_reason')
            }
        }
        get_request_logger().log_to_file('GET', '/api/portal/status', {'session_id': session_id}, response_data)
        return jsonify(response_data)
    else:
        get_request_logger().log_request('GET', '/api/portal/status', {'session_id': session_id}, 200)
        response_data = {
            'code': 200,
            'message': '未登录',
            'data': {
                'logged_in': False,
                'needs_relogin': True,
                'relogin_reason': '会话不存在或已过期'
            }
        }
        get_request_logger().log_to_file('GET', '/api/portal/status', {'session_id': session_id}, response_data)
        return jsonify(response_data)


@app.route('/api/portal/session/check', methods=['GET'])
def check_session_status():
    session_manager.update_activity()
    session_id = request.args.get('session_id')
    
    if not session_id:
        get_request_logger().log_request('GET', '/api/portal/session/check', None, 400)
        response_data = {'code': 400, 'message': '缺少session_id'}
        get_request_logger().log_to_file('GET', '/api/portal/session/check', {'session_id': session_id}, response_data)
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    
    if not client:
        get_request_logger().log_request('GET', '/api/portal/session/check', {'session_id': session_id}, 200)
        response_data = {
            'code': 200,
            'data': {
                'logged_in': False,
                'needs_relogin': True,
                'reason': '会话不存在或已过期'
            }
        }
        get_request_logger().log_to_file('GET', '/api/portal/session/check', {'session_id': session_id}, response_data)
        return jsonify(response_data)
    
    status = client.get_status()
    get_request_logger().log_request('GET', '/api/portal/session/check', {'session_id': session_id}, 200)
    response_data = {
        'code': 200,
        'data': {
            'logged_in': status['logged_in'],
            'needs_relogin': status.get('needs_relogin', False),
            'reason': status.get('relogin_reason'),
            'user_info': status['user_info']
        }
    }
    get_request_logger().log_to_file('GET', '/api/portal/session/check', {'session_id': session_id}, response_data)
    return jsonify(response_data)


@app.route('/api/portal/logout', methods=['POST'])
def logout():
    session_manager.update_activity()
    data = request.json or {}
    session_id = data.get('session_id')
    
    get_request_logger().log_request_info(
        username=g.forwarded_user,
        request_time=g.request_time,
        method='POST',
        path='/api/portal/logout',
        data={'session_id': session_id},
        source='backend'
    )
    
    if session_id:
        session_manager.remove_session(session_id)
    
    get_request_logger().log_request('POST', '/api/portal/logout', {'session_id': session_id}, 200)
    response_data = {'code': 200, 'message': '登出成功'}
    get_request_logger().log_to_file('POST', '/api/portal/logout', {'session_id': session_id}, response_data)
    return jsonify(response_data)


@app.route('/api/portal/keep-alive', methods=['POST'])
def keep_alive():
    session_manager.update_activity()
    data = request.json
    session_id = data.get('session_id') if data else None
    
    if not session_id:
        get_request_logger().log_request('POST', '/api/portal/keep-alive', None, 400)
        response_data = {'code': 400, 'message': '缺少session_id参数'}
        get_request_logger().log_to_file('POST', '/api/portal/keep-alive', {'session_id': session_id}, response_data)
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    if not client:
        get_request_logger().log_request('POST', '/api/portal/keep-alive', {'session_id': session_id}, 401)
        response_data = {'code': 401, 'message': '会话不存在或已过期', 'data': {'session_expired': True, 'need_relogin': True}}
        get_request_logger().log_to_file('POST', '/api/portal/keep-alive', {'session_id': session_id}, response_data)
        return jsonify(response_data), 401
    
    result = client.keep_alive()
    
    if result['success']:
        session_manager.update_timestamp(session_id)
        get_request_logger().log_request('POST', '/api/portal/keep-alive', {'session_id': session_id}, 200)
        response_data = {'code': 200, 'message': result['message'], 'data': {'session_expired': False, 'logged_in': True}}
        get_request_logger().log_to_file('POST', '/api/portal/keep-alive', {'session_id': session_id}, response_data)
        return jsonify(response_data)
    else:
        session_manager.remove_session(session_id)
        get_request_logger().log_request('POST', '/api/portal/keep-alive', {'session_id': session_id}, 500)
        response_data = {'code': 500, 'message': result['error'], 'data': {'session_expired': True, 'need_relogin': True}}
        get_request_logger().log_to_file('POST', '/api/portal/keep-alive', {'session_id': session_id}, response_data)
        return jsonify(response_data), 500


@app.route('/api/portal/sessions', methods=['GET'])
def get_all_sessions():
    sessions = session_manager.get_all_sessions()
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'sessions': sessions,
            'count': len(sessions)
        }
    })


@app.route('/api/portal/ai-audit/vehicle-images', methods=['POST'])
def ai_audit_vehicle_images():
    session_manager.update_activity()
    data = request.json
    
    if not data:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/vehicle-images', None, 400)
        response_data = {'code': 400, 'message': '请求体不能为空'}
        get_request_logger().log_to_file('POST', '/api/portal/ai-audit/vehicle-images', data, response_data)
        return jsonify(response_data), 400
    
    session_id = data.get('session_id')
    plate_number = data.get('plate_number')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    page = data.get('page', 0)
    page_size = data.get('page_size', 20)
    sort = data.get('sort', 'picTime DESC')
    
    if not all([session_id, plate_number, start_time, end_time]):
        get_request_logger().log_request('POST', '/api/portal/ai-audit/vehicle-images', {'session_id': session_id}, 400)
        response_data = {'code': 400, 'message': '缺少必要参数'}
        get_request_logger().log_to_file('POST', '/api/portal/ai-audit/vehicle-images', data, response_data)
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        get_request_logger().log_request('POST', '/api/portal/ai-audit/vehicle-images', {'session_id': session_id}, 401)
        response_data = {'code': 401, 'message': '未登录或会话已过期'}
        get_request_logger().log_to_file('POST', '/api/portal/ai-audit/vehicle-images', data, response_data)
        return jsonify(response_data), 401
    
    ai_client = AIAuditClient(client.access_token, client.source_ip)
    result = ai_client.query_vehicle_images(
        plate_number=plate_number,
        start_time=start_time,
        end_time=end_time,
        start=page,
        rows=page_size,
        sort=sort
    )
    
    if result['success']:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/vehicle-images', {'session_id': session_id}, 200)
        response_data = {'code': 200, 'message': 'success', 'data': result}
        get_request_logger().log_to_file('POST', '/api/portal/ai-audit/vehicle-images', data, response_data)
        return jsonify(response_data)
    else:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/vehicle-images', {'session_id': session_id}, 500)
        response_data = {'code': 500, 'message': result['error']}
        get_request_logger().log_to_file('POST', '/api/portal/ai-audit/vehicle-images', data, response_data)
        return jsonify(response_data), 500


@app.route('/api/portal/ai-audit/gantry-images', methods=['POST'])
def ai_audit_gantry_images():
    session_manager.update_activity()
    data = request.json
    
    if not data:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/gantry-images', None, 400)
        response_data = {'code': 400, 'message': '请求体不能为空'}
        get_request_logger().log_to_file('POST', '/api/portal/ai-audit/gantry-images', data, response_data)
        return jsonify(response_data), 400
    
    session_id = data.get('session_id')
    station_id = data.get('station_id')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    rows = data.get('rows', 20)
    start = data.get('start', 0)
    sort = data.get('sort', 'picTime DESC')
    
    if not all([session_id, station_id, start_time, end_time]):
        get_request_logger().log_request('POST', '/api/portal/ai-audit/gantry-images', {'session_id': session_id}, 400)
        response_data = {'code': 400, 'message': '缺少必要参数'}
        get_request_logger().log_to_file('POST', '/api/portal/ai-audit/gantry-images', data, response_data)
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        get_request_logger().log_request('POST', '/api/portal/ai-audit/gantry-images', {'session_id': session_id}, 401)
        response_data = {'code': 401, 'message': '未登录或会话已过期'}
        get_request_logger().log_to_file('POST', '/api/portal/ai-audit/gantry-images', data, response_data)
        return jsonify(response_data), 401
    
    ai_client = AIAuditClient(client.access_token, client.source_ip)
    result = ai_client.query_gantry_images(
        station_id=station_id,
        start_time=start_time,
        end_time=end_time,
        rows=rows,
        start=start,
        sort=sort
    )
    
    if result['success']:
        images = result.get('images', [])
        processed_images = []
        
        for img in images:
            big_positive_pic = img.get('bigPositivePic', '')
            if big_positive_pic and big_positive_pic.startswith('data:image'):
                big_positive_pic = big_positive_pic.replace('data:image/jpeg;base64,', '')
            
            processed_img = {
                'picTime': img.get('picTime', ''),
                'vehPlate': img.get('vehPlate', ''),
                'stationName': img.get('stationName', ''),
                'stationId': img.get('stationId', ''),
                'picturePath': img.get('picturePath', ''),
                'bigPositivePic': big_positive_pic,
                'vehPlateColor': img.get('vehPlateColor', ''),
                'picId': img.get('picId', '')
            }
            processed_images.append(processed_img)
        
        result['images'] = processed_images
        
        get_request_logger().log_request('POST', '/api/portal/ai-audit/gantry-images', {'session_id': session_id, 'station_id': station_id}, 200)
        response_data = {'code': 200, 'message': 'success', 'data': result}
        get_request_logger().log_to_file('POST', '/api/portal/ai-audit/gantry-images', data, response_data)
        return jsonify(response_data)
    else:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/gantry-images', {'session_id': session_id, 'station_id': station_id}, 500)
        response_data = {'code': 500, 'message': result['error']}
        get_request_logger().log_to_file('POST', '/api/portal/ai-audit/gantry-images', data, response_data)
        return jsonify(response_data), 500


@app.route('/api/portal/ai-audit/batch-query', methods=['POST'])
def ai_audit_batch_query():
    session_manager.update_activity()
    data = request.json
    
    if not data:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/batch-query', None, 400)
        response_data = {'code': 400, 'message': '请求体不能为空'}
        get_request_logger().log_to_file('POST', '/api/portal/ai-audit/batch-query', data, response_data)
        return jsonify(response_data), 400
    
    session_id = data.get('session_id')
    plate_number = data.get('plate_number')
    entry_time = data.get('entry_time')
    gate_time = data.get('gate_time')
    pass_id = data.get('pass_id')
    hours = data.get('hours', 5)
    
    if not all([session_id, plate_number, entry_time, gate_time]):
        get_request_logger().log_request('POST', '/api/portal/ai-audit/batch-query', {'session_id': session_id}, 400)
        response_data = {'code': 400, 'message': '缺少必要参数'}
        get_request_logger().log_to_file('POST', '/api/portal/ai-audit/batch-query', data, response_data)
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        get_request_logger().log_request('POST', '/api/portal/ai-audit/batch-query', {'session_id': session_id}, 401)
        response_data = {'code': 401, 'message': '未登录或会话已过期'}
        get_request_logger().log_to_file('POST', '/api/portal/ai-audit/batch-query', data, response_data)
        return jsonify(response_data), 401
    
    ai_client = AIAuditClient(client.access_token, client.source_ip)
    result = ai_client.batch_query_all(
        plate_number=plate_number,
        entry_time=entry_time,
        gate_time=gate_time,
        pass_id=pass_id,
        hours=hours
    )
    
    get_request_logger().log_request('POST', '/api/portal/ai-audit/batch-query', {'session_id': session_id}, 200)
    response_data = {'code': 200, 'message': 'success', 'data': result}
    get_request_logger().log_to_file('POST', '/api/portal/ai-audit/batch-query', data, response_data)
    return jsonify(response_data)


@app.route('/api/portal/ai-audit/gantry-trade', methods=['POST'])
def ai_audit_gantry_trade():
    session_manager.update_activity()
    data = request.json
    
    if not data:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/gantry-trade', None, 400)
        response_data = {'code': 400, 'message': '请求体不能为空'}
        return jsonify(response_data), 400
    
    session_id = data.get('session_id')
    query_value = data.get('query_value')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    
    if not all([session_id, query_value, start_time, end_time]):
        get_request_logger().log_request('POST', '/api/portal/ai-audit/gantry-trade', {'session_id': session_id}, 400)
        response_data = {'code': 400, 'message': '缺少必要参数'}
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        get_request_logger().log_request('POST', '/api/portal/ai-audit/gantry-trade', {'session_id': session_id}, 401)
        response_data = {'code': 401, 'message': '未登录或会话已过期'}
        return jsonify(response_data), 401
    
    ai_client = AIAuditClient(client.access_token, client.source_ip)
    result = ai_client.query_gantry_trade(
        query_value=query_value,
        start_time=start_time,
        end_time=end_time
    )
    
    if result['success']:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/gantry-trade', {'session_id': session_id}, 200)
        response_data = {'code': 200, 'message': 'success', 'data': result}
        return jsonify(response_data)
    else:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/gantry-trade', {'session_id': session_id}, 500)
        response_data = {'code': 500, 'message': result['error']}
        return jsonify(response_data), 500


@app.route('/api/portal/ai-audit/gantry-plate', methods=['POST'])
def ai_audit_gantry_plate():
    session_manager.update_activity()
    data = request.json
    
    if not data:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/gantry-plate', None, 400)
        response_data = {'code': 400, 'message': '请求体不能为空'}
        return jsonify(response_data), 400
    
    session_id = data.get('session_id')
    plate_number = data.get('plate_number')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    
    if not all([session_id, plate_number, start_time, end_time]):
        get_request_logger().log_request('POST', '/api/portal/ai-audit/gantry-plate', {'session_id': session_id}, 400)
        response_data = {'code': 400, 'message': '缺少必要参数'}
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        get_request_logger().log_request('POST', '/api/portal/ai-audit/gantry-plate', {'session_id': session_id}, 401)
        response_data = {'code': 401, 'message': '未登录或会话已过期'}
        return jsonify(response_data), 401
    
    ai_client = AIAuditClient(client.access_token, client.source_ip)
    result = ai_client.query_gantry_plate(
        plate_number=plate_number,
        start_time=start_time,
        end_time=end_time
    )
    
    if result['success']:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/gantry-plate', {'session_id': session_id}, 200)
        response_data = {'code': 200, 'message': 'success', 'data': result}
        return jsonify(response_data)
    else:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/gantry-plate', {'session_id': session_id}, 500)
        response_data = {'code': 500, 'message': result['error']}
        return jsonify(response_data), 500


@app.route('/api/portal/ai-audit/exit-trade', methods=['POST'])
def ai_audit_exit_trade():
    session_manager.update_activity()
    data = request.json
    
    if not data:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/exit-trade', None, 400)
        response_data = {'code': 400, 'message': '请求体不能为空'}
        return jsonify(response_data), 400
    
    session_id = data.get('session_id')
    query_value = data.get('query_value')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    trade_type = data.get('trade_type', 1)
    
    if not all([session_id, query_value, start_time, end_time]):
        get_request_logger().log_request('POST', '/api/portal/ai-audit/exit-trade', {'session_id': session_id}, 400)
        response_data = {'code': 400, 'message': '缺少必要参数'}
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        get_request_logger().log_request('POST', '/api/portal/ai-audit/exit-trade', {'session_id': session_id}, 401)
        response_data = {'code': 401, 'message': '未登录或会话已过期'}
        return jsonify(response_data), 401
    
    ai_client = AIAuditClient(client.access_token, client.source_ip)
    result = ai_client.query_exit_trade(
        query_value=query_value,
        start_time=start_time,
        end_time=end_time,
        trade_type=trade_type
    )
    
    if result['success']:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/exit-trade', {'session_id': session_id}, 200)
        response_data = {'code': 200, 'message': 'success', 'data': result}
        return jsonify(response_data)
    else:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/exit-trade', {'session_id': session_id}, 500)
        response_data = {'code': 500, 'message': result['error']}
        return jsonify(response_data), 500


@app.route('/api/portal/ai-audit/suspected-car', methods=['POST'])
def ai_audit_suspected_car():
    session_manager.update_activity()
    data = request.json
    
    if not data:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/suspected-car', None, 400)
        response_data = {'code': 400, 'message': '请求体不能为空'}
        return jsonify(response_data), 400
    
    session_id = data.get('session_id')
    vehicle_or_pass_id = data.get('vehicle_or_pass_id')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    
    if not all([session_id, vehicle_or_pass_id, start_time, end_time]):
        get_request_logger().log_request('POST', '/api/portal/ai-audit/suspected-car', {'session_id': session_id}, 400)
        response_data = {'code': 400, 'message': '缺少必要参数'}
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        get_request_logger().log_request('POST', '/api/portal/ai-audit/suspected-car', {'session_id': session_id}, 401)
        response_data = {'code': 401, 'message': '未登录或会话已过期'}
        return jsonify(response_data), 401
    
    ai_client = AIAuditClient(client.access_token, client.source_ip)
    result = ai_client.query_suspected_car(
        vehicle_or_pass_id=vehicle_or_pass_id,
        start_time=start_time,
        end_time=end_time
    )
    
    if result['success']:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/suspected-car', {'session_id': session_id}, 200)
        response_data = {'code': 200, 'message': 'success', 'data': result}
        return jsonify(response_data)
    else:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/suspected-car', {'session_id': session_id}, 500)
        response_data = {'code': 500, 'message': result['error']}
        return jsonify(response_data), 500


@app.route('/api/portal/ai-audit/audit-order', methods=['POST'])
def ai_audit_audit_order():
    session_manager.update_activity()
    data = request.json
    
    if not data:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/audit-order', None, 400)
        response_data = {'code': 400, 'message': '请求体不能为空'}
        return jsonify(response_data), 400
    
    session_id = data.get('session_id')
    vehicle_no = data.get('vehicle_no')
    
    if not all([session_id, vehicle_no]):
        get_request_logger().log_request('POST', '/api/portal/ai-audit/audit-order', {'session_id': session_id}, 400)
        response_data = {'code': 400, 'message': '缺少必要参数'}
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        get_request_logger().log_request('POST', '/api/portal/ai-audit/audit-order', {'session_id': session_id}, 401)
        response_data = {'code': 401, 'message': '未登录或会话已过期'}
        return jsonify(response_data), 401
    
    ai_client = AIAuditClient(client.access_token, client.source_ip)
    result = ai_client.query_audit_order(vehicle_no=vehicle_no)
    
    if result['success']:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/audit-order', {'session_id': session_id}, 200)
        response_data = {'code': 200, 'message': 'success', 'data': result}
        return jsonify(response_data)
    else:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/audit-order', {'session_id': session_id}, 500)
        response_data = {'code': 500, 'message': result['error']}
        return jsonify(response_data), 500


@app.route('/api/portal/captcha/ocr', methods=['POST'])
def captcha_ocr_recognize():
    """
    OCR识别验证码
    
    请求体:
    {
        "image": "base64编码的图片数据"
    }
    
    返回:
    {
        "code": 200,
        "message": "success",
        "data": {
            "text": "识别结果",
            "available": true
        }
    }
    """
    session_manager.update_activity()
    data = request.json
    
    if not data:
        get_request_logger().log_request('POST', '/api/portal/captcha/ocr', None, 400)
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400
    
    image_base64 = data.get('image')
    if not image_base64:
        get_request_logger().log_request('POST', '/api/portal/captcha/ocr', None, 400)
        return jsonify({'code': 400, 'message': '缺少图片数据'}), 400
    
    if not is_ocr_available():
        get_request_logger().log_request('POST', '/api/portal/captcha/ocr', None, 503)
        return jsonify({
            'code': 503,
            'message': 'OCR功能不可用，请安装ddddocr库',
            'data': {'available': False}
        }), 503
    
    result = captcha_ocr.recognize(image_base64)
    
    if result['success']:
        get_request_logger().log_request('POST', '/api/portal/captcha/ocr', None, 200)
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'text': result['text'],
                'available': True
            }
        })
    else:
        get_request_logger().log_request('POST', '/api/portal/captcha/ocr', None, 500)
        return jsonify({
            'code': 500,
            'message': result['error'],
            'data': {'available': True}
        }), 500


@app.route('/api/portal/captcha/ocr/status', methods=['GET'])
def captcha_ocr_status():
    """
    检查OCR功能状态
    """
    available = is_ocr_available()
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'available': available,
            'message': 'OCR功能可用' if available else 'OCR功能不可用，请安装ddddocr库'
        }
    })


@app.route('/api/portal/ai-audit/original-image', methods=['POST'])
def ai_audit_original_image():
    """
    获取高清原图
    
    请求体:
    {
        "session_id": "会话ID",
        "picture_path": "图片URL"
    }
    
    返回:
    {
        "code": 200,
        "message": "success",
        "data": {
            "image": "base64编码的图片数据",
            "content_type": "image/jpeg"
        }
    }
    """
    session_manager.update_activity()
    data = request.json
    
    if not data:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/original-image', None, 400)
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400
    
    session_id = data.get('session_id')
    picture_path = data.get('picture_path')
    
    if not all([session_id, picture_path]):
        get_request_logger().log_request('POST', '/api/portal/ai-audit/original-image', {'session_id': session_id}, 400)
        return jsonify({'code': 400, 'message': '缺少必要参数'}), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        get_request_logger().log_request('POST', '/api/portal/ai-audit/original-image', {'session_id': session_id}, 401)
        return jsonify({'code': 401, 'message': '未登录或会话已过期'}), 401
    
    import base64
    try:
        picture_url = picture_path.strip()
        if picture_url.startswith('`'):
            picture_url = picture_url.strip('`').strip()
        
        headers = {
            'Authorization': f'Bearer {client.access_token}',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'http://twaudit.hngsetc.com/aiAuditWeb/index.html'
        }
        
        response = client.session.get(picture_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            
            content_text = response.text.strip()
            if content_text.startswith('data:image'):
                image_data = content_text
                if ';' in content_text:
                    extracted_type = content_text.split(';')[0].replace('data:', '')
                    if extracted_type:
                        content_type = extracted_type
            else:
                image_data = base64.b64encode(response.content).decode('utf-8')
                image_data = f"data:{content_type.split(';')[0]};base64,{image_data}"
            
            get_request_logger().log_request('POST', '/api/portal/ai-audit/original-image', {'session_id': session_id}, 200)
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'image': image_data,
                    'content_type': content_type
                }
            })
        else:
            get_request_logger().log_request('POST', '/api/portal/ai-audit/original-image', {'session_id': session_id}, response.status_code)
            return jsonify({
                'code': response.status_code,
                'message': f'获取图片失败: HTTP {response.status_code}'
            }), response.status_code
            
    except Exception as e:
        logger.error(f"获取原图失败: {e}")
        get_request_logger().log_request('POST', '/api/portal/ai-audit/original-image', {'session_id': session_id}, 500)
        return jsonify({'code': 500, 'message': f'获取原图失败: {str(e)}'}), 500


@app.route('/api/portal/ai-audit/select-images', methods=['POST'])
def ai_audit_select_images():
    """
    根据门架ID筛选图片
    
    请求体:
    {
        "images": [...],
        "gantry_ids": ["门架ID1", "门架ID2"]
    }
    
    返回:
    {
        "code": 200,
        "message": "success",
        "data": {
            "first_gantry": {...},
            "last_gantry": {...}
        }
    }
    """
    session_manager.update_activity()
    data = request.json
    
    if not data:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/select-images', None, 400)
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400
    
    images = data.get('images', [])
    gantry_ids = data.get('gantry_ids', [])
    
    if not images:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/select-images', None, 400)
        return jsonify({'code': 400, 'message': '缺少图片列表'}), 400
    
    if not gantry_ids:
        get_request_logger().log_request('POST', '/api/portal/ai-audit/select-images', None, 400)
        return jsonify({'code': 400, 'message': '缺少门架ID列表'}), 400
    
    try:
        selected = {
            'first_gantry': None,
            'last_gantry': None
        }
        
        first_gantry_id = gantry_ids[0] if gantry_ids else None
        last_gantry_id = gantry_ids[-1] if len(gantry_ids) > 1 else first_gantry_id
        
        for image in images:
            station_id = image.get('stationId', '')
            
            if first_gantry_id and station_id.startswith(first_gantry_id[:16]):
                if selected['first_gantry'] is None:
                    selected['first_gantry'] = image
            
            if last_gantry_id and station_id.startswith(last_gantry_id[:16]):
                selected['last_gantry'] = image
        
        get_request_logger().log_request('POST', '/api/portal/ai-audit/select-images', None, 200)
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': selected
        })
        
    except Exception as e:
        logger.error(f"图片筛选失败: {e}")
        get_request_logger().log_request('POST', '/api/portal/ai-audit/select-images', None, 500)
        return jsonify({'code': 500, 'message': f'图片筛选失败: {str(e)}'}), 500


@app.route('/api/portal/ai-audit/branch-centers', methods=['POST'])
def ai_audit_branch_centers():
    """
    获取分中心列表
    
    请求体:
    {
        "session_id": "会话ID"
    }
    
    返回:
    {
        "code": 200,
        "message": "success",
        "data": [...]
    }
    """
    session_manager.update_activity()
    data = request.json or {}
    session_id = data.get('session_id')
    
    branch_centers = [
        {"center_no": "001", "center_name": "长沙分中心"},
        {"center_no": "002", "center_name": "株洲分中心"},
        {"center_no": "003", "center_name": "湘潭分中心"},
        {"center_no": "004", "center_name": "衡阳分中心"},
        {"center_no": "005", "center_name": "邵阳分中心"},
        {"center_no": "006", "center_name": "岳阳分中心"},
        {"center_no": "007", "center_name": "常德分中心"},
        {"center_no": "008", "center_name": "张家界分中心"},
        {"center_no": "009", "center_name": "益阳分中心"},
        {"center_no": "010", "center_name": "郴州分中心"},
        {"center_no": "011", "center_name": "永州分中心"},
        {"center_no": "012", "center_name": "怀化分中心"},
        {"center_no": "013", "center_name": "娄底分中心"},
        {"center_no": "014", "center_name": "湘西分中心"}
    ]
    
    get_request_logger().log_request('POST', '/api/portal/ai-audit/branch-centers', {'session_id': session_id}, 200)
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': branch_centers
    })


@app.route('/api/portal/ai-audit/road-sections', methods=['POST'])
def ai_audit_road_sections():
    """
    获取路段列表
    
    请求体:
    {
        "session_id": "会话ID",
        "center_no": "分中心编号"
    }
    
    返回:
    {
        "code": 200,
        "message": "success",
        "data": [...]
    }
    """
    session_manager.update_activity()
    data = request.json or {}
    session_id = data.get('session_id')
    center_no = data.get('center_no')
    
    road_sections = [
        {"road_section_no": f"{center_no}001", "road_section_name": f"{center_no}号路段1"},
        {"road_section_no": f"{center_no}002", "road_section_name": f"{center_no}号路段2"},
        {"road_section_no": f"{center_no}003", "road_section_name": f"{center_no}号路段3"}
    ]
    
    get_request_logger().log_request('POST', '/api/portal/ai-audit/road-sections', {'session_id': session_id, 'center_no': center_no}, 200)
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': road_sections
    })


@app.route('/api/portal/ai-audit/gantry-list', methods=['POST'])
def ai_audit_gantry_list():
    """
    获取门架列表
    
    请求体:
    {
        "session_id": "会话ID",
        "road_section_no": "路段编号"
    }
    
    返回:
    {
        "code": 200,
        "message": "success",
        "data": [...]
    }
    """
    session_manager.update_activity()
    data = request.json or {}
    session_id = data.get('session_id')
    road_section_no = data.get('road_section_no')
    
    gantry_list = [
        {"gantry_id": f"{road_section_no}001", "gantry_name": f"{road_section_no}号门架1"},
        {"gantry_id": f"{road_section_no}002", "gantry_name": f"{road_section_no}号门架2"},
        {"gantry_id": f"{road_section_no}003", "gantry_name": f"{road_section_no}号门架3"}
    ]
    
    get_request_logger().log_request('POST', '/api/portal/ai-audit/gantry-list', {'session_id': session_id, 'road_section_no': road_section_no}, 200)
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': gantry_list
    })


@app.route('/api/portal/order-detail', methods=['GET'])
def ai_audit_order_detail():
    """
    获取工单详情

    请求参数:
        session_id: 会话ID
        order_id: 工单编号

    返回:
    {
        "code": 200,
        "message": "success",
        "data": {
            "labelVo": {...},
            "enData": {...},
            "exData": {...}
        }
    }
    """
    session_manager.update_activity()

    session_id = request.args.get('session_id')
    order_id = request.args.get('order_id')

    if not all([session_id, order_id]):
        get_request_logger().log_request('GET', '/api/portal/order-detail',
                                        {'session_id': session_id, 'order_id': order_id}, 400)
        return jsonify({'code': 400, 'message': '缺少必要参数: session_id 或 order_id'}), 400

    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        get_request_logger().log_request('GET', '/api/portal/order-detail',
                                        {'session_id': session_id}, 401)
        return jsonify({'code': 401, 'message': '未登录或会话已过期'}), 401

    ai_client = AIAuditClient(client.access_token, client.source_ip)
    result = ai_client.query_order_detail(order_id=order_id)

    if result['success']:
        get_request_logger().log_request('GET', '/api/portal/order-detail',
                                        {'session_id': session_id, 'order_id': order_id}, 200)
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result['data']
        })
    else:
        get_request_logger().log_request('GET', '/api/portal/order-detail',
                                        {'session_id': session_id, 'order_id': order_id}, 500)
        return jsonify({'code': 500, 'message': result['error']}), 500


if __name__ == '__main__':
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    host = config.GUI_HOST
    port = config.GUI_PORT
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    
    logger.info(f"Starting Flask server on {host}:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)
