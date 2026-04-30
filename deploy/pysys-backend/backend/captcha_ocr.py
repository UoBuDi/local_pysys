import base64
import logging
import threading
import time
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class CaptchaOCRService:
    """
    统一验证码OCR服务（针对纯数字验证码优化）
    
    特性：
    - 单例模式，全局共享OCR实例
    - 线程安全
    - 针对纯数字验证码优化配置
    - 支持图片预处理（可选）
    - 识别统计功能
    """
    _instance: Optional['CaptchaOCRService'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
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
        self._ocr = None
        self._available = False
        self._stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'total_time': 0.0
        }
        self._stats_lock = threading.Lock()
        self._init_ocr()
    
    def _init_ocr(self) -> None:
        """
        初始化OCR引擎（针对纯数字验证码优化）
        """
        try:
            import ddddocr
            self._ocr = ddddocr.DdddOcr(
                show_ad=False,
                charsets='0123456789',
                ocr_version='v2'
            )
            self._available = True
            logger.info("[CaptchaOCR] OCR引擎初始化成功（纯数字模式）")
        except ImportError:
            self._available = False
            logger.warning("[CaptchaOCR] ddddocr未安装，OCR功能不可用。可通过 pip install ddddocr 安装")
        except Exception as e:
            self._available = False
            logger.error(f"[CaptchaOCR] OCR引擎初始化失败: {e}")
    
    @property
    def available(self) -> bool:
        """OCR功能是否可用"""
        return self._available
    
    def recognize(
        self,
        image_base64: str,
        preprocess: bool = False,
        expected_length: int = 4
    ) -> Dict[str, Any]:
        """
        识别验证码
        
        Args:
            image_base64: Base64编码的图片数据
            preprocess: 是否进行图片预处理
            expected_length: 期望的验证码长度，默认4位
            
        Returns:
            {
                'success': bool,      # 是否成功
                'text': str,          # 识别结果（成功时）
                'elapsed': float,     # 识别耗时（秒）
                'error': str          # 错误信息（失败时）
            }
        """
        if not self._available:
            return {
                'success': False,
                'text': None,
                'elapsed': 0.0,
                'error': 'OCR功能不可用'
            }
        
        start_time = time.time()
        
        try:
            if image_base64.startswith('data:image'):
                image_base64 = image_base64.split(',', 1)[1]
            
            image_data = base64.b64decode(image_base64)
            
            if preprocess:
                image_data = self._preprocess_image(image_data)
            
            result = self._ocr.classification(image_data)
            
            cleaned = ''.join(c for c in result if c.isdigit())
            
            elapsed = time.time() - start_time
            self._update_stats(True, elapsed)
            
            if cleaned and len(cleaned) == expected_length:
                logger.info(f"[OCR] 识别成功 - 结果: {cleaned}, 耗时: {elapsed:.3f}s")
                return {
                    'success': True,
                    'text': cleaned,
                    'elapsed': elapsed,
                    'error': None
                }
            else:
                logger.warning(f"[OCR] 识别结果异常 - 原始: {result}, 清理后: {cleaned}, 期望长度: {expected_length}")
                return {
                    'success': False,
                    'text': cleaned,
                    'elapsed': elapsed,
                    'error': f'识别结果异常: 原始={result}, 清理后={cleaned}'
                }
                
        except Exception as e:
            elapsed = time.time() - start_time
            self._update_stats(False, elapsed)
            logger.error(f"[OCR] 识别异常: {e}")
            return {
                'success': False,
                'text': None,
                'elapsed': elapsed,
                'error': str(e)
            }
    
    def _preprocess_image(self, image_data: bytes) -> bytes:
        """
        图片预处理
        
        处理步骤：
        1. 灰度化
        2. 增强对比度
        """
        try:
            from PIL import Image, ImageEnhance
            import io
            
            img = Image.open(io.BytesIO(image_data))
            
            if img.mode != 'L':
                img = img.convert('L')
            
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)
            
            output = io.BytesIO()
            img.save(output, format='PNG')
            return output.getvalue()
        except ImportError:
            logger.debug("[OCR] Pillow未安装，跳过图片预处理")
            return image_data
        except Exception as e:
            logger.debug(f"[OCR] 图片预处理失败: {e}")
            return image_data
    
    def _update_stats(self, success: bool, elapsed: float) -> None:
        """更新识别统计"""
        with self._stats_lock:
            self._stats['total'] += 1
            self._stats['total_time'] += elapsed
            if success:
                self._stats['success'] += 1
            else:
                self._stats['failed'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取识别统计信息
        
        Returns:
            {
                'total': int,         # 总识别次数
                'success': int,       # 成功次数
                'failed': int,        # 失败次数
                'success_rate': float,# 成功率
                'avg_time': float     # 平均耗时
            }
        """
        with self._stats_lock:
            total = self._stats['total']
            return {
                'total': total,
                'success': self._stats['success'],
                'failed': self._stats['failed'],
                'success_rate': self._stats['success'] / total if total > 0 else 0,
                'avg_time': self._stats['total_time'] / total if total > 0 else 0
            }
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        with self._stats_lock:
            self._stats = {
                'total': 0,
                'success': 0,
                'failed': 0,
                'total_time': 0.0
            }


captcha_ocr = CaptchaOCRService()


def is_ocr_available() -> bool:
    """
    检查OCR功能是否可用
    
    Returns:
        OCR功能是否可用
    """
    return captcha_ocr.available


def recognize_captcha(base64_img: str, preprocess: bool = False) -> Tuple[bool, Optional[str], str]:
    """
    识别base64编码的验证码图片
    
    Args:
        base64_img: base64编码的图片字符串
        preprocess: 是否进行图片预处理
        
    Returns:
        (success, result, message)
        - success: 是否识别成功
        - result: 识别结果（成功时）
        - message: 提示信息
    """
    result = captcha_ocr.recognize(base64_img, preprocess=preprocess)
    
    if result['success']:
        return True, result['text'], "识别成功"
    else:
        return False, None, result['error']
