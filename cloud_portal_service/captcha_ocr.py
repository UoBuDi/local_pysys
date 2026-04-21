import base64
import logging
import threading
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

_ocr_instance = None
_ocr_lock = threading.Lock()
_ocr_available = None


def _check_ocr_available() -> bool:
    global _ocr_available
    if _ocr_available is not None:
        return _ocr_available
    
    try:
        import ddddocr
        _ocr_available = True
        logger.info("[OCR] ddddocr库已加载，OCR功能可用")
    except ImportError:
        _ocr_available = False
        logger.warning("[OCR] ddddocr库未安装，OCR功能不可用。可通过 pip install ddddocr 安装")
    
    return _ocr_available


def get_ocr_instance():
    global _ocr_instance
    
    if not _check_ocr_available():
        return None
    
    if _ocr_instance is None:
        with _ocr_lock:
            if _ocr_instance is None:
                try:
                    import ddddocr
                    _ocr_instance = ddddocr.DdddOcr(show_ad=False)
                    logger.info("[OCR] OCR实例初始化成功")
                except Exception as e:
                    logger.error(f"[OCR] OCR实例初始化失败: {e}")
                    return None
    
    return _ocr_instance


def recognize_captcha(image_base64: str) -> Tuple[bool, str, Optional[str]]:
    """
    识别验证码图片
    
    Args:
        image_base64: Base64编码的图片数据
        
    Returns:
        (是否成功, 结果或错误信息, 识别出的文本)
    """
    ocr = get_ocr_instance()
    
    if ocr is None:
        return False, "OCR功能不可用", None
    
    try:
        if image_base64.startswith('data:image'):
            image_base64 = image_base64.split(',', 1)[1]
        
        image_data = base64.b64decode(image_base64)
        
        result = ocr.classification(image_data)
        
        if result:
            cleaned_result = ''.join(c for c in result if c.isalnum())
            logger.info(f"[OCR] 识别成功 - 原始: {result}, 清理后: {cleaned_result}")
            return True, cleaned_result, cleaned_result
        else:
            logger.warning("[OCR] 识别结果为空")
            return False, "无法识别验证码", None
            
    except Exception as e:
        logger.error(f"[OCR] 识别失败: {e}")
        return False, f"OCR识别异常: {str(e)}", None


def is_ocr_available() -> bool:
    """
    检查OCR功能是否可用
    
    Returns:
        OCR功能是否可用
    """
    return _check_ocr_available()


class CaptchaOCR:
    """
    验证码OCR识别器
    """
    
    def __init__(self):
        self._ocr = None
        self._available = False
        self._init_ocr()
    
    def _init_ocr(self) -> None:
        """
        初始化OCR引擎
        """
        try:
            import ddddocr
            self._ocr = ddddocr.DdddOcr(show_ad=False)
            self._available = True
            logger.info("[CaptchaOCR] OCR引擎初始化成功")
        except ImportError:
            self._available = False
            logger.warning("[CaptchaOCR] ddddocr未安装，OCR功能不可用")
        except Exception as e:
            self._available = False
            logger.error(f"[CaptchaOCR] OCR引擎初始化失败: {e}")
    
    @property
    def available(self) -> bool:
        return self._available
    
    def recognize(self, image_base64: str) -> Dict[str, Any]:
        """
        识别验证码
        
        Args:
            image_base64: Base64编码的图片
            
        Returns:
            {
                'success': bool,
                'text': str,  # 识别结果
                'error': str  # 错误信息
            }
        """
        if not self._available:
            return {
                'success': False,
                'text': None,
                'error': 'OCR功能不可用'
            }
        
        try:
            if image_base64.startswith('data:image'):
                image_base64 = image_base64.split(',', 1)[1]
            
            image_data = base64.b64decode(image_base64)
            result = self._ocr.classification(image_data)
            
            if result:
                cleaned = ''.join(c for c in result if c.isalnum())
                return {
                    'success': True,
                    'text': cleaned,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'text': None,
                    'error': '无法识别验证码'
                }
                
        except Exception as e:
            return {
                'success': False,
                'text': None,
                'error': str(e)
            }


captcha_ocr = CaptchaOCR()
