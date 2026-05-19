"""
部门管理路由
包含部门的增删改查接口
"""

import logging

import pymysql
from fastapi import APIRouter, Depends

from core.dependencies import get_db
from core.models import DepartmentCreateRequest, DepartmentUpdateRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/departments/")
async def get_departments(db=Depends(get_db)):
    """获取所有部门列表（树形结构）"""
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM departments ORDER BY sort_order")
            departments = cursor.fetchall()
            
            # 构建部门树
            dept_tree = build_department_tree(departments)
            
            return {
                "code": 200,
                "message": "success",
                "data": dept_tree
            }
    except Exception as e:
        logger.error(f"获取部门列表失败: {e}")
        return {"code": 500, "message": "获取部门列表失败"}


def build_department_tree(departments: list, parent_id: int = 0) -> list:
    """
    构建部门树结构
    
    Args:
        departments: 部门列表
        parent_id: 父级ID
    
    Returns:
        树形结构的部门列表
    """
    tree = []
    
    for dept in departments:
        if dept.get('parent_id') == parent_id:
            node = dept.copy()
            children = build_department_tree(departments, dept['id'])
            if children:
                node['children'] = children
            tree.append(node)
    
    return tree


@router.post("/api/departments/")
async def create_department(department: DepartmentCreateRequest, db=Depends(get_db)):
    """创建新部门"""
    try:
        with db.cursor() as cursor:
            # 插入新部门
            cursor.execute(
                "INSERT INTO departments (name, parent_id, sort_order, status) VALUES (%s, %s, %s, %s)",
                (department.name, department.parent_id, department.sort_order, department.status)
            )
            db.commit()
            
            return {"code": 200, "message": "部门创建成功"}
    except Exception as e:
        logger.error(f"创建部门失败: {e}")
        return {"code": 500, "message": "创建部门失败"}


@router.put("/api/departments/{department_id}")
async def update_department(department_id: int, department: DepartmentUpdateRequest, db=Depends(get_db)):
    """更新部门信息"""
    try:
        with db.cursor() as cursor:
            # 检查部门是否存在
            cursor.execute("SELECT id FROM departments WHERE id = %s", (department_id,))
            if not cursor.fetchone():
                return {"code": 404, "message": "部门不存在"}
            
            # 更新部门信息
            cursor.execute(
                "UPDATE departments SET name=%s, parent_id=%s, sort_order=%s, status=%s WHERE id=%s",
                (department.name, department.parent_id, department.sort_order, department.status, department_id)
            )
            db.commit()
            
            return {"code": 200, "message": "部门更新成功"}
    except Exception as e:
        logger.error(f"更新部门失败: {e}")
        return {"code": 500, "message": "更新部门失败"}


@router.delete("/api/departments/{department_id}")
async def delete_department(department_id: int, db=Depends(get_db)):
    """删除部门（同时删除子部门）"""
    try:
        with db.cursor() as cursor:
            # 检查部门是否存在
            cursor.execute("SELECT id FROM departments WHERE id = %s", (department_id,))
            if not cursor.fetchone():
                return {"code": 404, "message": "部门不存在"}
            
            # 删除子部门
            cursor.execute("DELETE FROM departments WHERE parent_id = %s", (department_id,))
            
            # 删除当前部门
            cursor.execute("DELETE FROM departments WHERE id = %s", (department_id,))
            db.commit()
            
            return {"code": 200, "message": "部门删除成功"}
    except Exception as e:
        logger.error(f"删除部门失败: {e}")
        return {"code": 500, "message": "删除部门失败"}
