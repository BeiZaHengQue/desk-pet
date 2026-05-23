import os
import random


class ResourceManager:
    STATE_DIR_MAP = {
        "idle": "idle",
        "move": "move",
        "drag": "drag",
        "interact": "click"
    }

    @classmethod
    def _get_assets_path(cls) -> str:
        """获取资源总目录绝对路径"""
        return os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets"))

    @classmethod
    def get_host_gif(cls, scene_name: str) -> str:
        """根据场景名称去文件夹随机抓取一个 GIF"""
        base_path = cls._get_assets_path()
        dir_name = cls.STATE_DIR_MAP.get(scene_name, "idle")
        target_dir = os.path.join(base_path, "host", dir_name)
        
        if not os.path.exists(target_dir) or not os.listdir(target_dir):
            target_dir = os.path.join(base_path, "host", "idle")
            
        gifs = [f for f in os.listdir(target_dir) if f.endswith('.gif')]
        if not gifs:
            print(f"[警告] 目录内无有效 gif 文件: {target_dir}")
            return ""
            
        return os.path.join(target_dir, random.choice(gifs))

    @classmethod
    def get_soul_text(cls, text_type: str) -> str:
        """
        根据文本类型获取对应的文本文件绝对路径
        """
        base_path = cls._get_assets_path()
        return os.path.normpath(os.path.join(base_path, "soul","text", f"{text_type}.txt"))