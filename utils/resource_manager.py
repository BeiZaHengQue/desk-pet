import os
import random
import logging

logger = logging.getLogger(__name__)

class ResourceManager:
    STATE_DIR_MAP = {
        "idle": "idle",
        "move": "move",
        "drag": "drag",
        "interact": "click"
    }

    @classmethod
    def _get_assets_path(cls) -> str:
        return os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets"))

    @classmethod
    def get_host_gif(cls, scene_name: str) -> str:
        """检索GIF资源"""
        base_path = cls._get_assets_path()
        dir_name = cls.STATE_DIR_MAP.get(scene_name, "idle")
        target_dir = os.path.join(base_path, "host", dir_name)
        hit_fallback = False
        lookup_paths = [target_dir]

        # 检查主目录
        if not os.path.exists(target_dir) or not os.listdir(target_dir):
            fallback_dir = os.path.join(base_path, "host", "idle")
            lookup_paths.append(fallback_dir)
            logger.warning("资源重定向 | 缺失指定动作目录，尝试切入降级待机轨道 | 缺失目录: %s", target_dir)
            target_dir = fallback_dir
            hit_fallback = True

        try:
            gifs = [f for f in os.listdir(target_dir) if f.endswith('.gif')]
            if not gifs:
                logger.error("资源错误 | 查找路径内无有效 GIF 文件 | 查找历史: %s", lookup_paths)
                return ""
            
            selected_gif = random.choice(gifs)
            absolute_path = os.path.join(target_dir, selected_gif)
            
            logger.debug("资源加载 | 类型=[GIF动图] | 命中路径=[%s] | fallback=[%s]", 
                         absolute_path, hit_fallback)
            return absolute_path
        except Exception as e:
            logger.error("资源异常 | 加载 GIF 发生未知文件系统阻碍 | 异常类型=%s | 查找历史=%s", 
                         type(e).__name__, lookup_paths, exc_info=True)
            return ""

    @classmethod
    def get_soul_text(cls, text_type: str) -> str:
        """检索文本资源路径"""
        base_path = cls._get_assets_path()
        target_file = os.path.join(base_path, "soul", "text", f"{text_type}.txt")
        
        if os.path.exists(target_file):
            logger.debug("资源加载 | 类型=[文本配置] | 路径=[%s] | fallback=[False]", target_file)
        else:
            logger.error("资源错误 | 核心文本库配置丢失 | 缺失文件名=[%s.txt] | 查找路径=[%s]", 
                         text_type, target_file)
        return target_file