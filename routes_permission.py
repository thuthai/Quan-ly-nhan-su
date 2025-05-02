from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
import logging
from app import db
from models import User, Role, Permission, user_roles
from forms_permission import RoleForm, RoleEditForm, PermissionForm, PermissionEditForm, UserRoleForm
from utils_permission import permission_required, setup_initial_permissions
from functools import wraps

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Bạn không có quyền truy cập trang này.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return login_required(decorated_function)

permission_bp = Blueprint('permission', __name__, url_prefix='/permissions')


@permission_bp.route('/')
@admin_required
def index():
    """Hiển thị trang tổng quan phân quyền"""
    roles = Role.query.all()
    permissions = Permission.query.all()
    
    # Thống kê
    total_roles = len(roles)
    total_perms = len(permissions)
    total_users = User.query.count()
    
    # Phân loại theo module
    modules = {}
    for perm in permissions:
        if perm.module not in modules:
            modules[perm.module] = 0
        modules[perm.module] += 1
    
    return render_template('permissions/index.html', 
                          roles=roles,
                          permissions=permissions,
                          total_roles=total_roles,
                          total_perms=total_perms,
                          total_users=total_users,
                          modules=modules,
                          title='Quản lý phân quyền')


@permission_bp.route('/setup', methods=['POST'])
@admin_required
def setup():
    """Thiết lập các quyền và vai trò mặc định ban đầu"""
    try:
        setup_initial_permissions()
        flash('Thiết lập quyền mặc định thành công!', 'success')
    except Exception as e:
        logging.error(f"Lỗi khi thiết lập quyền mặc định: {e}")
        flash(f'Có lỗi xảy ra: {str(e)}', 'danger')
    
    return redirect(url_for('permission.index'))


# ---------- QUẢN LÝ VAI TRÒ ----------
@permission_bp.route('/roles')
@permission_required('permission_view')
def role_list():
    """Hiển thị danh sách vai trò"""
    roles = Role.query.all()
    return render_template('permissions/role_list.html', 
                          roles=roles,
                          title='Danh sách vai trò')


@permission_bp.route('/roles/create', methods=['GET', 'POST'])
@permission_required('permission_manage')
def create_role():
    """Tạo vai trò mới"""
    form = RoleForm()
    
    # Lấy danh sách quyền để hiển thị trong form MultiSelect
    permissions = Permission.query.all()
    form.permissions.choices = [(p.id, f"{p.name} ({p.module})") for p in permissions]
    
    if form.validate_on_submit():
        # Kiểm tra xem vai trò đã tồn tại chưa
        existing = Role.query.filter_by(name=form.name.data).first()
        if existing:
            flash(f'Vai trò "{form.name.data}" đã tồn tại!', 'danger')
            return render_template('permissions/create_role.html', form=form, title='Thêm vai trò mới')
        
        # Tạo vai trò mới
        role = Role(
            name=form.name.data,
            description=form.description.data,
            is_active=form.is_active.data,
            created_by_id=current_user.id
        )
        
        # Thêm các quyền đã chọn
        selected_permissions = Permission.query.filter(Permission.id.in_(form.permissions.data)).all()
        for permission in selected_permissions:
            role.permissions.append(permission)
        
        db.session.add(role)
        db.session.commit()
        
        flash(f'Vai trò "{role.name}" đã được tạo thành công!', 'success')
        return redirect(url_for('permission.role_list'))
    
    return render_template('permissions/create_role.html', 
                          form=form,
                          title='Thêm vai trò mới')


