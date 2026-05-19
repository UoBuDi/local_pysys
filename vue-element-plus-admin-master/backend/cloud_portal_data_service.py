import requests
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

GUI_SERVICE_URL = "http://127.0.0.1:5000"
BACKEND_URL = "http://127.0.0.1:8000"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cloud_portal_data")

class CloudPortalDataService:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.backend_url = BACKEND_URL

    def get_branch_centers(self) -> Dict[str, Any]:
        url = f"{self.backend_url}/api/cloud-portal/ai-audit/branch-centers"

        try:
            response = requests.post(
                url,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 200:
                centers = result.get('data', [])
                logger.info(f"成功获取分中心列表，共 {len(centers)} 个分中心")
                return {
                    'success': True,
                    'data': centers
                }
            else:
                error_msg = result.get('message', '未知错误')
                logger.error(f"获取分中心列表失败: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
        except requests.exceptions.Timeout:
            logger.error("获取分中心列表超时")
            return {'success': False, 'error': '请求超时'}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"获取分中心列表连接失败: {e}")
            return {'success': False, 'error': '连接失败'}
        except Exception as e:
            logger.error(f"获取分中心列表异常: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_road_sections(self, center_no: str) -> Dict[str, Any]:
        url = f"{self.backend_url}/api/cloud-portal/ai-audit/road-sections"

        try:
            response = requests.post(
                url,
                json={"center_no": center_no},
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 200:
                sections = result.get('data', [])
                logger.info(f"成功获取分中心 {center_no} 的路段列表，共 {len(sections)} 个路段")
                return {
                    'success': True,
                    'data': sections
                }
            else:
                error_msg = result.get('message', '未知错误')
                logger.error(f"获取路段列表失败: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
        except requests.exceptions.Timeout:
            logger.error(f"获取分中心 {center_no} 路段列表超时")
            return {'success': False, 'error': '请求超时'}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"获取路段列表连接失败: {e}")
            return {'success': False, 'error': '连接失败'}
        except Exception as e:
            logger.error(f"获取路段列表异常: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_gantry_list(self, road_section_no: str) -> Dict[str, Any]:
        url = f"{self.backend_url}/api/cloud-portal/ai-audit/gantry-list"

        try:
            response = requests.post(
                url,
                json={"road_section_no": road_section_no},
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 200:
                gantries = result.get('data', [])
                logger.info(f"成功获取路段 {road_section_no} 的门架列表，共 {len(gantries)} 个门架")
                return {
                    'success': True,
                    'data': gantries
                }
            else:
                error_msg = result.get('message', '未知错误')
                logger.error(f"获取门架列表失败: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
        except requests.exceptions.Timeout:
            logger.error(f"获取路段 {road_section_no} 门架列表超时")
            return {'success': False, 'error': '请求超时'}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"获取门架列表连接失败: {e}")
            return {'success': False, 'error': '连接失败'}
        except Exception as e:
            logger.error(f"获取门架列表异常: {e}")
            return {'success': False, 'error': str(e)}
    
    def sync_all_data(self, progress_callback=None) -> Dict[str, Any]:
        result = {
            'success': False,
            'message': '',
            'data': None,
            'executed_at': datetime.now().isoformat(),
            'statistics': {
                'total_centers': 0,
                'total_road_sections': 0,
                'total_gantries': 0,
                'failed_centers': [],
                'failed_sections': []
            }
        }
        
        centers_result = self.get_branch_centers()
        if not centers_result['success']:
            result['message'] = f"获取分中心列表失败: {centers_result.get('error')}"
            return result
        
        centers = centers_result['data']
        result['statistics']['total_centers'] = len(centers)
        
        all_data = {
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_centers': 0,
            'total_road_sections': 0,
            'total_gantries': 0,
            'centers': []
        }
        
        total_gantries = 0
        total_road_sections = 0
        
        for i, center in enumerate(centers):
            center_no = center.get('centerNo')
            center_name = center.get('centerName')
            
            if progress_callback:
                progress_callback({
                    'current': i + 1,
                    'total': len(centers),
                    'center_name': center_name,
                    'status': 'processing'
                })
            
            center_data = {
                'centerNo': center_no,
                'centerName': center_name,
                'road_sections': []
            }
            
            sections_result = self.get_road_sections(center_no)
            if not sections_result['success']:
                logger.warning(f"分中心 {center_name}({center_no}) 获取路段失败: {sections_result.get('error')}")
                result['statistics']['failed_centers'].append({
                    'centerNo': center_no,
                    'centerName': center_name,
                    'error': sections_result.get('error')
                })
                all_data['centers'].append(center_data)
                continue
            
            sections = sections_result['data']
            
            for section in sections:
                road_section_no = section.get('roadSectionNo')
                road_section_name = section.get('roadSectionName')
                
                section_data = {
                    'roadSectionNo': road_section_no,
                    'roadSectionName': road_section_name,
                    'gantries': []
                }
                
                gantries_result = self.get_gantry_list(road_section_no)
                if not gantries_result['success']:
                    logger.warning(f"路段 {road_section_name}({road_section_no}) 获取门架失败: {gantries_result.get('error')}")
                    result['statistics']['failed_sections'].append({
                        'roadSectionNo': road_section_no,
                        'roadSectionName': road_section_name,
                        'centerNo': center_no,
                        'error': gantries_result.get('error')
                    })
                    center_data['road_sections'].append(section_data)
                    continue
                
                gantries = gantries_result['data']
                section_data['gantries'] = gantries
                total_gantries += len(gantries)
                total_road_sections += 1
                
                center_data['road_sections'].append(section_data)
            
            all_data['centers'].append(center_data)
            
            if progress_callback:
                progress_callback({
                    'current': i + 1,
                    'total': len(centers),
                    'center_name': center_name,
                    'status': 'completed'
                })
        
        all_data['total_centers'] = len(centers)
        all_data['total_road_sections'] = total_road_sections
        all_data['total_gantries'] = total_gantries
        
        save_result = self.save_to_json(all_data)
        if not save_result['success']:
            result['message'] = f"数据同步完成但保存失败: {save_result.get('error')}"
            return result
        
        result['success'] = True
        result['message'] = f"成功同步 {len(centers)} 个分中心，{total_road_sections} 个路段，{total_gantries} 个门架"
        result['data'] = all_data
        
        return result
    
    def save_to_json(self, data: Dict[str, Any], filename: str = "cloud_portal_basic_data.json") -> Dict[str, Any]:
        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"数据已保存到: {filepath}")
            return {
                'success': True,
                'filepath': filepath
            }
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def load_from_json(filename: str = "cloud_portal_basic_data.json") -> Optional[Dict[str, Any]]:
        try:
            filepath = os.path.join(OUTPUT_DIR, filename)
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载数据失败: {e}")
            return None


def run_cloud_portal_data_sync(access_token: str, progress_callback=None) -> Dict[str, Any]:
    service = CloudPortalDataService(access_token)
    return service.sync_all_data(progress_callback)


def get_cloud_portal_data() -> Optional[Dict[str, Any]]:
    return CloudPortalDataService.load_from_json()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("云门户数据同步服务模块")
    print("请通过API调用执行数据同步")
