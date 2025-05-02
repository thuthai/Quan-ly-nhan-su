from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SelectField, TextAreaField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional

class NotificationEmailForm(FlaskForm):
    """Form để thêm email mới vào danh sách nhận thông báo"""
    email = StringField('Địa chỉ email', validators=[
        DataRequired(message="Địa chỉ email là bắt buộc"),
        Email(message="Địa chỉ email không hợp lệ"),
        Length(max=120, message="Địa chỉ email không được vượt quá 120 ký tự")
    ])
    name = StringField('Tên người nhận', validators=[
        Optional(),
        Length(max=100, message="Tên không được vượt quá 100 ký tự")
    ])
    notification_types = SelectField('Loại thông báo', choices=[
        ('all', 'Tất cả thông báo'),
        ('contracts', 'Chỉ thông báo hợp đồng'),
        ('employees', 'Chỉ thông báo nhân viên'),
        ('performance', 'Chỉ thông báo đánh giá hiệu suất')
    ], default='all')
    is_active = BooleanField('Kích hoạt', default=True)
    submit = SubmitField('Thêm email')


class NotificationEmailEditForm(FlaskForm):
    """Form để chỉnh sửa email nhận thông báo"""
    email_id = HiddenField('ID')
    email = StringField('Địa chỉ email', validators=[
        DataRequired(message="Địa chỉ email là bắt buộc"),
        Email(message="Địa chỉ email không hợp lệ"),
        Length(max=120, message="Địa chỉ email không được vượt quá 120 ký tự")
    ])
    name = StringField('Tên người nhận', validators=[
        Optional(),
        Length(max=100, message="Tên không được vượt quá 100 ký tự")
    ])
    notification_types = SelectField('Loại thông báo', choices=[
        ('all', 'Tất cả thông báo'),
        ('contracts', 'Chỉ thông báo hợp đồng'),
        ('employees', 'Chỉ thông báo nhân viên'),
        ('performance', 'Chỉ thông báo đánh giá hiệu suất')
    ])
    is_active = BooleanField('Kích hoạt')
    submit = SubmitField('Cập nhật')


class SendTestEmailForm(FlaskForm):
    """Form để gửi email thử nghiệm"""
    email = StringField('Địa chỉ email nhận', validators=[
        DataRequired(message="Địa chỉ email là bắt buộc"),
        Email(message="Địa chỉ email không hợp lệ")
    ])
    subject = StringField('Tiêu đề', validators=[
        DataRequired(message="Tiêu đề là bắt buộc")
    ], default="Thử nghiệm thông báo từ hệ thống HR")
    message = TextAreaField('Nội dung', validators=[
        DataRequired(message="Nội dung là bắt buộc")
    ], default="Đây là email thử nghiệm từ hệ thống quản lý nhân sự. Nếu bạn nhận được email này, hệ thống thông báo đang hoạt động bình thường.")
    submit = SubmitField('Gửi email thử nghiệm')