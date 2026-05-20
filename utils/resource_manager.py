import os
import random
from utils.paths import resource_path

class ResourceManager:
    @staticmethod
    def get_host_gif(scene="idle"):
        """
        从 assets/host/<scene> 随机取一个 GIF，失败则去 fallback
        """
        target_path = resource_path("assets", "host", scene)
        fallback_path = resource_path("assets", "host", "fallback")

        # 尝试从目标路径获取
        gif = ResourceManager._pick_random_gif(target_path)
        if gif:
            return gif
        
        # 兜底
        return ResourceManager._pick_random_gif(fallback_path)

    @staticmethod
    def get_soul_text(text_type="idle"):
        """映射文本路径"""
        filename = "idle_sentences.txt" if text_type == "idle" else "interaction_sentences.txt"
        return resource_path("assets", "soul", "text", filename)

    @staticmethod
    def _pick_random_gif(dir_path):
        if not os.path.exists(dir_path):
            return None
        # 过滤
        gifs = [f for f in os.listdir(dir_path) if f.lower().endswith('.gif')]
        if not gifs:
            return None
        return os.path.join(dir_path, random.choice(gifs))