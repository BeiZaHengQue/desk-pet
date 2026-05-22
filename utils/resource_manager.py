import os
import random

class ResourceManager:
    # 物理文件夹映射映射表
    STATE_DIR_MAP = {
        "idle": "idle",
        "click": "click",
        "interact": "click",  # 将 pet_engine.py 里的旧状态名 "interact" 自动无缝指向新文件夹 "click"
        "drag": "drag",
        "move": "move"
    }

    @classmethod
    def _get_assets_path(cls):
        """动态获取 assets 目录的绝对路径"""
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

    @classmethod
    def get_host_gif(cls, scene_name: str) -> str:
        """
        根据场景名称去文件夹随机抓取一个 GIF
        """
        base_path = cls._get_assets_path()
        
        # 获取映射后的真实文件夹名称，防止传入未知状态导致闪退，默认 idle
        dir_name = cls.STATE_DIR_MAP.get(scene_name, "idle")
        target_dir = os.path.join(base_path, "host", dir_name)
        
        # 如果文件夹不存在或为空，去 fallback 拿素材
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
        
        path_in_soul = os.path.join(base_path,"soul","text", f"{text_type}.txt")
        path_in_assets = os.path.join(base_path, f"{text_type}.txt")
        
        if os.path.exists(path_in_soul):
            return path_in_soul
        if os.path.exists(path_in_assets):
            return path_in_assets
            
        return path_in_soul