from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, TextAreaField, FloatField, FileField, HiddenField, IntegerField
from wtforms.validators import DataRequired, Optional, ValidationError, Length, NumberRange
from flask_wtf.file import FileAllowed
from datetime import date, datetime
from models import (
    AssetCategory, AssetStatus, Asset, AssetAssignment, 
    MaintenanceType, MaintenanceStatus, 
    Employee, EmployeeStatus
)


class AssetForm(FlaskForm):
    """Form để tạo hoặc cập nhật tài sản công ty"""
    asset_code = StringField('Mã tài sản', validators=[
        DataRequired(message='Vui lòng nhập mã tài sản'),
        Length(min=3, max=20, message='Mã tài sản phải có từ 3-20 ký tự')
    ])
    name = StringField('Tên tài sản', validators=[
        DataRequired(message='Vui lòng nhập tên tài sản'),
        Length(min=3, max=100, message='Tên tài sản phải có từ 3-100 ký tự')
    ])
    category = SelectField('Loại tài sản', choices=[
        (cat.name, cat.value) for cat in AssetCategory
    ], validators=[DataRequired(message='Vui lòng chọn loại tài sản')])
    status = SelectField('Trạng thái', choices=[
        (s.name, s.value) for s in AssetStatus
    ], validators=[DataRequired(message='Vui lòng chọn trạng thái')])
    serial_number = StringField('Số serial', validators=[Optional()])
    purchase_date = DateField('Ngày mua', validators=[Optional()])
    purchase_price = FloatField('Giá mua', validators=[
        Optional(),
        NumberRange(min=0, message='Giá mua không được âm')
    ])
    warranty_expiry = DateField('Hạn bảo hành', validators=[Optional()])
    description = TextAreaField('Mô tả', validators=[Optional()])
    notes = TextAreaField('Ghi chú', validators=[Optional()])
    image = FileField('Hình ảnh', validators=[
        Optional(),
        FileAllowed(['jpg', 'png', 'jpeg'], 'Chỉ chấp nhận file hình ảnh')
    ])

    def validate_asset_code(self, asset_code):
        asset = Asset.query.filter_by(asset_code=asset_code.data).first()
        if asset and (not hasattr(self, 'asset_id') or asset.id != self.asset_id.data):
            raise ValidationError('Mã tài sản đã tồn tại.')


class AssetEditForm(AssetForm):
    """Form để chỉnh sửa tài sản"""
    asset_id = HiddenField('ID')


class AssetAssignmentForm(FlaskForm):
    """Form để bàn giao tài sản cho nhân viên"""
    asset_id = SelectField('Tài sản', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn tài sản')
    ])
    employee_id = SelectField('Nhân viên', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn nhân viên')
    ])
    assigned_date = DateField('Ngày bàn giao', validators=[
        DataRequired(message='Vui lòng chọn ngày bàn giao')
    ], default=date.today)
    condition_on_assignment = TextAreaField('Tình trạng khi bàn giao', validators=[Optional()])
    notes = TextAreaField('Ghi chú', validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super(AssetAssignmentForm, self).__init__(*args, **kwargs)
        # Lấy danh sách tài sản có thể bàn giao (sẵn sàng sử dụng)
        self.asset_id.choices = [(a.id, f"{a.asset_code} - {a.name}") for a in 
                                Asset.query.filter_by(status=AssetStatus.AVAILABLE).all()]
        # Lấy danh sách nhân viên đang làm việc
        self.employee_id.choices = [(e.id, f"{e.employee_code} - {e.full_name}") for e in 
                                  Employee.query.filter_by(status=EmployeeStatus.ACTIVE).all()]


class AssetReturnForm(FlaskForm):
    """Form để nhận lại tài sản từ nhân viên"""
    assignment_id = HiddenField('ID bàn giao')
    return_date = DateField('Ngày trả', validators=[
        DataRequired(message='Vui lòng chọn ngày trả')
    ], default=date.today)
    condition_on_return = TextAreaField('Tình trạng khi trả', validators=[Optional()])
    notes = TextAreaField('Ghi chú', validators=[Optional()])


class AssetMaintenanceForm(FlaskForm):
    """Form để tạo lịch bảo trì tài sản"""
    asset_id = SelectField('Tài sản', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn tài sản')
    ])
    maintenance_date = DateField('Ngày bảo trì', validators=[
        DataRequired(message='Vui lòng chọn ngày bảo trì')
    ], default=date.today)
    maintenance_type = SelectField('Loại bảo trì', choices=[
        (t.name, t.value) for t in MaintenanceType
    ], validators=[DataRequired(message='Vui lòng chọn loại bảo trì')])
    performed_by = StringField('Thực hiện bởi', validators=[Optional()])
    cost = FloatField('Chi phí', validators=[
        Optional(),
        NumberRange(min=0, message='Chi phí không được âm')
    ])
    description = TextAreaField('Mô tả', validators=[Optional()])
    status = SelectField('Trạng thái', choices=[
        (s.name, s.value) for s in MaintenanceStatus
    ], validators=[DataRequired(message='Vui lòng chọn trạng thái')])

    def __init__(self, *args, **kwargs):
        super(AssetMaintenanceForm, self).__init__(*args, **kwargs)
        # Lấy tất cả tài sản
        self.asset_id.choices = [(a.id, f"{a.asset_code} - {a.name}") for a in Asset.query.all()]


class AssetFilterForm(FlaskForm):
    """Form để lọc danh sách tài sản"""
    keyword = StringField('Từ khóa', validators=[Optional()])
    category = SelectField('Loại tài sản', validators=[Optional()])
    status = SelectField('Trạng thái', validators=[Optional()])
    purchase_date_from = DateField('Ngày mua từ', validators=[Optional()])
    purchase_date_to = DateField('Đến ngày', validators=[Optional()])
    price_min = FloatField('Giá từ', validators=[Optional()])
    price_max = FloatField('Đến', validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super(AssetFilterForm, self).__init__(*args, **kwargs)
        self.category.choices = [('', 'Tất cả loại')] + [(cat.name, cat.value) for cat in AssetCategory]
        self.status.choices = [('', 'Tất cả trạng thái')] + [(s.name, s.value) for s in AssetStatus]

    def validate_price_range(self):
        if self.price_min.data is not None and self.price_max.data is not None:
            if self.price_min.data > self.price_max.data:
                self.price_max.errors.append('Giá tối đa phải lớn hơn giá tối thiểu.')
                return False
        return True

    def validate_date_range(self):
        if self.purchase_date_from.data and self.purchase_date_to.data:
            if self.purchase_date_from.data > self.purchase_date_to.data:
                self.purchase_date_to.errors.append('Ngày kết thúc phải sau ngày bắt đầu.')
                return False
        return True