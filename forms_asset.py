from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, FloatField, TextAreaField, FileField, HiddenField, BooleanField
from wtforms.validators import DataRequired, Optional, NumberRange, Length
from flask_wtf.file import FileAllowed
from datetime import date
from models import (
    AssetCategory, AssetStatus, MaintenanceType, 
    MaintenanceStatus, Asset, Employee, EmployeeStatus,
    AssetCategoryModel
)


class AssetCategoryForm(FlaskForm):
    """Form để tạo hoặc cập nhật danh mục tài sản"""
    name = StringField('Tên danh mục', validators=[
        DataRequired(message='Vui lòng nhập tên danh mục'),
        Length(min=2, max=100, message='Tên danh mục phải có độ dài từ 2-100 ký tự')
    ])
    description = TextAreaField('Mô tả', validators=[Optional()])
    is_active = BooleanField('Kích hoạt', default=True)


class AssetCategoryEditForm(AssetCategoryForm):
    """Form để chỉnh sửa danh mục tài sản"""
    id = HiddenField('ID')


class AssetForm(FlaskForm):
    """Form để tạo hoặc cập nhật tài sản"""
    asset_code = StringField('Mã tài sản', validators=[
        DataRequired(message='Vui lòng nhập mã tài sản'),
        Length(min=2, max=20, message='Mã tài sản phải có độ dài từ 2-20 ký tự')
    ])
    name = StringField('Tên tài sản', validators=[
        DataRequired(message='Vui lòng nhập tên tài sản'),
        Length(min=3, max=100, message='Tên tài sản phải có độ dài từ 3-100 ký tự')
    ])
    category = SelectField('Danh mục', choices=[
        (c.name, c.value) for c in AssetCategory
    ], validators=[DataRequired(message='Vui lòng chọn danh mục')])
    status = SelectField('Trạng thái', choices=[
        (s.name, s.value) for s in AssetStatus
    ], validators=[DataRequired(message='Vui lòng chọn trạng thái')])
    serial_number = StringField('Số sê-ri', validators=[Optional()])
    purchase_date = DateField('Ngày mua', validators=[Optional()], default=date.today)
    purchase_price = FloatField('Giá mua', validators=[
        Optional(),
        NumberRange(min=0, message='Giá không được âm')
    ])
    warranty_expiry = DateField('Hết hạn bảo hành', validators=[Optional()])
    warranty_info = TextAreaField('Thông tin bảo hành', validators=[Optional()])
    department_id = SelectField('Phòng ban quản lý', coerce=int, validators=[Optional()])
    assignee_id = SelectField('Người đang sử dụng', coerce=int, validators=[Optional()])
    description = TextAreaField('Mô tả', validators=[Optional()])
    notes = TextAreaField('Ghi chú', validators=[Optional()])
    image = FileField('Hình ảnh', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Chỉ chấp nhận file hình ảnh (jpg, jpeg, png)')
    ])
    
    def __init__(self, *args, **kwargs):
        super(AssetForm, self).__init__(*args, **kwargs)
        from models import Department, Employee
        
        # Lấy danh sách phòng ban (chỉ khi có dữ liệu)
        departments = Department.query.all()
        if departments:
            self.department_id.choices = [(d.id, d.name) for d in departments]
        else:
            self.department_id.choices = [(0, '-- Không có phòng ban --')]
            
        # Lấy danh sách nhân viên (chỉ khi có dữ liệu)
        employees = Employee.query.all()
        if employees:
            self.assignee_id.choices = [(0, '-- Không có người sử dụng --')] + [(e.id, f"{e.employee_code} - {e.full_name}") for e in employees]
        else:
            self.assignee_id.choices = [(0, '-- Không có người sử dụng --')]


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
    condition_on_assignment = TextAreaField('Tình trạng khi bàn giao', validators=[
        DataRequired(message='Vui lòng nhập tình trạng tài sản khi bàn giao')
    ])
    notes = TextAreaField('Ghi chú', validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super(AssetAssignmentForm, self).__init__(*args, **kwargs)
        # Lấy danh sách tài sản khả dụng
        self.asset_id.choices = [(a.id, f"{a.asset_code} - {a.name}") for a in 
                               Asset.query.filter_by(status=AssetStatus.AVAILABLE).all()]
        # Lấy danh sách nhân viên đang làm việc
        self.employee_id.choices = [(e.id, f"{e.employee_code} - {e.full_name}") for e in 
                                  Employee.query.filter_by(status=EmployeeStatus.ACTIVE).all()]


class AssetReturnForm(FlaskForm):
    """Form để nhận lại tài sản từ nhân viên"""
    assignment_id = HiddenField('ID')
    return_date = DateField('Ngày trả', validators=[
        DataRequired(message='Vui lòng chọn ngày trả')
    ], default=date.today)
    condition_on_return = TextAreaField('Tình trạng khi trả', validators=[
        DataRequired(message='Vui lòng nhập tình trạng tài sản khi trả')
    ])
    notes = TextAreaField('Ghi chú', validators=[Optional()])


class AssetMaintenanceForm(FlaskForm):
    """Form để tạo hoặc cập nhật bảo trì tài sản"""
    asset_id = SelectField('Tài sản', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn tài sản')
    ])
    maintenance_date = DateField('Ngày bảo trì', validators=[
        DataRequired(message='Vui lòng chọn ngày bảo trì')
    ], default=date.today)
    maintenance_type = SelectField('Loại bảo trì', choices=[
        (t.name, t.value) for t in MaintenanceType
    ], validators=[DataRequired(message='Vui lòng chọn loại bảo trì')])
    performed_by = StringField('Người thực hiện', validators=[
        DataRequired(message='Vui lòng nhập người thực hiện')
    ])
    cost = FloatField('Chi phí', validators=[
        Optional(),
        NumberRange(min=0, message='Chi phí không được âm')
    ], default=0)
    description = TextAreaField('Mô tả bảo trì', validators=[
        DataRequired(message='Vui lòng nhập mô tả bảo trì')
    ])
    status = SelectField('Trạng thái', choices=[
        (s.name, s.value) for s in MaintenanceStatus
    ], validators=[DataRequired(message='Vui lòng chọn trạng thái')])

    def __init__(self, *args, **kwargs):
        super(AssetMaintenanceForm, self).__init__(*args, **kwargs)
        # Lấy tất cả tài sản
        self.asset_id.choices = [(a.id, f"{a.asset_code} - {a.name}") for a in Asset.query.all()]


class AssetFilterForm(FlaskForm):
    """Form để lọc và tìm kiếm tài sản"""
    keyword = StringField('Từ khóa', validators=[Optional()])
    category = SelectField('Danh mục', validators=[Optional()])
    status = SelectField('Trạng thái', validators=[Optional()])
    purchase_date_from = DateField('Ngày mua từ', validators=[Optional()])
    purchase_date_to = DateField('Ngày mua đến', validators=[Optional()])
    price_min = FloatField('Giá thấp nhất', validators=[Optional(), NumberRange(min=0)])
    price_max = FloatField('Giá cao nhất', validators=[Optional(), NumberRange(min=0)])

    def __init__(self, *args, **kwargs):
        super(AssetFilterForm, self).__init__(*args, **kwargs)
        self.category.choices = [('', 'Tất cả danh mục')] + [(c.name, c.value) for c in AssetCategory]
        self.status.choices = [('', 'Tất cả trạng thái')] + [(s.name, s.value) for s in AssetStatus]

    def validate_price_range(self):
        if self.price_min.data is not None and self.price_max.data is not None:
            if self.price_min.data > self.price_max.data:
                self.price_max.errors.append('Giá cao nhất phải lớn hơn giá thấp nhất.')
                return False
        return True