from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, SubmitField, HiddenField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional


class NotificationEmailForm(FlaskForm):
    """Form để thêm email nhận thông báo"""
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    name = StringField('Tên người nhận', validators=[Optional(), Length(max=100)])
    is_active = BooleanField('Kích hoạt', default=True)
    notification_types = SelectField('Loại thông báo', choices=[
        ('all', 'Tất cả thông báo'),
        ('contracts', 'Thông báo hợp đồng'),
        ('employees', 'Thông báo nhân viên'),
        ('performance', 'Thông báo đánh giá')
    ], default='all')
    submit = SubmitField('Lưu')


class NotificationEmailEditForm(NotificationEmailForm):
    """Form để chỉnh sửa email nhận thông báo"""
    email_id = HiddenField('ID')


class SendTestEmailForm(FlaskForm):
    """Form để gửi email thử nghiệm"""
    email = StringField('Email nhận', validators=[DataRequired(), Email(), Length(max=120)])
    subject = StringField('Tiêu đề', validators=[DataRequired(), Length(max=255)], 
                          default='Thư thử nghiệm từ hệ thống quản lý nhân sự')
    message = TextAreaField('Nội dung', validators=[DataRequired()], 
                           default='Đây là thư thử nghiệm từ hệ thống quản lý nhân sự. Nếu bạn nhận được thư này, cấu hình gửi mail đã hoạt động thành công.')
    submit = SubmitField('Gửi thử nghiệm')