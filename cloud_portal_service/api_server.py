import logging
import uuid
import base64
import json
import time
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from session_manager import session_manager
from config import config, get_base_path
from ai_audit_client import AIAuditClient
from datetime import datetime
from collections import deque
from network_utils import create_portal_session, restore_create_connection

logger = logging.getLogger(__name__)

request_log = deque(maxlen=100)
latest_response_data = None

def add_request_log(method, path, params=None, response_code=None):
    log_entry = {
        'time': datetime.now().strftime('%H:%M:%S'),
        'method': method,
        'path': path,
        'params': params,
        'response_code': response_code
    }
    request_log.append(log_entry)
    logger.info(f"请求: {method} {path} - {response_code}")

def log_request_to_file(method, path, data=None, response=None):
    try:
        log_dir = get_base_path()
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'data.log')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        log_entry = {
            'timestamp': timestamp,
            'type': 'request',
            'method': method,
            'path': path,
            'data': data
        }
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        if response is not None:
            response_entry = {
                'timestamp': timestamp,
                'type': 'response',
                'method': method,
                'path': path,
                'data': response
            }
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(response_entry, ensure_ascii=False) + '\n')
    except Exception as e:
        logger.error(f"写入请求日志失败: {e}")

def get_request_logs():
    return list(request_log)

def update_latest_response(response_data):
    global latest_response_data
    latest_response_data = response_data

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

@app.route('/api/portal/health', methods=['GET'])
def health_check():
    add_request_log('GET', '/api/portal/health', response_code=200)
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'status': 'healthy',
            'service': 'cloud-portal-service',
            'version': '1.0.0'
        }
    })

@app.route('/api/portal/request-logs', methods=['GET'])
def get_logs():
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': get_request_logs()
    })

@app.route('/api/portal/latest-response', methods=['GET'])
def get_latest_response():
    global latest_response_data
    if latest_response_data:
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': latest_response_data
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
    
    logger.info(f"[验证码] 请求开始 - session_id: {session_id}")
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
            add_request_log('GET', '/api/portal/captcha', {'session_id': session_id}, 200)
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
            log_request_to_file('GET', '/api/portal/captcha', {'session_id': session_id}, response_data)
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
            add_request_log('GET', '/api/portal/captcha', {'session_id': session_id}, 500)
            logger.error(f"[验证码] 失败 - 错误: {result.get('error')}, 总耗时: {elapsed:.2f}s")
            response_data = {
                'code': 500,
                'message': result['error']
            }
            log_request_to_file('GET', '/api/portal/captcha', {'session_id': session_id}, response_data)
            return jsonify(response_data), 500
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[验证码] 异常 - 错误: {e}, 总耗时: {elapsed:.2f}s", exc_info=True)
        add_request_log('GET', '/api/portal/captcha', {'session_id': session_id}, 500)
        response_data = {
            'code': 500,
            'message': f'获取验证码异常: {str(e)}'
        }
        log_request_to_file('GET', '/api/portal/captcha', {'session_id': session_id}, response_data)
        return jsonify(response_data), 500

@app.route('/api/portal/login', methods=['POST'])
def login():
    session_manager.update_activity()
    data = request.json
    
    if not data:
        add_request_log('POST', '/api/portal/login', None, 400)
        response_data = {'code': 400, 'message': '请求体不能为空'}
        log_request_to_file('POST', '/api/portal/login', data, response_data)
        return jsonify(response_data), 400
    
    session_id = data.get('session_id')
    username = data.get('username')
    password = data.get('password')
    captcha = data.get('captcha')
    uuid_str = data.get('uuid')
    
    if not all([session_id, username, password, captcha, uuid_str]):
        add_request_log('POST', '/api/portal/login', {'session_id': session_id}, 400)
        response_data = {'code': 400, 'message': '缺少必要参数'}
        log_request_to_file('POST', '/api/portal/login', data, response_data)
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    if not client:
        add_request_log('POST', '/api/portal/login', {'session_id': session_id}, 401)
        response_data = {'code': 401, 'message': '会话已过期，请刷新验证码'}
        log_request_to_file('POST', '/api/portal/login', data, response_data)
        return jsonify(response_data), 401
    
    result = client.login(username, password, captcha, uuid_str)
    
    if result['success']:
        session_manager.update_timestamp(session_id)
        add_request_log('POST', '/api/portal/login', {'session_id': session_id, 'username': username}, 200)
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
        log_request_to_file('POST', '/api/portal/login', data, response_data)
        return jsonify(response_data)
    else:
        add_request_log('POST', '/api/portal/login', {'session_id': session_id, 'username': username}, 401)
        response_data = {'code': 401, 'message': result['error']}
        log_request_to_file('POST', '/api/portal/login', data, response_data)
        return jsonify(response_data), 401

@app.route('/api/portal/query', methods=['POST'])
def query():
    session_manager.update_activity()
    data = request.json
    
    if not data:
        add_request_log('POST', '/api/portal/query', None, 400)
        response_data = {'code': 400, 'message': '请求体不能为空'}
        log_request_to_file('POST', '/api/portal/query', data, response_data)
        return jsonify(response_data), 400
    
    session_id = data.get('session_id')
    query_params = data.get('query_params')
    
    if not session_id:
        add_request_log('POST', '/api/portal/query', None, 400)
        response_data = {'code': 400, 'message': '缺少session_id'}
        log_request_to_file('POST', '/api/portal/query', data, response_data)
        return jsonify(response_data), 400
    
    if not query_params:
        add_request_log('POST', '/api/portal/query', {'session_id': session_id}, 400)
        response_data = {'code': 400, 'message': '缺少查询参数'}
        log_request_to_file('POST', '/api/portal/query', data, response_data)
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    if not client:
        add_request_log('POST', '/api/portal/query', {'session_id': session_id}, 401)
        response_data = {'code': 401, 'message': '未登录或会话已过期'}
        log_request_to_file('POST', '/api/portal/query', data, response_data)
        return jsonify(response_data), 401
    
    result = client.query_pass_data(query_params)
    
    if result['success']:
        session_manager.update_timestamp(session_id)
        add_request_log('POST', '/api/portal/query', {'session_id': session_id}, 200)
        response_data = {'code': 200, 'message': 'success', 'data': result['data']}
        log_request_to_file('POST', '/api/portal/query', data, response_data)
        return jsonify(response_data)
    else:
        add_request_log('POST', '/api/portal/query', {'session_id': session_id}, 500)
        response_data = {'code': 500, 'message': result['error']}
        log_request_to_file('POST', '/api/portal/query', data, response_data)
        return jsonify(response_data), 500

