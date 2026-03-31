import logging
import uuid
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from session_manager import session_manager
from config import config
from ai_audit_client import AIAuditClient
from datetime import datetime
from collections import deque
from network_utils import create_portal_session, restore_create_connection

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

request_log = deque(maxlen=100)

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

def get_request_logs():
    return list(request_log)

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

@app.route('/api/portal/captcha', methods=['GET'])
def get_captcha():
    session_id = request.args.get('session_id')
    
    if not session_id:
        session_id = str(uuid.uuid4())
    
    client = session_manager.get_session(session_id)
    if not client:
        client = session_manager.create_session(session_id)
    
    result = client.get_captcha()
    
    if result['success']:
        add_request_log('GET', '/api/portal/captcha', {'session_id': session_id}, 200)
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
        return jsonify({
            'code': 500,
            'message': result['error']
        }), 500

@app.route('/api/portal/login', methods=['POST'])
def login():
    data = request.json
    
    if not data:
        return jsonify({
            'code': 400,
            'message': '请求体不能为空'
        }), 400
    
    session_id = data.get('session_id')
    username = data.get('username')
    password = data.get('password')
    captcha = data.get('captcha')
    uuid_str = data.get('uuid')
    
    if not all([session_id, username, password, captcha, uuid_str]):
        return jsonify({
            'code': 400,
            'message': '缺少必要参数'
        }), 400
    
    client = session_manager.get_session(session_id)
    if not client:
        return jsonify({
            'code': 401,
            'message': '会话已过期，请刷新验证码'
        }), 401
    
    result = client.login(username, password, captcha, uuid_str)
    
    if result['success']:
        session_manager.update_timestamp(session_id)
        return jsonify({
            'code': 200,
            'message': '登录成功',
            'data': {
                'user_info': result['user_info']
            }
        })
    else:
        return jsonify({
            'code': 401,
            'message': result['error']
        }), 401

@app.route('/api/portal/query', methods=['POST'])
def query():
    data = request.json
    
    if not data:
        return jsonify({
            'code': 400,
            'message': '请求体不能为空'
        }), 400
    
    session_id = data.get('session_id')
    query_params = data.get('query_params')
    
    if not session_id:
        return jsonify({
            'code': 400,
            'message': '缺少session_id'
        }), 400
    
    if not query_params:
        return jsonify({
            'code': 400,
            'message': '缺少查询参数'
        }), 400
    
    client = session_manager.get_session(session_id)
    if not client:
        return jsonify({
            'code': 401,
            'message': '未登录或会话已过期'
        }), 401
    
    result = client.query_pass_data(query_params)
    
    if result['success']:
        session_manager.update_timestamp(session_id)
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result['data']
        })
    else:
        return jsonify({
            'code': 500,
            'message': result['error']
        }), 500

@app.route('/api/portal/status', methods=['GET'])
def status():
    session_id = request.args.get('session_id')
    
    if not session_id:
        return jsonify({
            'code': 400,
            'message': '缺少session_id'
        }), 400
    
    client = session_manager.get_session(session_id)
    
    if client and client.is_logged_in():
        status_data = client.get_status()
        return jsonify({
            'code': 200,
            'message': '已登录',
            'data': {
                'logged_in': True,
                'user_info': status_data['user_info'],
                'login_time': status_data['login_time'],
                'expires_at': status_data['expires_at']
            }
        })
    else:
        return jsonify({
            'code': 200,
            'message': '未登录',
            'data': {
                'logged_in': False
            }
        })

