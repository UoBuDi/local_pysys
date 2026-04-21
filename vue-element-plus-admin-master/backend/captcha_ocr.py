import base64
import io
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

_ocr_instance = None


def get_ocr_instance():
    global _ocr_instance
    if _ocr_instance is None:
        try:
            import ddddocr
            _ocr_instance = ddddocr.DdddOcr(show_ad=False)
            logger.info("[OCR] ddddocr初始化成功")
        except ImportError:
            logger.error("[OCR] ddddocr未安装，请运行: pip install ddddocr")
            return None
        except Exception as e:
            logger.error(f"[OCR] ddddocr初始化失败: {e}")
            return None
    return _ocr_instance


def recognize_captcha(base64_img: str) -> Tuple[bool, Optional[str], str]:
    """
    识别base64编码的验证码图片
    
    Args:
        base64_img: base64编码的图片字符串
        
    Returns:
        (success, result, message)
        - success: 是否识别成功
        - result: 识别结果（成功时）
        - message: 提示信息
    """
    ocr = get_ocr_instance()
    if not ocr:
        return False, None, "OCR服务未初始化"
    
    try:
        if base64_img.startswith('data:image'):
            base64_img = base64_img.split(',')[1]
        
        img_data = base64.b64decode(base64_img)
        img_bytes = io.BytesIO(img_data)
        
        result = ocr.classification(img_bytes.read())
        
        if result:
            result = result.strip().upper()
            logger.info(f"[OCR] 识别成功: {result}")
            return True, result, "识别成功"
        else:
            logger.warning("[OCR] 识别结果为空")
            return False, None, "识别结果为空"
            
    except Exception as e:
        logger.error(f"[OCR] 识别异常: {e}")
        return False, None, f"识别异常: {str(e)}"