@app.route('/api/portal/status', methods=['GET'])
def status():
    session_manager.update_activity()
    session_id = request.args.get('session_id')
    
    if not session_id:
        add_request_log('GET', '/api/portal/status', None, 400)
        response_data = {'code': 400, 'message': '缺少session_id'}
        log_request_to_file('GET', '/api/portal/status', {'session_id': session_id}, response_data)
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    
    if client and client.is_logged_in():
        status_data = client.get_status()
        add_request_log('GET', '/api/portal/status', {'session_id': session_id}, 200)
        response_data = {
            'code': 200,
            'message': '已登录',
            'data': {
                'logged_in': True,
                'user_info': status_data['user_info'],
                'login_time': status_data['login_time'],
                'expires_at': status_data['expires_at']
            }
        }
        log_request_to_file('GET', '/api/portal/status', {'session_id': session_id}, response_data)
        return jsonify(response_data)
    else:
        add_request_log('GET', '/api/portal/status', {'session_id': session_id}, 200)
        response_data = {'code': 200, 'message': '未登录', 'data': {'logged_in': False}}
        log_request_to_file('GET', '/api/portal/status', {'session_id': session_id}, response_data)
        return jsonify(response_data)

@app.route('/api/portal/logout', methods=['POST'])
def logout():
    session_manager.update_activity()
    data = request.json or {}
    session_id = data.get('session_id')
    
    if session_id:
        session_manager.remove_session(session_id)
    
    add_request_log('POST', '/api/portal/logout', {'session_id': session_id}, 200)
    response_data = {'code': 200, 'message': '登出成功'}
    log_request_to_file('POST', '/api/portal/logout', {'session_id': session_id}, response_data)
    return jsonify(response_data)

@app.route('/api/portal/keep-alive', methods=['POST'])
def keep_alive():
    session_manager.update_activity()
    data = request.json
    session_id = data.get('session_id') if data else None
    
    if not session_id:
        add_request_log('POST', '/api/portal/keep-alive', None, 400)
        response_data = {'code': 400, 'message': '缺少session_id参数'}
        log_request_to_file('POST', '/api/portal/keep-alive', {'session_id': session_id}, response_data)
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    if not client:
        add_request_log('POST', '/api/portal/keep-alive', {'session_id': session_id}, 401)
        response_data = {'code': 401, 'message': '会话不存在或已过期', 'data': {'session_expired': True, 'need_relogin': True}}
        log_request_to_file('POST', '/api/portal/keep-alive', {'session_id': session_id}, response_data)
        return jsonify(response_data), 401
    
    result = client.keep_alive()
    
    if result['success']:
        session_manager.update_timestamp(session_id)
        add_request_log('POST', '/api/portal/keep-alive', {'session_id': session_id}, 200)
        response_data = {'code': 200, 'message': result['message'], 'data': {'session_expired': False, 'logged_in': True}}
        log_request_to_file('POST', '/api/portal/keep-alive', {'session_id': session_id}, response_data)
        return jsonify(response_data)
    else:
        session_manager.remove_session(session_id)
        add_request_log('POST', '/api/portal/keep-alive', {'session_id': session_id}, 500)
        response_data = {'code': 500, 'message': result['error'], 'data': {'session_expired': True, 'need_relogin': True}}
        log_request_to_file('POST', '/api/portal/keep-alive', {'session_id': session_id}, response_data)
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
        add_request_log('POST', '/api/portal/ai-audit/vehicle-images', None, 400)
        response_data = {'code': 400, 'message': '请求体不能为空'}
        log_request_to_file('POST', '/api/portal/ai-audit/vehicle-images', data, response_data)
        return jsonify(response_data), 400
    
    session_id = data.get('session_id')
    plate_number = data.get('plate_number')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    page = data.get('page', 0)
    page_size = data.get('page_size', 20)
    sort = data.get('sort', 'picTime DESC')
    
    if not all([session_id, plate_number, start_time, end_time]):
        add_request_log('POST', '/api/portal/ai-audit/vehicle-images', {'session_id': session_id}, 400)
        response_data = {'code': 400, 'message': '缺少必要参数'}
        log_request_to_file('POST', '/api/portal/ai-audit/vehicle-images', data, response_data)
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        add_request_log('POST', '/api/portal/ai-audit/vehicle-images', {'session_id': session_id}, 401)
        response_data = {'code': 401, 'message': '未登录或会话已过期'}
        log_request_to_file('POST', '/api/portal/ai-audit/vehicle-images', data, response_data)
        return jsonify(response_data), 401
    
    try:
        ai_client = AIAuditClient(client.access_token)
        result = ai_client.query_vehicle_images(
            plate_number=plate_number,
            start_time=start_time,
            end_time=end_time,
            rows=page_size,
            start=page,
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
                    'stationId': img.get('stationId', ''),
                    'stationName': img.get('stationName', ''),
                    'picTime': img.get('picTime', ''),
                    'picturePath': img.get('picturePath', ''),
                    'bigPositivePic': big_positive_pic
                }
                processed_images.append(processed_img)
            
            result['images'] = processed_images
            
            add_request_log('POST', '/api/portal/ai-audit/vehicle-images', {'session_id': session_id, 'plate_number': plate_number}, 200)
            response_data = {'code': 200, 'message': 'success', 'data': result}
            log_request_to_file('POST', '/api/portal/ai-audit/vehicle-images', data, response_data)
            return jsonify(response_data)
        else:
            add_request_log('POST', '/api/portal/ai-audit/vehicle-images', {'session_id': session_id, 'plate_number': plate_number}, 500)
            response_data = {'code': 500, 'message': result['error']}
            log_request_to_file('POST', '/api/portal/ai-audit/vehicle-images', data, response_data)
            return jsonify(response_data), 500
    except Exception as e:
        logger.error(f"车辆图库查询失败: {e}")
        add_request_log('POST', '/api/portal/ai-audit/vehicle-images', {'session_id': session_id, 'plate_number': plate_number}, 500)
        response_data = {'code': 500, 'message': str(e)}
        log_request_to_file('POST', '/api/portal/ai-audit/vehicle-images', data, response_data)
        return jsonify(response_data), 500

