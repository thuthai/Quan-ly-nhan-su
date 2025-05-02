from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, BooleanField, SelectMultipleField, HiddenField
from wtforms.validators import DataRequired, Length, Optional


class RoleForm(FlaskForm):
    """Form để tạo và chỉnh sửa vai trò"""
    name = StringField('Tên vai trò', validators=[
        DataRequired(message="Tên vai trò là bắt buộc"),
        Length(max=100, message="Tên vai trò không được vượt quá 100 ký tự")
    ])
    description = TextAreaField('Mô tả', validators=[
        Optional(),
        Length(max=255, message="Mô tả không được vượt quá 255 ký tự")
    ])
    is_active = BooleanField('Kích hoạt', default=True)
    permissions = SelectMultipleField('Quyền hạn', coerce=int)
    submit = SubmitField('Lưu')


class RoleEditForm(RoleForm):
    """Form để chỉnh sửa vai trò"""
    role_id = HiddenField('ID')


class UserRoleForm(FlaskForm):
    """Form để gán vai trò cho người dùng"""
    user_id = HiddenField('ID người dùng', validators=[DataRequired()])
    roles = SelectMultipleField('Vai trò', coerce=int)
    submit = SubmitField('Cập nhật vai trò')


class PermissionForm(FlaskForm):
    """Form để tạo và chỉnh sửa quyền"""
    name = StringField('Tên quyền', validators=[
        DataRequired(message="Tên quyền là bắt buộc"),
        Length(max=100, message="Tên quyền không được vượt quá 100 ký tự")
    ])
    code = StringField('Mã quyền', validators=[
        DataRequired(message="Mã quyền là bắt buộc"),
        Length(max=100, message="Mã quyền không được vượt quá 100 ký tự")
    ])
    description = TextAreaField('Mô tả', validators=[
        Optional(),
        Length(max=255, message="Mô tả không được vượt quá 255 ký tự")
    ])
    module = SelectField('Module', choices=[
        ('employee', 'Nhân viên'),
        ('department', 'Phòng ban'),
        ('position', 'Chức vụ'),
        ('attendance', 'Chấm công'),
        ('leave', 'Nghỉ phép'),
        ('salary', 'Lương'),
        ('kpi', 'Đánh giá KPI'),
        ('contract', 'Hợp đồng'),
        ('user', 'Người dùng'),
        ('notification', 'Thông báo'),
        ('permission', 'Phân quyền'),
        ('asset', 'Tài sản'),
        ('recruitment', 'Tuyển dụng'),
        ('other', 'Khác')
    ])
    submit = SubmitField('Lưu')


class PermissionEditForm(PermissionForm):
    """Form để chỉnh sửa quyền"""
    permission_id = HiddenField('ID')
    code = StringField('Mã quyền', render_kw={'readonly': True}, validators=[
        DataRequired(message="Mã quyền là bắt buộc"),
        Length(max=100, message="Mã quyền không được vượt quá 100 ký tự")
    ])