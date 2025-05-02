from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def permission_required(permission_code):
    """
    Decorator kiểm tra quyền truy cập trước khi cho phép truy cập vào route
    
    Args:
        permission_code (str): Mã quyền cần kiểm tra
    
    Returns:
        function: Decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Admin luôn có quyền truy cập tất cả các tính năng
            if current_user.is_admin():
                return f(*args, **kwargs)
                
            # Nếu người dùng không có quyền, chuyển hướng đến trang chủ
            if not current_user.has_permission(permission_code):
                flash('Bạn không có quyền truy cập chức năng này.', 'danger')
                return redirect(url_for('index'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def role_required(role_name):
    """
    Decorator kiểm tra vai trò trước khi cho phép truy cập vào route
    
    Args:
        role_name (str): Tên vai trò cần kiểm tra
    
    Returns:
        function: Decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Admin luôn có tất cả các vai trò
            if current_user.is_admin():
                return f(*args, **kwargs)
                
            # Nếu người dùng không có vai trò, chuyển hướng đến trang chủ
            if not current_user.has_role(role_name):
                flash('Bạn không có vai trò cần thiết để truy cập chức năng này.', 'danger')
                return redirect(url_for('index'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Danh sách các quyền mặc định trong hệ thống 
DEFAULT_PERMISSIONS = [
    # Quyền quản lý nhân viên
    {
        'code': 'employee_view',
        'name': 'Xem danh sách nhân viên',
        'module': 'employee',
        'description': 'Xem danh sách và thông tin nhân viên'
    },
    {
        'code': 'employee_create',
        'name': 'Thêm nhân viên mới',
        'module': 'employee',
        'description': 'Thêm nhân viên mới vào hệ thống'
    },
    {
        'code': 'employee_edit',
        'name': 'Chỉnh sửa thông tin nhân viên',
        'module': 'employee',
        'description': 'Chỉnh sửa thông tin nhân viên hiện có'
    },
    {
        'code': 'employee_delete',
        'name': 'Xóa nhân viên',
        'module': 'employee',
        'description': 'Xóa nhân viên khỏi hệ thống'
    },
    
    # Quyền quản lý phòng ban
    {
        'code': 'department_view',
        'name': 'Xem phòng ban',
        'module': 'department',
        'description': 'Xem danh sách và thông tin phòng ban'
    },
    {
        'code': 'department_create',
        'name': 'Thêm phòng ban',
        'module': 'department',
        'description': 'Thêm phòng ban mới vào hệ thống'
    },
    {
        'code': 'department_edit',
        'name': 'Chỉnh sửa phòng ban',
        'module': 'department',
        'description': 'Chỉnh sửa thông tin phòng ban'
    },
    {
        'code': 'department_delete',
        'name': 'Xóa phòng ban',
        'module': 'department',
        'description': 'Xóa phòng ban khỏi hệ thống'
    },
    
    # Quyền quản lý chức vụ
    {
        'code': 'position_view',
        'name': 'Xem chức vụ',
        'module': 'position',
        'description': 'Xem danh sách và thông tin chức vụ'
    },
    {
        'code': 'position_create',
        'name': 'Thêm chức vụ',
        'module': 'position',
        'description': 'Thêm chức vụ mới vào hệ thống'
    },
    {
        'code': 'position_edit',
        'name': 'Chỉnh sửa chức vụ',
        'module': 'position',
        'description': 'Chỉnh sửa thông tin chức vụ'
    },
    {
        'code': 'position_delete',
        'name': 'Xóa chức vụ',
        'module': 'position',
        'description': 'Xóa chức vụ khỏi hệ thống'
    },
    
    # Quyền chấm công
    {
        'code': 'attendance_view',
        'name': 'Xem báo cáo chấm công',
        'module': 'attendance',
        'description': 'Xem báo cáo chấm công của nhân viên'
    },
    {
        'code': 'attendance_manage',
        'name': 'Quản lý chấm công',
        'module': 'attendance',
        'description': 'Quản lý chấm công nhân viên'
    },
    
    # Quyền đơn xin nghỉ phép
    {
        'code': 'leave_request_view',
        'name': 'Xem đơn xin nghỉ phép',
        'module': 'leave',
        'description': 'Xem danh sách đơn xin nghỉ phép'
    },
    {
        'code': 'leave_request_create',
        'name': 'Tạo đơn xin nghỉ phép',
        'module': 'leave',
        'description': 'Tạo đơn xin nghỉ phép mới'
    },
    {
        'code': 'leave_request_approve',
        'name': 'Phê duyệt đơn xin nghỉ phép',
        'module': 'leave',
        'description': 'Phê duyệt hoặc từ chối đơn xin nghỉ phép'
    },
    
    # Quyền quản lý lương
    {
        'code': 'salary_view',
        'name': 'Xem thông tin lương',
        'module': 'salary',
        'description': 'Xem thông tin lương nhân viên'
    },
    {
        'code': 'salary_manage',
        'name': 'Quản lý lương',
        'module': 'salary',
        'description': 'Quản lý thông tin lương nhân viên'
    },
    
    # Quyền đánh giá KPI
    {
        'code': 'kpi_view',
        'name': 'Xem đánh giá KPI',
        'module': 'kpi',
        'description': 'Xem đánh giá KPI nhân viên'
    },
    {
        'code': 'kpi_create',
        'name': 'Tạo đánh giá KPI',
        'module': 'kpi',
        'description': 'Tạo đánh giá KPI mới'
    },
    {
        'code': 'kpi_approve',
        'name': 'Phê duyệt KPI',
        'module': 'kpi',
        'description': 'Phê duyệt đánh giá KPI'
    },
    
    # Quyền quản lý hợp đồng
    {
        'code': 'contract_view',
        'name': 'Xem hợp đồng',
        'module': 'contract',
        'description': 'Xem thông tin hợp đồng'
    },
    {
        'code': 'contract_create',
        'name': 'Tạo hợp đồng',
        'module': 'contract',
        'description': 'Tạo hợp đồng mới'
    },
    {
        'code': 'contract_edit',
        'name': 'Chỉnh sửa hợp đồng',
        'module': 'contract',
        'description': 'Chỉnh sửa thông tin hợp đồng'
    },
    {
        'code': 'contract_terminate',
        'name': 'Chấm dứt hợp đồng',
        'module': 'contract',
        'description': 'Chấm dứt hợp đồng nhân viên'
    },
    
    # Quyền quản lý người dùng
    {
        'code': 'user_view',
        'name': 'Xem người dùng',
        'module': 'user',
        'description': 'Xem danh sách người dùng'
    },
    {
        'code': 'user_create',
        'name': 'Tạo người dùng',
        'module': 'user',
        'description': 'Tạo người dùng mới'
    },
    {
        'code': 'user_edit',
        'name': 'Chỉnh sửa người dùng',
        'module': 'user',
        'description': 'Chỉnh sửa thông tin người dùng'
    },
    {
        'code': 'user_delete',
        'name': 'Xóa người dùng',
        'module': 'user',
        'description': 'Xóa người dùng khỏi hệ thống'
    },
    
    # Quyền quản lý thông báo
    {
        'code': 'notification_view',
        'name': 'Xem thông báo',
        'module': 'notification',
        'description': 'Xem danh sách thông báo'
    },
    {
        'code': 'notification_manage',
        'name': 'Quản lý thông báo',
        'module': 'notification',
        'description': 'Quản lý cấu hình thông báo'
    },
    
    # Quyền phân quyền
    {
        'code': 'permission_view',
        'name': 'Xem phân quyền',
        'module': 'permission',
        'description': 'Xem danh sách phân quyền'
    },
    {
        'code': 'permission_manage',
        'name': 'Quản lý phân quyền',
        'module': 'permission',
        'description': 'Quản lý phân quyền trong hệ thống'
    },
]


# Danh sách các vai trò mặc định trong hệ thống
DEFAULT_ROLES = [
    {
        'name': 'Quản lý nhân sự',
        'description': 'Quản lý toàn bộ hoạt động liên quan đến nhân sự',
        'permissions': [
            'employee_view', 'employee_create', 'employee_edit', 'employee_delete',
            'department_view', 'department_create', 'department_edit',
            'position_view', 'position_create', 'position_edit',
            'attendance_view', 'attendance_manage',
            'leave_request_view', 'leave_request_approve',
            'contract_view', 'contract_create', 'contract_edit', 'contract_terminate',
            'notification_view', 'notification_manage'
        ]
    },
    {
        'name': 'Quản lý lương thưởng',
        'description': 'Quản lý lương và đánh giá nhân viên',
        'permissions': [
            'employee_view',
            'salary_view', 'salary_manage',
            'kpi_view', 'kpi_create', 'kpi_approve'
        ]
    },
    {
        'name': 'Trưởng phòng',
        'description': 'Quản lý phòng ban và nhân viên thuộc phòng',
        'permissions': [
            'employee_view',
            'attendance_view',
            'leave_request_view', 'leave_request_approve',
            'kpi_view', 'kpi_create',
        ]
    },
    {
        'name': 'Nhân viên',
        'description': 'Quyền hạn cơ bản của nhân viên',
        'permissions': [
            'leave_request_create',
        ]
    }
]


def setup_initial_permissions():
    """
    Thiết lập các quyền mặc định ban đầu cho hệ thống
    """
    from app import db
    from models import Permission, Role
    
    # Thêm các quyền mặc định
    for perm_data in DEFAULT_PERMISSIONS:
        # Kiểm tra xem quyền đã tồn tại chưa
        existing_perm = Permission.query.filter_by(code=perm_data['code']).first()
        if not existing_perm:
            perm = Permission(
                name=perm_data['name'],
                code=perm_data['code'],
                description=perm_data['description'],
                module=perm_data['module']
            )
            db.session.add(perm)
    
    db.session.commit()
    
    # Tạo các vai trò mặc định
    for role_data in DEFAULT_ROLES:
        # Kiểm tra xem vai trò đã tồn tại chưa
        existing_role = Role.query.filter_by(name=role_data['name']).first()
        if not existing_role:
            role = Role(
                name=role_data['name'],
                description=role_data['description']
            )
            
            # Thêm các quyền cho vai trò
            for perm_code in role_data['permissions']:
                perm = Permission.query.filter_by(code=perm_code).first()
                if perm:
                    role.permissions.append(perm)
            
            db.session.add(role)
    
    db.session.commit()