@app.route('/api/portal/ai-audit/original-image', methods=['POST'])
def ai_audit_original_image():
    session_manager.update_activity()
    data = request.json
    
    if not data:
        add_request_log('POST', '/api/portal/ai-audit/original-image', None, 400)
        response_data = {'code': 400, 'message': '请求体不能为空'}
        log_request_to_file('POST', '/api/portal/ai-audit/original-image', data, response_data)
        return jsonify(response_data), 400
    
    session_id = data.get('session_id')
    picture_path = data.get('picture_path')
    
    if not all([session_id, picture_path]):
        add_request_log('POST', '/api/portal/ai-audit/original-image', {'session_id': session_id}, 400)
        response_data = {'code': 400, 'message': '缺少必要参数'}
        log_request_to_file('POST', '/api/portal/ai-audit/original-image', data, response_data)
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        add_request_log('POST', '/api/portal/ai-audit/original-image', {'session_id': session_id}, 401)
        response_data = {'code': 401, 'message': '未登录或会话已过期'}
        log_request_to_file('POST', '/api/portal/ai-audit/original-image', data, response_data)
        return jsonify(response_data), 401
    
    try:
        if picture_path.startswith('/'):
            full_url = f'http://api.hngsetc.com{picture_path}'
        else:
            full_url = picture_path
        
        request_headers = {
            'Host': 'api.hngsetc.com',
            'Accept': 'application/json, text/plain, */*',
            'Authorization': client.access_token,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.49',
            'Origin': 'http://twaudit.hngsetc.com',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6'
        }
        
        log_headers = {
            'Host': 'api.hngsetc.com',
            'Accept': 'application/json, text/plain, */*',
            'Authorization': f'{client.access_token[:20]}...' if client.access_token else 'None',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.49',
            'Origin': 'http://twaudit.hngsetc.com'
        }
        
        logger.info(f"========== 获取原图请求开始 ==========")
        logger.info(f"请求URL: {full_url}")
        logger.info(f"请求头: {json.dumps(log_headers, ensure_ascii=False, indent=2)}")
        
        response = client.session.get(full_url, headers=request_headers, timeout=30)
        
        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应头: {json.dumps(dict(response.headers), ensure_ascii=False, indent=2)}")
        
        response_headers_dict = dict(response.headers)
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            logger.info(f"Content-Type: {content_type}")
            logger.info(f"响应体长度: {len(response.content)} bytes")
            
            if content_type and content_type.startswith('image'):
                logger.info("响应类型: 图片 - 成功获取原图")
                logger.info(f"========== 获取原图请求结束(成功) ==========")
                image_base64 = base64.b64encode(response.content).decode('utf-8')
                main_content_type = content_type.split(';')[0].strip()
                data_url = f"data:{main_content_type};base64,{image_base64}"
                result = {
                    'code': 200,
                    'message': 'success',
                    'data': {
                        'image': image_base64,
                        'data_url': data_url,
                        'content_type': main_content_type,
                        'request_url': full_url,
                        'response_status': response.status_code,
                        'response_content_type': content_type,
                        'response_content_length': len(response.content),
                        'response_headers': response_headers_dict
                    }
                }
                update_latest_response(result)
                add_request_log('POST', '/api/portal/ai-audit/original-image', {'session_id': session_id}, 200)
                log_request_to_file('POST', '/api/portal/ai-audit/original-image', data, {'code': 200, 'message': 'success'})
                return jsonify(result)
            elif content_type and 'application/json' in content_type:
                logger.info(f"响应类型: JSON - 响应体内容前200字符: {response.text[:200]}")
                
                if response.text.startswith('data:image'):
                    logger.info("响应体是data_url格式 - 成功获取图片")
                    logger.info(f"========== 获取原图请求结束(data_url成功) ==========")
                    data_url = response.text.strip()
                    if data_url.startswith('data:image/') and ';base64,' in data_url:
                        parts = data_url.split(';base64,')
                        if len(parts) == 2:
                            image_base64 = parts[1]
                            main_content_type = parts[0].replace('data:', '')
                            result = {
                                'code': 200,
                                'message': 'success',
                                'data': {
                                    'image': image_base64,
                                    'data_url': data_url,
                                    'content_type': main_content_type,
                                    'request_url': full_url,
                                    'response_status': response.status_code,
                                    'response_content_type': content_type,
                                    'response_content_length': len(response.content),
                                    'response_headers': response_headers_dict
                                }
                            }
                            update_latest_response(result)
                            add_request_log('POST', '/api/portal/ai-audit/original-image', {'session_id': session_id}, 200)
                            log_request_to_file('POST', '/api/portal/ai-audit/original-image', data, {'code': 200, 'message': 'success'})
                            return jsonify(result)
                    logger.error(f"data_url格式解析失败")
                    add_request_log('POST', '/api/portal/ai-audit/original-image', {'session_id': session_id}, 500)
                    response_data = {
                        'code': 500, 
                        'message': 'data_url格式解析失败',
                        'data': {
                            'request_url': full_url,
                            'response_status': response.status_code,
                            'response_content_type': content_type,
                            'response_headers': response_headers_dict,
                            'response_body': response.text[:500]
                        }
                    }
                    log_request_to_file('POST', '/api/portal/ai-audit/original-image', data, response_data)
                    return jsonify(response_data), 500
                
                logger.info(f"========== 获取原图请求结束(JSON错误) ==========")
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_data.get('msg', '云门户返回错误'))
                    logger.error(f"获取原图失败，云门户响应: {error_data}")
                    add_request_log('POST', '/api/portal/ai-audit/original-image', {'session_id': session_id}, 500)
                    response_data = {
                        'code': 500, 
                        'message': f'云门户错误: {error_msg}',
                        'data': {
                            'request_url': full_url,
                            'response_status': response.status_code,
                            'response_content_type': content_type,
                            'response_headers': response_headers_dict,
                            'response_body': response.text[:2000]
                        }
                    }
                    log_request_to_file('POST', '/api/portal/ai-audit/original-image', data, response_data)
                    return jsonify(response_data), 500
                except:
                    logger.error(f"获取原图失败，响应内容: {response.text[:500]}")
                    add_request_log('POST', '/api/portal/ai-audit/original-image', {'session_id': session_id}, 500)
                    response_data = {
                        'code': 500, 
                        'message': '云门户返回异常响应',
                        'data': {
                            'request_url': full_url,
                            'response_status': response.status_code,
                            'response_content_type': content_type,
                            'response_headers': response_headers_dict,
                            'response_body': response.text[:2000]
                        }
                    }
                    log_request_to_file('POST', '/api/portal/ai-audit/original-image', data, response_data)
                    return jsonify(response_data), 500
            else:
                logger.info(f"响应类型: 未知 - 响应体前500字符: {response.text[:500]}")
                logger.info(f"========== 获取原图请求结束(未知类型) ==========")
                logger.error(f"获取原图失败，Content-Type: {content_type}, 响应长度: {len(response.content)}")
                add_request_log('POST', '/api/portal/ai-audit/original-image', {'session_id': session_id}, 500)
                response_data = {
                    'code': 500, 
                    'message': f'响应类型异常: {content_type}',
                    'data': {
                        'request_url': full_url,
                        'response_status': response.status_code,
                        'response_content_type': content_type,
                        'response_headers': response_headers_dict,
                        'response_body': response.text[:2000]
                    }
                }
                log_request_to_file('POST', '/api/portal/ai-audit/original-image', data, response_data)
                return jsonify(response_data), 500
        else:
            logger.info(f"响应体内容: {response.text[:1000]}")
            logger.info(f"========== 获取原图请求结束(HTTP错误) ==========")
            logger.error(f"获取图片失败，状态码: {response.status_code}, 响应: {response.text[:500]}")
            add_request_log('POST', '/api/portal/ai-audit/original-image', {'session_id': session_id}, 500)
            response_data = {
                'code': 500, 
                'message': f'获取图片失败，状态码: {response.status_code}',
                'data': {
                    'referer': referer,
                    'response_status': response.status_code,
                    'response_headers': response_headers_dict,
                    'response_body': response.text[:2000]
                }
            }
            log_request_to_file('POST', '/api/portal/ai-audit/original-image', data, response_data)
            return jsonify(response_data), 500
    except requests.exceptions.Timeout:
        restore_create_connection()
        logger.error("获取原始图片超时")
        add_request_log('POST', '/api/portal/ai-audit/original-image', {'session_id': session_id}, 500)
        response_data = {'code': 500, 'message': '获取图片超时'}
        log_request_to_file('POST', '/api/portal/ai-audit/original-image', data, response_data)
        return jsonify(response_data), 500
    except requests.exceptions.ConnectionError as e:
        restore_create_connection()
        logger.error(f"获取原始图片连接失败: {e}")
        add_request_log('POST', '/api/portal/ai-audit/original-image', {'session_id': session_id}, 500)
        response_data = {'code': 500, 'message': '无法连接到图片服务器'}
        log_request_to_file('POST', '/api/portal/ai-audit/original-image', data, response_data)
        return jsonify(response_data), 500
    except Exception as e:
        restore_create_connection()
        logger.error(f"获取原始图片失败: {e}")
        add_request_log('POST', '/api/portal/ai-audit/original-image', {'session_id': session_id}, 500)
        response_data = {'code': 500, 'message': str(e)}
        log_request_to_file('POST', '/api/portal/ai-audit/original-image', data, response_data)
        return jsonify(response_data), 500