@permission_bp.route('/roles/<int:id>/edit', methods=['GET', 'POST'])
@permission_required('permission_manage')
def edit_role(id):
    """Chỉnh sửa vai trò"""
    role = Role.query.get_or_404(id)
    form = RoleEditForm(obj=role)
    
    # Lấy danh sách quyền để hiển thị trong form MultiSelect
    permissions = Permission.query.all()
    form.permissions.choices = [(p.id, f"{p.name} ({p.module})") for p in permissions]
    
    if request.method == 'GET':
        # Đặt các giá trị mặc định cho form
        form.role_id.data = role.id
        form.permissions.data = [p.id for p in role.permissions]
    
    if form.validate_on_submit():
        # Kiểm tra xem tên mới đã tồn tại chưa (nếu khác tên hiện tại)
        if form.name.data != role.name:
            existing = Role.query.filter_by(name=form.name.data).first()
            if existing:
                flash(f'Vai trò "{form.name.data}" đã tồn tại!', 'danger')
                return render_template('permissions/edit_role.html', form=form, role=role, title=f'Chỉnh sửa vai trò: {role.name}')
        
        # Cập nhật thông tin vai trò
        role.name = form.name.data
        role.description = form.description.data
        role.is_active = form.is_active.data
        
        # Cập nhật quyền
        role.permissions = []
        selected_permissions = Permission.query.filter(Permission.id.in_(form.permissions.data)).all()
        for permission in selected_permissions:
            role.permissions.append(permission)
        
        db.session.commit()
        
        flash(f'Vai trò "{role.name}" đã được cập nhật thành công!', 'success')
        return redirect(url_for('permission.role_list'))
    
    return render_template('permissions/edit_role.html', 
                          form=form,
                          role=role,
                          title=f'Chỉnh sửa vai trò: {role.name}')