@app.route('/api/portal/logout', methods=['POST'])
def logout():
    data = request.json or {}
    session_id = data.get('session_id')
    
    if session_id:
        session_manager.remove_session(session_id)
    
    return jsonify({
        'code': 200,
        'message': '登出成功'
    })

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
    data = request.json
    
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400
    
    session_id = data.get('session_id')
    plate_number = data.get('plate_number')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    page = data.get('page', 0)
    page_size = data.get('page_size', 20)
    sort = data.get('sort', 'picTime DESC')
    
    if not all([session_id, plate_number, start_time, end_time]):
        return jsonify({'code': 400, 'message': '缺少必要参数'}), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        return jsonify({'code': 401, 'message': '未登录或会话已过期'}), 401
    
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
            
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': result
            })
        else:
            return jsonify({'code': 500, 'message': result['error']}), 500
    except Exception as e:
        logger.error(f"车辆图库查询失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/portal/ai-audit/original-image', methods=['POST'])
def ai_audit_original_image():
    data = request.json
    
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400
    
    session_id = data.get('session_id')
    picture_path = data.get('picture_path')
    
    if not all([session_id, picture_path]):
        return jsonify({'code': 400, 'message': '缺少必要参数'}), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        return jsonify({'code': 401, 'message': '未登录或会话已过期'}), 401
    
    try:
        ethernet2_ip = config.ETHERNET2_IP
        img_session = create_portal_session(source_ip=ethernet2_ip)
        
        headers = {
            'Authorization': f'Bearer {client.access_token}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.49',
            'Accept': 'application/json, text/plain, */*',
            'DNT': '1',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6'
        }
        
        response = img_session.get(picture_path, headers=headers, timeout=30)
        restore_create_connection()
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            if content_type and content_type.startswith('image'):
                image_base64 = base64.b64encode(response.content).decode('utf-8')
                return jsonify({
                    'code': 200,
                    'message': 'success',
                    'data': {
                        'image': image_base64
                    }
                })
            else:
                return jsonify({'code': 500, 'message': f'响应类型异常: {content_type}'}), 500
        else:
            return jsonify({'code': 500, 'message': f'获取图片失败，状态码: {response.status_code}'}), 500
    except requests.exceptions.Timeout:
        restore_create_connection()
        logger.error("获取原始图片超时")
        return jsonify({'code': 500, 'message': '获取图片超时'}), 500
    except requests.exceptions.ConnectionError as e:
        restore_create_connection()
        logger.error(f"获取原始图片连接失败: {e}")
        return jsonify({'code': 500, 'message': '无法连接到图片服务器'}), 500
    except Exception as e:
        restore_create_connection()
        logger.error(f"获取原始图片失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/portal/ai-audit/gantry-trade', methods=['POST'])
def ai_audit_gantry_trade():
    data = request.json
    
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400
    
    session_id = data.get('session_id')
    query_value = data.get('query_value')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    
    if not all([session_id, query_value, start_time, end_time]):
        return jsonify({'code': 400, 'message': '缺少必要参数'}), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        return jsonify({'code': 401, 'message': '未登录或会话已过期'}), 401
    
    try:
        ai_client = AIAuditClient(client.access_token)
        result = ai_client.query_gantry_trade(
            query_value=query_value,
            start_time=start_time,
            end_time=end_time
        )
        
        if result['success']:
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'total': result['total'],
                    'records': result['records']
                }
            })
        else:
            return jsonify({'code': 500, 'message': result['error']}), 500
    except Exception as e:
        logger.error(f"门架交易查询失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/portal/ai-audit/gantry-plate', methods=['POST'])
def ai_audit_gantry_plate():
    data = request.json
    
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400
    
    session_id = data.get('session_id')
    plate_number = data.get('plate_number')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    
    if not all([session_id, plate_number, start_time, end_time]):
        return jsonify({'code': 400, 'message': '缺少必要参数'}), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        return jsonify({'code': 401, 'message': '未登录或会话已过期'}), 401
    
    try:
        ai_client = AIAuditClient(client.access_token)
        result = ai_client.query_gantry_plate(
            plate_number=plate_number,
            start_time=start_time,
            end_time=end_time
        )
        
        if result['success']:
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'total': result['total'],
                    'records': result['records']
                }
            })
        else:
            return jsonify({'code': 500, 'message': result['error']}), 500
    except Exception as e:
        logger.error(f"门架牌识查询失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/portal/ai-audit/exit-trade', methods=['POST'])
def ai_audit_exit_trade():
    data = request.json
    
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400
    
    session_id = data.get('session_id')
    query_value = data.get('query_value')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    trade_type = data.get('trade_type', 1)
    
    if not all([session_id, query_value, start_time, end_time]):
        return jsonify({'code': 400, 'message': '缺少必要参数'}), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        return jsonify({'code': 401, 'message': '未登录或会话已过期'}), 401
    
    try:
        ai_client = AIAuditClient(client.access_token)
        result = ai_client.query_exit_trade(
            query_value=query_value,
            start_time=start_time,
            end_time=end_time,
            trade_type=trade_type
        )
        
        if result['success']:
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'total': result['total'],
                    'records': result['records']
                }
            })
        else:
            return jsonify({'code': 500, 'message': result['error']}), 500
    except Exception as e:
        logger.error(f"出口交易查询失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/portal/ai-audit/suspected-car', methods=['POST'])
def ai_audit_suspected_car():
    data = request.json
    
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400
    
    session_id = data.get('session_id')
    vehicle_or_pass_id = data.get('vehicle_or_pass_id')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    
    if not all([session_id, vehicle_or_pass_id, start_time, end_time]):
        return jsonify({'code': 400, 'message': '缺少必要参数'}), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        return jsonify({'code': 401, 'message': '未登录或会话已过期'}), 401
    
    try:
        ai_client = AIAuditClient(client.access_token)
        result = ai_client.query_suspected_car(
            vehicle_or_pass_id=vehicle_or_pass_id,
            start_time=start_time,
            end_time=end_time
        )
        
        if result['success']:
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'trade_list': result['trade_list']
                }
            })
        else:
            return jsonify({'code': 500, 'message': result['error']}), 500
    except Exception as e:
        logger.error(f"疑难车牌追查失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/portal/ai-audit/batch-query', methods=['POST'])
def ai_audit_batch_query():
    data = request.json
    
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400
    
    session_id = data.get('session_id')
    plate_number = data.get('plate_number')
    entry_time = data.get('entry_time')
    gate_time = data.get('gate_time')
    pass_id = data.get('pass_id')
    
    if not all([session_id, plate_number, entry_time, gate_time]):
        return jsonify({'code': 400, 'message': '缺少必要参数'}), 400
    
    client = session_manager.get_session(session_id)
    if not client or not client.is_logged_in():
        return jsonify({'code': 401, 'message': '未登录或会话已过期'}), 401
    
    try:
        ai_client = AIAuditClient(client.access_token)
        result = ai_client.batch_query_all(
            plate_number=plate_number,
            entry_time=entry_time,
            gate_time=gate_time,
            pass_id=pass_id
        )
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result
        })
    except Exception as e:
        logger.error(f"批量查询失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/portal/ai-audit/select-images', methods=['POST'])
def ai_audit_select_images():
    data = request.json
    
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400
    
    images = data.get('images', [])
    gantry_ids = data.get('gantry_ids', [])
    
    if not images:
        return jsonify({'code': 400, 'message': '缺少图片数据'}), 400
    
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
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result
        })
    except Exception as e:
        logger.error(f"图片选取失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

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