@app.route('/api/portal/fetch-picture', methods=['POST'])
def fetch_picture():
    session_manager.update_activity()
    data = request.json
    
    if not data:
        add_request_log('POST', '/api/portal/fetch-picture', None, 400)
        response_data = {'code': 400, 'message': '请求体不能为空'}
        log_request_to_file('POST', '/api/portal/fetch-picture', data, response_data)
        return jsonify(response_data), 400
    
    session_id = data.get('session_id')
    picture_url = data.get('picture_url')
    
    if not all([session_id, picture_url]):
        add_request_log('POST', '/api/portal/fetch-picture', {'session_id': session_id}, 400)
        response_data = {'code': 400, 'message': '缺少必要参数'}
        log_request_to_file('POST', '/api/portal/fetch-picture', data, response_data)
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        add_request_log('POST', '/api/portal/fetch-picture', {'session_id': session_id}, 401)
        response_data = {'code': 401, 'message': '未登录或会话已过期'}
        log_request_to_file('POST', '/api/portal/fetch-picture', data, response_data)
        return jsonify(response_data), 401
    
    try:
        if picture_url.startswith('/'):
            full_url = f'http://api.hngsetc.com{picture_url}'
        else:
            full_url = picture_url
        
        request_headers = {
            'Host': 'api.hngsetc.com',
            'Accept': 'application/json, text/plain, */*',
            'Authorization': client.access_token,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.49',
            'Origin': 'http://twaudit.hngsetc.com',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6'
        }
        
        log_headers = {
            'Host': 'api.hngsetc.com',
            'Accept': 'application/json, text/plain, */*',
            'Authorization': f'{client.access_token[:20]}...' if client.access_token else 'None',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.49',
            'Origin': 'http://twaudit.hngsetc.com'
        }
        
        logger.info(f"========== 获取指定图片请求开始 ==========")
        logger.info(f"请求URL: {full_url}")
        logger.info(f"请求头: {json.dumps(log_headers, ensure_ascii=False, indent=2)}")
        
        response = client.session.get(full_url, headers=request_headers, timeout=30)
        
        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应头: {json.dumps(dict(response.headers), ensure_ascii=False, indent=2)}")
        
        response_headers_dict = dict(response.headers)
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            logger.info(f"Content-Type: {content_type}")
            logger.info(f"响应体长度: {len(response.content)} bytes")
            
            if content_type and content_type.startswith('image'):
                logger.info("响应类型: 图片 - 成功获取图片")
                logger.info(f"========== 获取指定图片请求结束(成功) ==========")
                image_base64 = base64.b64encode(response.content).decode('utf-8')
                main_content_type = content_type.split(';')[0].strip()
                data_url = f"data:{main_content_type};base64,{image_base64}"
                result = {
                    'code': 200,
                    'message': 'success',
                    'data': {
                        'image': image_base64,
                        'data_url': data_url,
                        'content_type': main_content_type,
                        'request_url': full_url,
                        'response_status': response.status_code,
                        'response_content_type': content_type,
                        'response_content_length': len(response.content),
                        'response_headers': response_headers_dict
                    }
                }
                update_latest_response(result)
                add_request_log('POST', '/api/portal/fetch-picture', {'session_id': session_id}, 200)
                log_request_to_file('POST', '/api/portal/fetch-picture', data, {'code': 200, 'message': 'success'})
                return jsonify(result)
            elif content_type and 'application/json' in content_type:
                logger.info(f"响应类型: JSON - 响应体内容前200字符: {response.text[:200]}")
                
                if response.text.startswith('data:image'):
                    logger.info("响应体是data_url格式 - 成功获取图片")
                    logger.info(f"========== 获取指定图片请求结束(data_url成功) ==========")
                    data_url = response.text.strip()
                    if data_url.startswith('data:image/') and ';base64,' in data_url:
                        parts = data_url.split(';base64,')
                        if len(parts) == 2:
                            image_base64 = parts[1]
                            main_content_type = parts[0].replace('data:', '')
                            result = {
                                'code': 200,
                                'message': 'success',
                                'data': {
                                    'image': image_base64,
                                    'data_url': data_url,
                                    'content_type': main_content_type,
                                    'request_url': full_url,
                                    'response_status': response.status_code,
                                    'response_content_type': content_type,
                                    'response_content_length': len(response.content),
                                    'response_headers': response_headers_dict
                                }
                            }
                            update_latest_response(result)
                            add_request_log('POST', '/api/portal/fetch-picture', {'session_id': session_id}, 200)
                            log_request_to_file('POST', '/api/portal/fetch-picture', data, {'code': 200, 'message': 'success'})
                            return jsonify(result)
                    logger.error(f"data_url格式解析失败")
                    add_request_log('POST', '/api/portal/fetch-picture', {'session_id': session_id}, 500)
                    response_data = {
                        'code': 500, 
                        'message': 'data_url格式解析失败',
                        'data': {
                            'request_url': full_url,
                            'response_status': response.status_code,
                            'response_content_type': content_type,
                            'response_headers': response_headers_dict,
                            'response_body': response.text[:500]
                        }
                    }
                    log_request_to_file('POST', '/api/portal/fetch-picture', data, response_data)
                    return jsonify(response_data), 500
                
                logger.info(f"========== 获取指定图片请求结束(JSON) ==========")
                add_request_log('POST', '/api/portal/fetch-picture', {'session_id': session_id}, 200)
                response_data = {
                    'code': 200,
                    'message': 'success',
                    'data': {
                        'request_url': full_url,
                        'response_status': response.status_code,
                        'response_content_type': content_type,
                        'response_headers': response_headers_dict,
                        'response_body': response.text
                    }
                }
                log_request_to_file('POST', '/api/portal/fetch-picture', data, response_data)
                return jsonify(response_data)
            else:
                logger.info(f"响应类型: 未知 - Content-Type: {content_type}")
                logger.info(f"========== 获取指定图片请求结束(未知类型) ==========")
                add_request_log('POST', '/api/portal/fetch-picture', {'session_id': session_id}, 500)
                response_data = {
                    'code': 500, 
                    'message': f'响应类型异常: {content_type}',
                    'data': {
                        'request_url': full_url,
                        'response_status': response.status_code,
                        'response_content_type': content_type,
                        'response_headers': response_headers_dict,
                        'response_body': response.text[:2000]
                    }
                }
                log_request_to_file('POST', '/api/portal/fetch-picture', data, response_data)
                return jsonify(response_data), 500
        else:
            logger.info(f"响应体内容: {response.text[:1000]}")
            logger.info(f"========== 获取指定图片请求结束(HTTP错误) ==========")
            logger.error(f"获取图片失败，状态码: {response.status_code}, 响应: {response.text[:500]}")
            add_request_log('POST', '/api/portal/fetch-picture', {'session_id': session_id}, 500)
            response_data = {
                'code': 500, 
                'message': f'获取图片失败，状态码: {response.status_code}',
                'data': {
                    'request_url': full_url,
                    'response_status': response.status_code,
                    'response_headers': response_headers_dict,
                    'response_body': response.text[:2000]
                }
            }
            log_request_to_file('POST', '/api/portal/fetch-picture', data, response_data)
            return jsonify(response_data), 500
    except requests.exceptions.Timeout:
        restore_create_connection()
        logger.error("获取图片超时")
        add_request_log('POST', '/api/portal/fetch-picture', {'session_id': session_id}, 500)
        response_data = {'code': 500, 'message': '获取图片超时'}
        log_request_to_file('POST', '/api/portal/fetch-picture', data, response_data)
        return jsonify(response_data), 500
    except requests.exceptions.ConnectionError as e:
        restore_create_connection()
        logger.error(f"获取图片连接失败: {e}")
        add_request_log('POST', '/api/portal/fetch-picture', {'session_id': session_id}, 500)
        response_data = {'code': 500, 'message': '无法连接到图片服务器'}
        log_request_to_file('POST', '/api/portal/fetch-picture', data, response_data)
        return jsonify(response_data), 500
    except Exception as e:
        restore_create_connection()
        logger.error(f"获取图片失败: {e}")
        add_request_log('POST', '/api/portal/fetch-picture', {'session_id': session_id}, 500)
        response_data = {'code': 500, 'message': str(e)}
        log_request_to_file('POST', '/api/portal/fetch-picture', data, response_data)
        return jsonify(response_data), 500

