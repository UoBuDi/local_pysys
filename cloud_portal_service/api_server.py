import logging
import uuid
import json
import time
import os
import threading
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from portal_client import PortalClient
from config import config, get_base_path, Limits
from ai_audit_client import AIAuditClient
from captcha_ocr import captcha_ocr, is_ocr_available
from datetime import datetime
from collections import deque
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

app.config['JSON_AS_ASCII'] = False

@app.before_request
def before_request():
    g.forwarded_user = request.headers.get('X-Forwarded-User', '')
    g.request_time = datetime.now().isoformat()

    from session_manager import session_manager
    session_manager.update_activity()


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
    
    def set_latest_response(self, response: Dict[str, Any]) -> None:
        with self._log_lock:
            self._latest_response = response
    
    def get_latest_response(self) -> Optional[Dict[str, Any]]:
        with self._log_lock:
            return self._latest_response
    
    def get_request_logs(self) -> List[Dict[str, Any]]:
        with self._log_lock:
            return list(self._request_log)


def get_request_logger() -> RequestLogger:
    return RequestLogger()


def _create_temp_client(source_ip: Optional[str] = None) -> PortalClient:
    """创建临时的PortalClient实例（无状态）- 用于需要session的场景如登录、验证码"""
    return PortalClient(source_ip)


def _create_temp_ai_client(access_token: str, source_ip: Optional[str] = None) -> AIAuditClient:
    """创建临时的AIAuditClient实例（无状态）- 用于AI审计业务查询"""
    return AIAuditClient(access_token, source_ip)


@app.route('/api/portal/health', methods=['GET'])
def health_check():
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
    start_time = time.time()

    get_request_logger().log_request_info(
        username=g.forwarded_user,
        request_time=g.request_time,
        method='GET',
        path='/api/portal/captcha',
        data=None,
        source='backend'
    )

    client = _create_temp_client()

    try:
        result = client.get_captcha()
        elapsed = time.time() - start_time

        if result['success']:
            captcha_uuid = result['uuid']

            response_data = {
                'code': 200,
                'message': 'success',
                'data': {
                    'img': result['img'],
                    'uuid': captcha_uuid
                }
            }
            get_request_logger().set_latest_response(response_data)
            get_request_logger().log_to_file('GET', '/api/portal/captcha', {'uuid': captcha_uuid}, response_data)
            return jsonify(response_data)
        else:
            response_data = {'code': 500, 'message': result['error']}
            get_request_logger().log_to_file('GET', '/api/portal/captcha', None, response_data)
            return jsonify(response_data), 500
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[验证码] 异常 - 错误: {e}, 耗时: {elapsed:.2f}s", exc_info=True)
        response_data = {'code': 500, 'message': f'获取验证码异常: {str(e)}'}
        get_request_logger().log_to_file('GET', '/api/portal/captcha', None, response_data)
        return jsonify(response_data), 500


@app.route('/api/portal/login', methods=['POST'])
def login():
    data = request.json

    get_request_logger().log_request_info(
        username=g.forwarded_user,
        request_time=g.request_time,
        method='POST',
        path='/api/portal/login',
        data={'uuid': data.get('uuid') if data else None},
        source='backend'
    )

    if not data:
        response_data = {'code': 400, 'message': '请求体不能为空'}
        return jsonify(response_data), 400

    uuid_str = data.get('uuid')
    username = data.get('username')
    password = data.get('password')
    captcha = data.get('captcha')

    if not all([uuid_str, username, password, captcha]):
        response_data = {'code': 400, 'message': '缺少必要参数'}
        return jsonify(response_data), 400

    client = _create_temp_client()
    result = client.login(username, password, captcha, uuid_str)

    if result['success']:
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
        get_request_logger().set_latest_response(response_data)
        get_request_logger().log_to_file('POST', '/api/portal/login', data, response_data)
        return jsonify(response_data)
    else:
        response_data = {'code': 401, 'message': result['error']}
        get_request_logger().log_to_file('POST', '/api/portal/login', data, response_data)
        return jsonify(response_data), 401


