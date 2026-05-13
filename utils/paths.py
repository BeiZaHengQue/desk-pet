import os
import sys


def resource_path(*paths):
    """ 获取资源路径 """

    if getattr(sys, 'frozen', False):
        # 打包后 exe 所在目录
        base_path = os.path.dirname(sys.executable)
    else:
        # 项目根目录
        base_path = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

    return os.path.join(base_path, *paths)