@app.route('/api/portal/ai-audit/gantry-trade', methods=['POST'])
def ai_audit_gantry_trade():
    session_manager.update_activity()
    data = request.json
    
    if not data:
        add_request_log('POST', '/api/portal/ai-audit/gantry-trade', None, 400)
        response_data = {'code': 400, 'message': '请求体不能为空'}
        log_request_to_file('POST', '/api/portal/ai-audit/gantry-trade', data, response_data)
        return jsonify(response_data), 400
    
    session_id = data.get('session_id')
    query_value = data.get('query_value')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    
    if not all([session_id, query_value, start_time, end_time]):
        add_request_log('POST', '/api/portal/ai-audit/gantry-trade', {'session_id': session_id}, 400)
        response_data = {'code': 400, 'message': '缺少必要参数'}
        log_request_to_file('POST', '/api/portal/ai-audit/gantry-trade', data, response_data)
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        add_request_log('POST', '/api/portal/ai-audit/gantry-trade', {'session_id': session_id}, 401)
        response_data = {'code': 401, 'message': '未登录或会话已过期'}
        log_request_to_file('POST', '/api/portal/ai-audit/gantry-trade', data, response_data)
        return jsonify(response_data), 401
    
    try:
        ai_client = AIAuditClient(client.access_token)
        result = ai_client.query_gantry_trade(
            query_value=query_value,
            start_time=start_time,
            end_time=end_time
        )
        
        if result['success']:
            add_request_log('POST', '/api/portal/ai-audit/gantry-trade', {'session_id': session_id}, 200)
            response_data = {
                'code': 200,
                'message': 'success',
                'data': {
                    'total': result['total'],
                    'records': result['records']
                }
            }
            log_request_to_file('POST', '/api/portal/ai-audit/gantry-trade', data, response_data)
            return jsonify(response_data)
        else:
            add_request_log('POST', '/api/portal/ai-audit/gantry-trade', {'session_id': session_id}, 500)
            response_data = {'code': 500, 'message': result['error']}
            log_request_to_file('POST', '/api/portal/ai-audit/gantry-trade', data, response_data)
            return jsonify(response_data), 500
    except Exception as e:
        logger.error(f"门架交易查询失败: {e}")
        add_request_log('POST', '/api/portal/ai-audit/gantry-trade', {'session_id': session_id}, 500)
        response_data = {'code': 500, 'message': str(e)}
        log_request_to_file('POST', '/api/portal/ai-audit/gantry-trade', data, response_data)
        return jsonify(response_data), 500