@app.route('/api/portal/query', methods=['POST'])
def query():
    data = request.json

    get_request_logger().log_request_info(
        username=g.forwarded_user,
        request_time=g.request_time,
        method='POST',
        path='/api/portal/query',
        data={'has_access_token': bool(data.get('access_token')) if data else False},
        source='backend'
    )

    if not data:
        response_data = {'code': 400, 'message': '请求体不能为空'}
        return jsonify(response_data), 400

    access_token = data.get('access_token', '')
    query_params = data.get('query_params')

    if not query_params:
        response_data = {'code': 400, 'message': '缺少必要参数: query_params'}
        return jsonify(response_data), 400

    client = _create_temp_client()
    client.access_token = access_token

    result = client.query_pass_data(query_params)

    if result['success']:
        response_data = {'code': 200, 'message': 'success', 'data': result['data']}
        get_request_logger().set_latest_response(response_data)
        get_request_logger().log_to_file('POST', '/api/portal/query', {'params': list(query_params.keys()) if isinstance(query_params, dict) else 'provided'}, response_data)
        return jsonify(response_data)
    else:
        response_data = {'code': 500, 'message': result['error']}
        get_request_logger().log_to_file('POST', '/api/portal/query', None, response_data)
        return jsonify(response_data), 500


@app.route('/api/portal/status', methods=['GET'])
def status():
    access_token = request.args.get('access_token')

    get_request_logger().log_request_info(
        username=g.forwarded_user,
        request_time=g.request_time,
        method='GET',
        path='/api/portal/status',
        data={'has_access_token': bool(access_token)},
        source='backend'
    )

    if not access_token:
        response_data = {'code': 200, 'message': '未登录', 'data': {'logged_in': False}}
        return jsonify(response_data)

    from portal_client import parse_jwt_expiration
    import json as _json
    import base64 as _base64

    try:
        parts = access_token.split('.')
        payload = parts[1] + '=' * (4 - len(parts[1]) % 4)
        decoded = _base64.urlsafe_b64decode(payload)
        token_data = _json.loads(decoded)

        exp = token_data.get('exp')
        is_valid = exp and time.time() < exp

        if is_valid:
            response_data = {
                'code': 200,
                'message': '已登录',
                'data': {
                    'logged_in': True,
                    'expires_at': exp,
                    'token_valid': True
                }
            }
        else:
            response_data = {
                'code': 200,
                'message': 'Token已过期',
                'data': {
                    'logged_in': False,
                    'needs_relogin': True,
                    'reason': 'token_expired'
                }
            }

        get_request_logger().log_to_file('GET', '/api/portal/status', {'token_valid': is_valid}, response_data)
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"[status] 解析Token失败: {e}")
        response_data = {
            'code': 200,
            'message': '无效的Token格式',
            'data': {
                'logged_in': False,
                'needs_relogin': True,
                'reason': 'invalid_token_format'
            }
        }
        get_request_logger().log_to_file('GET', '/api/portal/status', None, response_data)
        return jsonify(response_data)


@app.route('/api/portal/session/check', methods=['GET'])
def check_session_status():
    access_token = request.args.get('access_token')

    if not access_token:
        response_data = {
            'code': 200,
            'data': {
                'logged_in': False,
                'needs_relogin': True,
                'reason': '未提供access_token'
            }
        }
        return jsonify(response_data)

    from portal_client import parse_jwt_expiration
    import json as _json
    import base64 as _base64

    try:
        parts = access_token.split('.')
        payload = parts[1] + '=' * (4 - len(parts[1]) % 4)
        decoded = _base64.urlsafe_b64decode(payload)
        token_data = _json.loads(decoded)

        exp = token_data.get('exp')
        is_valid = exp and time.time() < exp

        response_data = {
            'code': 200,
            'data': {
                'logged_in': is_valid,
                'needs_relogin': not is_valid,
                'reason': None if is_valid else 'token_expired_or_invalid'
            }
        }
    except Exception as e:
        response_data = {
            'code': 200,
            'data': {
                'logged_in': False,
                'needs_relogin': True,
                'reason': str(e)
            }
        }

    get_request_logger().log_to_file('GET', '/api/portal/session/check', None, response_data)
    return jsonify(response_data)


@app.route('/api/portal/logout', methods=['POST'])
def logout():
    data = request.json or {}

    get_request_logger().log_request_info(
        username=g.forwarded_user,
        request_time=g.request_time,
        method='POST',
        path='/api/portal/logout',
        data=None,
        source='backend'
    )

    response_data = {'code': 200, 'message': '登出成功（请在调用方清除本地Token）'}
    get_request_logger().log_to_file('POST', '/api/portal/logout', None, response_data)
    return jsonify(response_data)