@permission_bp.route('/roles/<int:id>/delete', methods=['POST'])
@permission_required('permission_manage')
def delete_role(id):
    """Xóa vai trò"""
    role = Role.query.get_or_404(id)
    
    # Kiểm tra xem vai trò có đang được sử dụng không
    if role.users.count() > 0:
        flash(f'Không thể xóa vai trò "{role.name}" vì đang được sử dụng bởi {role.users.count()} người dùng!', 'danger')
        return redirect(url_for('permission.role_list'))
    
    try:
        db.session.delete(role)
        db.session.commit()
        flash(f'Vai trò "{role.name}" đã được xóa thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Lỗi khi xóa vai trò: {e}")
        flash(f'Có lỗi xảy ra khi xóa vai trò: {str(e)}', 'danger')
    
    return redirect(url_for('permission.role_list'))


# ---------- QUẢN LÝ QUYỀN ----------
@permission_bp.route('/permissions/list')
@permission_required('permission_view')
def permission_list():
    """Hiển thị danh sách quyền"""
    permissions = Permission.query.all()
    
    # Nhóm quyền theo module
    permissions_by_module = {}
    for perm in permissions:
        if perm.module not in permissions_by_module:
            permissions_by_module[perm.module] = []
        permissions_by_module[perm.module].append(perm)
    
    return render_template('permissions/permission_list.html', 
                          permissions=permissions,
                          permissions_by_module=permissions_by_module,
                          title='Danh sách quyền')


@permission_bp.route('/permissions/create', methods=['GET', 'POST'])
@permission_required('permission_manage')
def create_permission():
    """Tạo quyền mới"""
    form = PermissionForm()
    
    if form.validate_on_submit():
        # Kiểm tra xem quyền đã tồn tại chưa
        existing = Permission.query.filter_by(code=form.code.data).first()
        if existing:
            flash(f'Mã quyền "{form.code.data}" đã tồn tại!', 'danger')
            return render_template('permissions/create_permission.html', form=form, title='Thêm quyền mới')
        
        # Tạo quyền mới
        permission = Permission(
            name=form.name.data,
            code=form.code.data,
            description=form.description.data,
            module=form.module.data
        )
        
        db.session.add(permission)
        db.session.commit()
        
        flash(f'Quyền "{permission.name}" đã được tạo thành công!', 'success')
        return redirect(url_for('permission.permission_list'))
    
    return render_template('permissions/create_permission.html', 
                          form=form,
                          title='Thêm quyền mới')


@permission_bp.route('/permissions/<int:id>/edit', methods=['GET', 'POST'])
@permission_required('permission_manage')
def edit_permission(id):
    """Chỉnh sửa quyền"""
    permission = Permission.query.get_or_404(id)
    form = PermissionEditForm(obj=permission)
    
    if request.method == 'GET':
        # Đặt các giá trị mặc định cho form
        form.permission_id.data = permission.id
    
    if form.validate_on_submit():
        # Cập nhật thông tin quyền (không thay đổi code)
        permission.name = form.name.data
        permission.description = form.description.data
        permission.module = form.module.data
        
        db.session.commit()
        
        flash(f'Quyền "{permission.name}" đã được cập nhật thành công!', 'success')
        return redirect(url_for('permission.permission_list'))
    
    return render_template('permissions/edit_permission.html', 
                          form=form,
                          permission=permission,
                          title=f'Chỉnh sửa quyền: {permission.name}')


@permission_bp.route('/permissions/<int:id>/delete', methods=['POST'])
@permission_required('permission_manage')
def delete_permission(id):
    """Xóa quyền"""
    permission = Permission.query.get_or_404(id)
    
    # Kiểm tra xem quyền có đang được sử dụng không
    if permission.roles.count() > 0:
        flash(f'Không thể xóa quyền "{permission.name}" vì đang được sử dụng bởi {permission.roles.count()} vai trò!', 'danger')
        return redirect(url_for('permission.permission_list'))
    
    try:
        db.session.delete(permission)
        db.session.commit()
        flash(f'Quyền "{permission.name}" đã được xóa thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Lỗi khi xóa quyền: {e}")
        flash(f'Có lỗi xảy ra khi xóa quyền: {str(e)}', 'danger')
    
    return redirect(url_for('permission.permission_list'))


# ---------- PHÂN QUYỀN NGƯỜI DÙNG ----------
@permission_bp.route('/users')
@permission_required('permission_view')
def user_list():
    """Hiển thị danh sách người dùng để phân quyền"""
    users = User.query.all()
    return render_template('permissions/user_list.html', 
                          users=users,
                          title='Phân quyền người dùng')


@permission_bp.route('/users/<int:id>/roles', methods=['GET', 'POST'])
@permission_required('permission_manage')
def user_roles(id):
    """Gán vai trò cho người dùng"""
    user = User.query.get_or_404(id)
    form = UserRoleForm()
    
    # Lấy danh sách vai trò để hiển thị trong form MultiSelect
    roles = Role.query.filter_by(is_active=True).all()
    form.roles.choices = [(r.id, r.name) for r in roles]
    
    if request.method == 'GET':
        # Đặt các giá trị mặc định cho form
        form.user_id.data = user.id
        form.roles.data = [r.id for r in user.custom_roles]
    
    if form.validate_on_submit():
        # Cập nhật vai trò cho người dùng
        # Xóa tất cả vai trò hiện tại
        for role in user.custom_roles:
            user.custom_roles.remove(role)
        
        # Thêm các vai trò mới đã chọn
        selected_roles = Role.query.filter(Role.id.in_(form.roles.data)).all()
        for role in selected_roles:
            user.custom_roles.append(role)
        
        db.session.commit()
        
        flash(f'Vai trò của người dùng "{user.username}" đã được cập nhật thành công!', 'success')
        return redirect(url_for('permission.user_list'))
    
    return render_template('permissions/user_roles.html', 
                          form=form,
                          user=user,
                          title=f'Phân quyền cho người dùng: {user.username}')


@permission_bp.route('/users/<int:id>/permissions')
@permission_required('permission_view')
def user_permissions(id):
    """Hiển thị danh sách quyền của người dùng"""
    user = User.query.get_or_404(id)
    
    # Lấy tất cả quyền của người dùng
    permissions = user.get_all_permissions()
    
    # Nhóm quyền theo module
    permissions_by_module = {}
    for perm in permissions:
        if perm.module not in permissions_by_module:
            permissions_by_module[perm.module] = []
        permissions_by_module[perm.module].append(perm)
    
    return render_template('permissions/user_permissions.html', 
                          user=user,
                          permissions=permissions,
                          permissions_by_module=permissions_by_module,
                          title=f'Quyền của người dùng: {user.username}')