@app.route('/api/portal/ai-audit/gantry-plate', methods=['POST'])
def ai_audit_gantry_plate():
    session_manager.update_activity()
    data = request.json
    
    if not data:
        add_request_log('POST', '/api/portal/ai-audit/gantry-plate', None, 400)
        response_data = {'code': 400, 'message': '请求体不能为空'}
        log_request_to_file('POST', '/api/portal/ai-audit/gantry-plate', data, response_data)
        return jsonify(response_data), 400
    
    session_id = data.get('session_id')
    plate_number = data.get('plate_number')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    
    if not all([session_id, plate_number, start_time, end_time]):
        add_request_log('POST', '/api/portal/ai-audit/gantry-plate', {'session_id': session_id}, 400)
        response_data = {'code': 400, 'message': '缺少必要参数'}
        log_request_to_file('POST', '/api/portal/ai-audit/gantry-plate', data, response_data)
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        add_request_log('POST', '/api/portal/ai-audit/gantry-plate', {'session_id': session_id}, 401)
        response_data = {'code': 401, 'message': '未登录或会话已过期'}
        log_request_to_file('POST', '/api/portal/ai-audit/gantry-plate', data, response_data)
        return jsonify(response_data), 401
    
    try:
        ai_client = AIAuditClient(client.access_token)
        result = ai_client.query_gantry_plate(
            plate_number=plate_number,
            start_time=start_time,
            end_time=end_time
        )
        
        if result['success']:
            add_request_log('POST', '/api/portal/ai-audit/gantry-plate', {'session_id': session_id}, 200)
            response_data = {
                'code': 200,
                'message': 'success',
                'data': {
                    'total': result['total'],
                    'records': result['records']
                }
            }
            log_request_to_file('POST', '/api/portal/ai-audit/gantry-plate', data, response_data)
            return jsonify(response_data)
        else:
            add_request_log('POST', '/api/portal/ai-audit/gantry-plate', {'session_id': session_id}, 500)
            response_data = {'code': 500, 'message': result['error']}
            log_request_to_file('POST', '/api/portal/ai-audit/gantry-plate', data, response_data)
            return jsonify(response_data), 500
    except Exception as e:
        logger.error(f"门架牌识查询失败: {e}")
        add_request_log('POST', '/api/portal/ai-audit/gantry-plate', {'session_id': session_id}, 500)
        response_data = {'code': 500, 'message': str(e)}
        log_request_to_file('POST', '/api/portal/ai-audit/gantry-plate', data, response_data)
        return jsonify(response_data), 500

