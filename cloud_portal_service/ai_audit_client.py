import requests
import json
import logging
import base64
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from network_utils import create_portal_session
from config import config

logger = logging.getLogger(__name__)


class AIAuditClient:
    AI_AUDIT_BASE_URL = "http://twaudit.hngsetc.com"
    
    def __init__(self, access_token: str, source_ip: Optional[str] = None):
        self.access_token = access_token
        self.source_ip = source_ip or config.ETHERNET2_IP
        self.session = create_portal_session(self.source_ip)
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json;charset=UTF-8',
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Origin': self.AI_AUDIT_BASE_URL,
            'Referer': f'{self.AI_AUDIT_BASE_URL}/aiAuditWeb/index.html'
        }
    
    def _calculate_time_range(self, entry_time: str, gate_time: str, hours: int = 5) -> Dict[str, str]:
        try:
            entry_dt = datetime.strptime(entry_time, '%Y-%m-%d %H:%M:%S')
            gate_dt = datetime.strptime(gate_time, '%Y-%m-%d %H:%M:%S')
            end_dt = gate_dt + timedelta(hours=hours)
            
            return {
                'start_time': entry_dt.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': end_dt.strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            logger.error(f"时间范围计算失败: {e}")
            return {
                'start_time': entry_time,
                'end_time': gate_time
            }
    
    def query_vehicle_images(
        self,
        plate_number: str,
        start_time: str,
        end_time: str,
        plate_color: str = "",
        rows: int = 40,
        start: int = 0,
        sort: str = "picTime DESC"
    ) -> Dict[str, Any]:
        url = f"{self.AI_AUDIT_BASE_URL}/gateway/ai-audit-server/ExternalAudit/travelTrack.json"
        
        payload = {
            "vehPlate": plate_number,
            "vehPlateColor": plate_color,
            "rows": rows,
            "start": start,
            "sort": sort,
            "startTime": start_time,
            "endTime": end_time
        }
        
        try:
            response = self.session.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get('code', {}).get('ok'):
                return {
                    'success': True,
                    'data': result.get('result', {}),
                    'total': result.get('result', {}).get('total', 0),
                    'images': result.get('result', {}).get('picBeanList', []),
                    'page': start,
                    'page_size': rows
                }
            else:
                return {
                    'success': False,
                    'error': result.get('code', {}).get('msg', '查询失败'),
                    'data': None
                }
        except requests.exceptions.Timeout:
            logger.error("车辆图库查询超时")
            return {'success': False, 'error': '查询超时', 'data': None}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"车辆图库查询连接失败: {e}")
            return {'success': False, 'error': '无法连接到AI稽核服务器', 'data': None}
        except Exception as e:
            logger.error(f"车辆图库查询失败: {e}")
            return {'success': False, 'error': str(e), 'data': None}
    
    def query_gantry_trade(
        self,
        query_value: str,
        start_time: str,
        end_time: str,
        start: int = 0,
        length: int = 50
    ) -> Dict[str, Any]:
        url = f"{self.AI_AUDIT_BASE_URL}/gateway/ai-audit-server/tool/query/gantry/trade"
        
        json_param = {
            "queryValue": query_value,
            "startTime": start_time,
            "endTime": end_time
        }
        
        payload = {
            "draw": 1,
            "start": start,
            "length": length,
            "jsonParam": json.dumps(json_param, ensure_ascii=False)
        }
        
        try:
            response = self.session.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get('code', {}).get('ok'):
                return {
                    'success': True,
                    'data': result.get('result', {}),
                    'total': result.get('result', {}).get('recordsTotal', 0),
                    'records': result.get('result', {}).get('data', [])
                }
            else:
                return {
                    'success': False,
                    'error': result.get('code', {}).get('msg', '查询失败'),
                    'data': None
                }
        except requests.exceptions.Timeout:
            logger.error("门架交易查询超时")
            return {'success': False, 'error': '查询超时', 'data': None}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"门架交易查询连接失败: {e}")
            return {'success': False, 'error': '无法连接到AI稽核服务器', 'data': None}
        except Exception as e:
            logger.error(f"门架交易查询失败: {e}")
            return {'success': False, 'error': str(e), 'data': None}
    
    def query_gantry_plate(
        self,
        plate_number: str,
        start_time: str,
        end_time: str,
        start: int = 0,
        length: int = 50
    ) -> Dict[str, Any]:
        url = f"{self.AI_AUDIT_BASE_URL}/gateway/ai-audit-server/tool/query/picInfo/query"
        
        json_param = {
            "vehPlate": plate_number,
            "startTime": start_time,
            "endTime": end_time
        }
        
        payload = {
            "draw": 1,
            "start": start,
            "length": length,
            "jsonParam": json.dumps(json_param, ensure_ascii=False)
        }
        
        try:
            response = self.session.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get('code', {}).get('ok'):
                return {
                    'success': True,
                    'data': result.get('result', {}),
                    'total': result.get('result', {}).get('recordsTotal', 0),
                    'records': result.get('result', {}).get('data', [])
                }
            else:
                return {
                    'success': False,
                    'error': result.get('code', {}).get('msg', '查询失败'),
                    'data': None
                }
        except requests.exceptions.Timeout:
            logger.error("门架牌识查询超时")
            return {'success': False, 'error': '查询超时', 'data': None}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"门架牌识查询连接失败: {e}")
            return {'success': False, 'error': '无法连接到AI稽核服务器', 'data': None}
        except Exception as e:
            logger.error(f"门架牌识查询失败: {e}")
            return {'success': False, 'error': str(e), 'data': None}
    
    def query_exit_trade(
        self,
        query_value: str,
        start_time: str,
        end_time: str,
        trade_type: int = 1,
        card_id: str = "",
        media_no: str = "",
        start: int = 0,
        length: int = 50
    ) -> Dict[str, Any]:
        url = f"{self.AI_AUDIT_BASE_URL}/gateway/ai-audit-server/tool/query/ex/lane"
        
        json_param = {
            "cardId": card_id,
            "mediaNo": media_no,
            "type": str(trade_type),
            "queryValue": query_value,
            "startTime": start_time,
            "endTime": end_time
        }
        
        payload = {
            "draw": 1,
            "start": start,
            "length": length,
            "jsonParam": json.dumps(json_param, ensure_ascii=False)
        }
        
        try:
            response = self.session.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get('code', {}).get('ok'):
                return {
                    'success': True,
                    'data': result.get('result', {}),
                    'total': result.get('result', {}).get('recordsTotal', 0),
                    'records': result.get('result', {}).get('data', [])
                }
            else:
                return {
                    'success': False,
                    'error': result.get('code', {}).get('msg', '查询失败'),
                    'data': None
                }
        except requests.exceptions.Timeout:
            logger.error("出口交易查询超时")
            return {'success': False, 'error': '查询超时', 'data': None}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"出口交易查询连接失败: {e}")
            return {'success': False, 'error': '无法连接到AI稽核服务器', 'data': None}
        except Exception as e:
            logger.error(f"出口交易查询失败: {e}")
            return {'success': False, 'error': str(e), 'data': None}
    
    def query_suspected_car(
        self,
        vehicle_or_pass_id: str,
        start_time: str,
        end_time: str,
        plate_color: str = "",
        flag: str = "0"
    ) -> Dict[str, Any]:
        url = f"{self.AI_AUDIT_BASE_URL}/gateway/ai-audit-server/tool/suspected/car/query"
        
        payload = {
            "vehicleOrPassId": vehicle_or_pass_id,
            "plateColor": plate_color,
            "flag": flag,
            "begTime": start_time,
            "endTime": end_time
        }
        
        try:
            response = self.session.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get('code', {}).get('ok'):
                return {
                    'success': True,
                    'data': result.get('result', {}),
                    'trade_list': result.get('result', {}).get('tradeList', [])
                }
            else:
                return {
                    'success': False,
                    'error': result.get('code', {}).get('msg', '查询失败'),
                    'data': None
                }
        except requests.exceptions.Timeout:
            logger.error("疑难车牌追查超时")
            return {'success': False, 'error': '查询超时', 'data': None}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"疑难车牌追查连接失败: {e}")
            return {'success': False, 'error': '无法连接到AI稽核服务器', 'data': None}
        except Exception as e:
            logger.error(f"疑难车牌追查失败: {e}")
            return {'success': False, 'error': str(e), 'data': None}
    
    def query_audit_order(
        self,
        vehicle_no: str,
        start: int = 0,
        length: int = 100
    ) -> Dict[str, Any]:
        url = f"{self.AI_AUDIT_BASE_URL}/gateway/ai-audit-server/order-review/auditOrderNoAuth"
        
        json_param = {
            "order": "en_time desc",
            "if_multi_prov": "",
            "startTime": "",
            "endTime": "",
            "dbStartTime": "",
            "dbEndTime": "",
            "vehicle_no": vehicle_no,
            "label_code": "",
            "vehicleType": "",
            "loss_amount_param": "",
            "order_source": "",
            "orderStatusList": [],
            "authority_list": [],
            "centerNo": "",
            "stationNo": "",
            "orderType": "",
            "startTollFee": None,
            "endTollFee": None,
            "startPenaltyFee": None,
            "endPenaltyFee": None
        }
        
        payload = {
            "draw": 1,
            "start": start,
            "length": length,
            "jsonParam": json.dumps(json_param, ensure_ascii=False)
        }
        
        try:
            response = self.session.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get('code', {}).get('ok'):
                return {
                    'success': True,
                    'data': result.get('result', {}),
                    'total': result.get('result', {}).get('recordsTotal', 0),
                    'records': result.get('result', {}).get('data', [])
                }
            else:
                return {
                    'success': False,
                    'error': result.get('code', {}).get('msg', '查询失败'),
                    'data': None
                }
        except requests.exceptions.Timeout:
            logger.error("稽核工单查询超时")
            return {'success': False, 'error': '查询超时', 'data': None}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"稽核工单查询连接失败: {e}")
            return {'success': False, 'error': '无法连接到AI稽核服务器', 'data': None}
        except Exception as e:
            logger.error(f"稽核工单查询失败: {e}")
            return {'success': False, 'error': str(e), 'data': None}
    
    def batch_query_all(
        self,
        plate_number: str,
        entry_time: str,
        gate_time: str,
        pass_id: Optional[str] = None,
        hours: int = 5,
        rows: int = 40
    ) -> Dict[str, Any]:
        time_range = self._calculate_time_range(entry_time, gate_time, hours)
        start_time = time_range['start_time']
        end_time = time_range['end_time']
        
        clean_plate = plate_number.split('_')[0] if '_' in plate_number else plate_number
        
        results = {
            'time_range': time_range,
            'vehicle_images': None,
            'gantry_trade': None,
            'gantry_plate': None,
            'exit_trade_etc': None,
            'exit_trade_other': None,
            'audit_order': None,
            'suspected_car': None,
            'errors': []
        }
        
        results['vehicle_images'] = self.query_vehicle_images(
            plate_number=clean_plate,
            start_time=start_time,
            end_time=end_time,
            rows=rows
        )
        if not results['vehicle_images']['success']:
            results['errors'].append(f"车辆图库查询失败: {results['vehicle_images']['error']}")
        
        results['gantry_trade'] = self.query_gantry_trade(
            query_value=clean_plate,
            start_time=start_time,
            end_time=end_time
        )
        if not results['gantry_trade']['success']:
            results['errors'].append(f"门架交易查询失败: {results['gantry_trade']['error']}")
        
        results['gantry_plate'] = self.query_gantry_plate(
            plate_number=clean_plate,
            start_time=start_time,
            end_time=end_time
        )
        if not results['gantry_plate']['success']:
            results['errors'].append(f"门架牌识查询失败: {results['gantry_plate']['error']}")
        
        results['exit_trade_etc'] = self.query_exit_trade(
            query_value=clean_plate,
            start_time=start_time,
            end_time=end_time,
            trade_type=1
        )
        if not results['exit_trade_etc']['success']:
            results['errors'].append(f"ETC出口交易查询失败: {results['exit_trade_etc']['error']}")
        
        results['exit_trade_other'] = self.query_exit_trade(
            query_value=clean_plate,
            start_time=start_time,
            end_time=end_time,
            trade_type=2
        )
        if not results['exit_trade_other']['success']:
            results['errors'].append(f"其它出口交易查询失败: {results['exit_trade_other']['error']}")
        
        results['audit_order'] = self.query_audit_order(
            vehicle_no=clean_plate
        )
        if not results['audit_order']['success']:
            results['errors'].append(f"稽核工单查询失败: {results['audit_order']['error']}")
        
        query_value = pass_id if pass_id else clean_plate
        results['suspected_car'] = self.query_suspected_car(
            vehicle_or_pass_id=query_value,
            start_time=start_time,
            end_time=end_time
        )
        if not results['suspected_car']['success']:
            results['errors'].append(f"疑难车牌追查失败: {results['suspected_car']['error']}")
        
        return results
    
    def select_images_by_gantry_ids(
        self,
        images: List[Dict],
        gantry_ids: List[str]
    ) -> Dict[str, Optional[Dict]]:
        selected = {
            'first_gantry': None,
            'last_gantry': None
        }
        
        if not images or not gantry_ids:
            return selected
        
        first_gantry_id = gantry_ids[0] if gantry_ids else None
        last_gantry_id = gantry_ids[-1] if len(gantry_ids) > 1 else first_gantry_id
        
        for image in images:
            station_id = image.get('stationId', '')
            
            if first_gantry_id and station_id.startswith(first_gantry_id[:16]):
                if selected['first_gantry'] is None:
                    selected['first_gantry'] = image
            
            if last_gantry_id and station_id.startswith(last_gantry_id[:16]):
                selected['last_gantry'] = image
        
        return selected
    
    @staticmethod
    def extract_image_base64(image_data: Dict) -> Optional[str]:
        big_positive_pic = image_data.get('bigPositivePic', '')
        if big_positive_pic and big_positive_pic.startswith('data:image'):
            parts = big_positive_pic.split(',', 1)
            if len(parts) > 1:
                return parts[1]
        elif big_positive_pic:
            return big_positive_pic
        return None