@app.route('/api/portal/keep-alive', methods=['POST'])
def keep_alive():
    data = request.json
    access_token = data.get('access_token') if data else None

    if not access_token:
        response_data = {'code': 400, 'message': '缺少access_token参数'}
        return jsonify(response_data), 400

    from portal_client import parse_jwt_expiration

    exp = parse_jwt_expiration(access_token)

    if exp and time.time() < exp - 300:
        logger.info("[保活] Token有效，剩余时间: %d秒", int(exp - time.time()))
        response_data = {
            'code': 200,
            'message': 'Token有效',
            'data': {
                'valid': True,
                'expires_at': exp,
                'remaining_seconds': int(exp - time.time())
            }
        }
    else:
        reason = 'token_expired' if exp else 'invalid_format'
        logger.warning("[保活] Token无效: %s", reason)
        response_data = {
            'code': 200,
            'message': 'Token即将过期或已失效',
            'data': {
                'valid': False,
                'expires_at': exp,
                'reason': reason
            }
        }

    get_request_logger().log_to_file('POST', '/api/portal/keep-alive', {'token_valid': response_data['data']['valid']}, response_data)
    return jsonify(response_data)


@app.route('/api/portal/sessions', methods=['GET'])
def get_all_sessions():
    return jsonify({
        'code': 200,
        'message': 'GUI服务运行在无状态模式',
        'data': {
            'mode': 'stateless',
            'active_sessions': [],
            'count': 0,
            'note': '会话管理已移至后端数据库，v2.1.0版本已移除服务端会话状态'
        }
    })


def _get_ai_client_from_token(access_token: str) -> Optional[AIAuditClient]:
    """根据access_token创建临时的AIAuditClient实例"""
    if not access_token:
        return None
    return _create_temp_ai_client(access_token)


@app.route('/api/portal/ai-audit/vehicle-images', methods=['POST'])
def ai_audit_vehicle_images():
    data = request.json

    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    plate_number = data.get('plate_number')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    page = data.get('page', 0)
    page_size = data.get('page_size', 20)
    sort = data.get('sort', 'picTime DESC')

    if not all([plate_number, start_time, end_time]):
        return jsonify({'code': 400, 'message': '缺少必要参数: plate_number, start_time, end_time'}), 400

    access_token = data.get('access_token', '')
    ai_client = _create_temp_ai_client(access_token)

    result = ai_client.query_vehicle_images(
        plate_number=plate_number,
        start_time=start_time,
        end_time=end_time,
        start=page,
        rows=page_size,
        sort=sort
    )

    if result['success']:
        response_data = {'code': 200, 'message': 'success', 'data': result}
        get_request_logger().set_latest_response(response_data)
        return jsonify(response_data)
    else:
        return jsonify({'code': 500, 'message': result['error']}), 500


@app.route('/api/portal/ai-audit/gantry-images', methods=['POST'])
def ai_audit_gantry_images():
    data = request.json

    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    station_id = data.get('station_id')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    rows = data.get('rows', 20)
    start_idx = data.get('start', 0)
    sort = data.get('sort', 'picTime DESC')

    if not all([station_id, start_time, end_time]):
        return jsonify({'code': 400, 'message': '缺少必要参数: station_id, start_time, end_time'}), 400

    access_token = data.get('access_token', '')
    ai_client = _create_temp_ai_client(access_token)

    result = ai_client.query_gantry_images(
        station_id=station_id,
        start_time=start_time,
        end_time=end_time,
        rows=rows,
        start=start_idx,
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

        response_data = {'code': 200, 'message': 'success', 'data': result}
        get_request_logger().set_latest_response(response_data)
        return jsonify(response_data)
    else:
        return jsonify({'code': 500, 'message': result['error']}), 500


@app.route('/api/portal/ai-audit/batch-query', methods=['POST'])
def ai_audit_batch_query():
    data = request.json

    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    plate_number = data.get('plate_number')
    entry_time = data.get('entry_time')
    gate_time = data.get('gate_time')
    pass_id = data.get('pass_id')
    hours = data.get('hours', 5)

    if not all([plate_number, entry_time, gate_time]):
        return jsonify({'code': 400, 'message': '缺少必要参数: plate_number, entry_time, gate_time'}), 400

    access_token = data.get('access_token', '')
    ai_client = _create_temp_ai_client(access_token)

    try:
        result = ai_client.batch_query_all(
            plate_number=plate_number,
            entry_time=entry_time,
            gate_time=gate_time,
            pass_id=pass_id,
            hours=hours
        )

        response_data = {'code': 200, 'message': 'success', 'data': result}
        get_request_logger().set_latest_response(response_data)
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"[batch-query] 执行失败: {e}", exc_info=True)
        return jsonify({'code': 500, 'message': f'查询失败: {str(e)}'}), 500


