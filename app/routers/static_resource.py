
import os
from fastapi import APIRouter
from fastapi.responses import FileResponse


router = APIRouter(prefix="/app", tags=["static"])

# {path_name:path} 是一个路径参数，表示将 /app/ 后面的所有路径（包括嵌套路径）传递给 path_name。例如，访问 /app/dashboard 时，path_name 的值将是 dashboard。
# path 类型的参数可以匹配多个路径段（即 path_name 可以包含 /）
@router.get("/{path_name:path}")
def serve_static_resource(path_name: str):
    return FileResponse(os.path.join("dist", "index.html"))
