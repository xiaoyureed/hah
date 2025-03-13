import importlib
from typing import Type


def create_instance_from_cls_path(class_path: str, *args, **kwargs):
    """Nested class not supported"""
    try:
        # 分割模块路径和类名
        module_path, class_name = class_path.rsplit(".", 1)
        
        # 动态导入模块
        module = importlib.import_module(module_path)
        # or
        # module = __import__(module_path, fromlist=[class_name])

        
        # 获取类对象
        cls: Type = getattr(module, class_name)
        
        # 创建实例
        return cls(*args, **kwargs)
    except (ImportError, AttributeError) as e:
        print(f"Failed to create instance from path {class_path}: {e}")
        raise e