@app.route('/api/portal/ai-audit/gantry-trade', methods=['POST'])
def ai_audit_gantry_trade():
    data = request.json

    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    query_value = data.get('query_value')
    start_time = data.get('start_time')
    end_time = data.get('end_time')

    if not all([query_value, start_time, end_time]):
        return jsonify({'code': 400, 'message': '缺少必要参数: query_value, start_time, end_time'}), 400

    access_token = data.get('access_token', '')
    ai_client = _create_temp_ai_client(access_token)

    result = ai_client.query_gantry_trade(
        query_value=query_value,
        start_time=start_time,
        end_time=end_time
    )

    if result['success']:
        response_data = {'code': 200, 'message': 'success', 'data': result}
        get_request_logger().set_latest_response(response_data)
        return jsonify(response_data)
    else:
        return jsonify({'code': 500, 'message': result['error']}), 500


@app.route('/api/portal/ai-audit/gantry-plate', methods=['POST'])
def ai_audit_gantry_plate():
    data = request.json

    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    plate_number = data.get('plate_number')
    start_time = data.get('start_time')
    end_time = data.get('end_time')

    if not all([plate_number, start_time, end_time]):
        return jsonify({'code': 400, 'message': '缺少必要参数: plate_number, start_time, end_time'}), 400

    access_token = data.get('access_token', '')
    ai_client = _create_temp_ai_client(access_token)

    result = ai_client.query_gantry_plate(
        plate_number=plate_number,
        start_time=start_time,
        end_time=end_time
    )

    if result['success']:
        response_data = {'code': 200, 'message': 'success', 'data': result}
        get_request_logger().set_latest_response(response_data)
        return jsonify(response_data)
    else:
        return jsonify({'code': 500, 'message': result['error']}), 500


@app.route('/api/portal/ai-audit/exit-trade', methods=['POST'])
def ai_audit_exit_trade():
    data = request.json

    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    query_value = data.get('query_value')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    trade_type = data.get('trade_type', 1)

    if not all([query_value, start_time, end_time]):
        return jsonify({'code': 400, 'message': '缺少必要参数: query_value, start_time, end_time'}), 400

    access_token = data.get('access_token', '')
    ai_client = _create_temp_ai_client(access_token)

    result = ai_client.query_exit_trade(
        query_value=query_value,
        start_time=start_time,
        end_time=end_time,
        trade_type=trade_type
    )

    if result['success']:
        response_data = {'code': 200, 'message': 'success', 'data': result}
        get_request_logger().set_latest_response(response_data)
        return jsonify(response_data)
    else:
        return jsonify({'code': 500, 'message': result['error']}), 500


@app.route('/api/portal/ai-audit/suspected-car', methods=['POST'])
def ai_audit_suspected_car():
    data = request.json

    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    vehicle_or_pass_id = data.get('vehicle_or_pass_id')
    start_time = data.get('start_time')
    end_time = data.get('end_time')

    if not all([vehicle_or_pass_id, start_time, end_time]):
        return jsonify({'code': 400, 'message': '缺少必要参数: vehicle_or_pass_id, start_time, end_time'}), 400

    access_token = data.get('access_token', '')
    ai_client = _create_temp_ai_client(access_token)

    result = ai_client.query_suspected_car(
        vehicle_or_pass_id=vehicle_or_pass_id,
        start_time=start_time,
        end_time=end_time
    )

    if result['success']:
        response_data = {'code': 200, 'message': 'success', 'data': result}
        get_request_logger().set_latest_response(response_data)
        return jsonify(response_data)
    else:
        return jsonify({'code': 500, 'message': result['error']}), 500


@app.route('/api/portal/ai-audit/audit-order', methods=['POST'])
def ai_audit_audit_order():
    data = request.json

    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    vehicle_no = data.get('vehicle_no')

    if not vehicle_no:
        return jsonify({'code': 400, 'message': '缺少必要参数: vehicle_no'}), 400

    access_token = data.get('access_token', '')
    ai_client = _create_temp_ai_client(access_token)

    result = ai_client.query_audit_order(vehicle_no=vehicle_no)

    if result['success']:
        response_data = {'code': 200, 'message': 'success', 'data': result}
        get_request_logger().set_latest_response(response_data)
        return jsonify(response_data)
    else:
        return jsonify({'code': 500, 'message': result['error']}), 500