@app.route('/api/portal/ai-audit/exit-trade', methods=['POST'])
def ai_audit_exit_trade():
    session_manager.update_activity()
    data = request.json
    
    if not data:
        add_request_log('POST', '/api/portal/ai-audit/exit-trade', None, 400)
        response_data = {'code': 400, 'message': '请求体不能为空'}
        log_request_to_file('POST', '/api/portal/ai-audit/exit-trade', data, response_data)
        return jsonify(response_data), 400
    
    session_id = data.get('session_id')
    query_value = data.get('query_value')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    trade_type = data.get('trade_type', 1)
    
    if not all([session_id, query_value, start_time, end_time]):
        add_request_log('POST', '/api/portal/ai-audit/exit-trade', {'session_id': session_id}, 400)
        response_data = {'code': 400, 'message': '缺少必要参数'}
        log_request_to_file('POST', '/api/portal/ai-audit/exit-trade', data, response_data)
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        add_request_log('POST', '/api/portal/ai-audit/exit-trade', {'session_id': session_id}, 401)
        response_data = {'code': 401, 'message': '未登录或会话已过期'}
        log_request_to_file('POST', '/api/portal/ai-audit/exit-trade', data, response_data)
        return jsonify(response_data), 401
    
    try:
        ai_client = AIAuditClient(client.access_token)
        result = ai_client.query_exit_trade(
            query_value=query_value,
            start_time=start_time,
            end_time=end_time,
            trade_type=trade_type
        )
        
        if result['success']:
            add_request_log('POST', '/api/portal/ai-audit/exit-trade', {'session_id': session_id}, 200)
            response_data = {
                'code': 200,
                'message': 'success',
                'data': {
                    'total': result['total'],
                    'records': result['records']
                }
            }
            log_request_to_file('POST', '/api/portal/ai-audit/exit-trade', data, response_data)
            return jsonify(response_data)
        else:
            add_request_log('POST', '/api/portal/ai-audit/exit-trade', {'session_id': session_id}, 500)
            response_data = {'code': 500, 'message': result['error']}
            log_request_to_file('POST', '/api/portal/ai-audit/exit-trade', data, response_data)
            return jsonify(response_data), 500
    except Exception as e:
        logger.error(f"出口交易查询失败: {e}")
        add_request_log('POST', '/api/portal/ai-audit/exit-trade', {'session_id': session_id}, 500)
        response_data = {'code': 500, 'message': str(e)}
        log_request_to_file('POST', '/api/portal/ai-audit/exit-trade', data, response_data)
        return jsonify(response_data), 500

@app.route('/api/portal/ai-audit/suspected-car', methods=['POST'])
def ai_audit_suspected_car():
    session_manager.update_activity()
    data = request.json
    
    if not data:
        add_request_log('POST', '/api/portal/ai-audit/suspected-car', None, 400)
        response_data = {'code': 400, 'message': '请求体不能为空'}
        log_request_to_file('POST', '/api/portal/ai-audit/suspected-car', data, response_data)
        return jsonify(response_data), 400
    
    session_id = data.get('session_id')
    vehicle_or_pass_id = data.get('vehicle_or_pass_id')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    
    if not all([session_id, vehicle_or_pass_id, start_time, end_time]):
        add_request_log('POST', '/api/portal/ai-audit/suspected-car', {'session_id': session_id}, 400)
        response_data = {'code': 400, 'message': '缺少必要参数'}
        log_request_to_file('POST', '/api/portal/ai-audit/suspected-car', data, response_data)
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        add_request_log('POST', '/api/portal/ai-audit/suspected-car', {'session_id': session_id}, 401)
        response_data = {'code': 401, 'message': '未登录或会话已过期'}
        log_request_to_file('POST', '/api/portal/ai-audit/suspected-car', data, response_data)
        return jsonify(response_data), 401
    
    try:
        ai_client = AIAuditClient(client.access_token)
        result = ai_client.query_suspected_car(
            vehicle_or_pass_id=vehicle_or_pass_id,
            start_time=start_time,
            end_time=end_time
        )
        
        if result['success']:
            add_request_log('POST', '/api/portal/ai-audit/suspected-car', {'session_id': session_id}, 200)
            response_data = {
                'code': 200,
                'message': 'success',
                'data': {
                    'trade_list': result['trade_list']
                }
            }
            log_request_to_file('POST', '/api/portal/ai-audit/suspected-car', data, response_data)
            return jsonify(response_data)
        else:
            add_request_log('POST', '/api/portal/ai-audit/suspected-car', {'session_id': session_id}, 500)
            response_data = {'code': 500, 'message': result['error']}
            log_request_to_file('POST', '/api/portal/ai-audit/suspected-car', data, response_data)
            return jsonify(response_data), 500
    except Exception as e:
        logger.error(f"疑难车牌追查失败: {e}")
        add_request_log('POST', '/api/portal/ai-audit/suspected-car', {'session_id': session_id}, 500)
        response_data = {'code': 500, 'message': str(e)}
        log_request_to_file('POST', '/api/portal/ai-audit/suspected-car', data, response_data)
        return jsonify(response_data), 500