@app.route('/api/portal/captcha/ocr', methods=['POST'])
def captcha_ocr_recognize():
    data = request.json
    
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400
    
    image_base64 = data.get('image')
    if not image_base64:
        return jsonify({'code': 400, 'message': '缺少图片数据'}), 400
    
    if not is_ocr_available():
        return jsonify({
            'code': 503,
            'message': 'OCR功能不可用，请安装ddddocr库',
            'data': {'available': False}
        }), 503
    
    result = captcha_ocr.recognize(image_base64)
    
    if result['success']:
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'text': result['text'],
                'available': True
            }
        })
    else:
        return jsonify({
            'code': 500,
            'message': result['error'],
            'data': {'available': True}
        }), 500


@app.route('/api/portal/captcha/ocr/status', methods=['GET'])
def captcha_ocr_status():
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
    data = request.json

    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    picture_path = data.get('picture_path')

    if not picture_path:
        return jsonify({'code': 400, 'message': '缺少必要参数: picture_path'}), 400

    access_token = data.get('access_token', '')

    client = _create_temp_client()
    client.access_token = access_token

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

            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'image': image_data,
                    'content_type': content_type
                }
            })
        else:
            return jsonify({
                'code': response.status_code,
                'message': f'获取图片失败: HTTP {response.status_code}'
            }), response.status_code

    except Exception as e:
        logger.error(f"获取原图失败: {e}")
        return jsonify({'code': 500, 'message': f'获取原图失败: {str(e)}'}), 500


@app.route('/api/portal/ai-audit/select-images', methods=['POST'])
def ai_audit_select_images():
    data = request.json
    
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400
    
    images = data.get('images', [])
    gantry_ids = data.get('gantry_ids', [])
    
    if not images:
        return jsonify({'code': 400, 'message': '缺少图片列表'}), 400
    
    if not gantry_ids:
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
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': selected
        })
        
    except Exception as e:
        logger.error(f"图片筛选失败: {e}")
        return jsonify({'code': 500, 'message': f'图片筛选失败: {str(e)}'}), 500


@app.route('/api/portal/ai-audit/branch-centers', methods=['POST'])
def ai_audit_branch_centers():
    data = request.json or {}
    
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
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': branch_centers
    })


@app.route('/api/portal/ai-audit/road-sections', methods=['POST'])
def ai_audit_road_sections():
    data = request.json or {}
    center_no = data.get('center_no', '001')
    
    road_sections = [
        {"road_section_no": f"{center_no}001", "road_section_name": f"{center_no}号路段1"},
        {"road_section_no": f"{center_no}002", "road_section_name": f"{center_no}号路段2"},
        {"road_section_no": f"{center_no}003", "road_section_name": f"{center_no}号路段3"}
    ]
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': road_sections
    })


@app.route('/api/portal/ai-audit/gantry-list', methods=['POST'])
def ai_audit_gantry_list():
    data = request.json or {}
    road_section_no = data.get('road_section_no', '001001')
    
    gantry_list = [
        {"gantry_id": f"{road_section_no}001", "gantry_name": f"{road_section_no}号门架1"},
        {"gantry_id": f"{road_section_no}002", "gantry_name": f"{road_section_no}号门架2"},
        {"gantry_id": f"{road_section_no}003", "gantry_name": f"{road_section_no}号门架3"}
    ]
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': gantry_list
    })


@app.route('/api/portal/order-detail', methods=['GET'])
def ai_audit_order_detail():
    access_token = request.args.get('access_token', '')
    order_id = request.args.get('order_id')

    if not order_id:
        return jsonify({'code': 400, 'message': '缺少必要参数: order_id'}), 400

    ai_client = _create_temp_ai_client(access_token)

    result = ai_client.query_order_detail(order_id=order_id)

    if result['success']:
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result['data']
        })
    else:
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

    logger.info(f"Starting Flask server on {host}:{port} (v2.1.0 Stateless Mode)")
    logger.info("GUI服务已切换至无状态模式 - 所有业务接口使用access_token认证")
    logger.info("会话管理已移除 - Token由调用方管理")

    app.run(host=host, port=port, debug=False, threaded=True)