@app.route('/api/portal/ai-audit/batch-query', methods=['POST'])
def ai_audit_batch_query():
    session_manager.update_activity()
    data = request.json
    
    if not data:
        add_request_log('POST', '/api/portal/ai-audit/batch-query', None, 400)
        response_data = {'code': 400, 'message': '请求体不能为空'}
        log_request_to_file('POST', '/api/portal/ai-audit/batch-query', data, response_data)
        return jsonify(response_data), 400
    
    session_id = data.get('session_id')
    plate_number = data.get('plate_number')
    entry_time = data.get('entry_time')
    gate_time = data.get('gate_time')
    pass_id = data.get('pass_id')
    hours = data.get('hours', 5)
    rows = data.get('rows', 40)
    
    if not all([session_id, plate_number, entry_time, gate_time]):
        add_request_log('POST', '/api/portal/ai-audit/batch-query', {'session_id': session_id}, 400)
        response_data = {'code': 400, 'message': '缺少必要参数'}
        log_request_to_file('POST', '/api/portal/ai-audit/batch-query', data, response_data)
        return jsonify(response_data), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        add_request_log('POST', '/api/portal/ai-audit/batch-query', {'session_id': session_id}, 401)
        response_data = {'code': 401, 'message': '未登录或会话已过期'}
        log_request_to_file('POST', '/api/portal/ai-audit/batch-query', data, response_data)
        return jsonify(response_data), 401
    
    try:
        ai_client = AIAuditClient(client.access_token)
        result = ai_client.batch_query_all(
            plate_number=plate_number,
            entry_time=entry_time,
            gate_time=gate_time,
            pass_id=pass_id,
            hours=hours,
            rows=rows
        )
        
        add_request_log('POST', '/api/portal/ai-audit/batch-query', {'session_id': session_id, 'plate_number': plate_number}, 200)
        response_data = {
            'code': 200,
            'message': 'success',
            'data': result
        }
        log_request_to_file('POST', '/api/portal/ai-audit/batch-query', data, response_data)
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"批量查询失败: {e}")
        add_request_log('POST', '/api/portal/ai-audit/batch-query', {'session_id': session_id, 'plate_number': plate_number}, 500)
        response_data = {'code': 500, 'message': str(e)}
        log_request_to_file('POST', '/api/portal/ai-audit/batch-query', data, response_data)
        return jsonify(response_data), 500

@app.route('/api/portal/ai-audit/select-images', methods=['POST'])
def ai_audit_select_images():
    session_manager.update_activity()
    data = request.json
    
    if not data:
        add_request_log('POST', '/api/portal/ai-audit/select-images', None, 400)
        response_data = {'code': 400, 'message': '请求体不能为空'}
        log_request_to_file('POST', '/api/portal/ai-audit/select-images', data, response_data)
        return jsonify(response_data), 400
    
    images = data.get('images', [])
    gantry_ids = data.get('gantry_ids', [])
    
    if not images:
        add_request_log('POST', '/api/portal/ai-audit/select-images', None, 400)
        response_data = {'code': 400, 'message': '缺少图片数据'}
        log_request_to_file('POST', '/api/portal/ai-audit/select-images', data, response_data)
        return jsonify(response_data), 400
    
    try:
        ai_client = AIAuditClient('')
        selected = ai_client.select_images_by_gantry_ids(images, gantry_ids)
        
        result = {}
        if selected['first_gantry']:
            result['image1'] = {
                'base64': AIAuditClient.extract_image_base64(selected['first_gantry']),
                'station_name': selected['first_gantry'].get('stationName', ''),
                'pic_time': selected['first_gantry'].get('picTime', '')
            }
        if selected['last_gantry']:
            result['image2'] = {
                'base64': AIAuditClient.extract_image_base64(selected['last_gantry']),
                'station_name': selected['last_gantry'].get('stationName', ''),
                'pic_time': selected['last_gantry'].get('picTime', '')
            }
        
        add_request_log('POST', '/api/portal/ai-audit/select-images', None, 200)
        response_data = {
            'code': 200,
            'message': 'success',
            'data': result
        }
        log_request_to_file('POST', '/api/portal/ai-audit/select-images', data, response_data)
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"图片选取失败: {e}")
        add_request_log('POST', '/api/portal/ai-audit/select-images', None, 500)
        response_data = {'code': 500, 'message': str(e)}
        log_request_to_file('POST', '/api/portal/ai-audit/select-images', data, response_data)
        return jsonify(response_data), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'code': 404,
        'message': '接口不存在'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"服务器内部错误: {error}")
    return jsonify({
        'code': 500,
        'message': '服务器内部错误'
    }), 500

if __name__ == '__main__':
    logger.info(f"启动云门户查询服务")
    logger.info(f"监听地址: {config.GUI_HOST}:{config.GUI_PORT}")
    
    from werkzeug.serving import run_simple
    run_simple(
        config.GUI_HOST,
        config.GUI_PORT,
        app,
        use_debugger=False,
        use_reloader=False,
        threaded=True
    )
