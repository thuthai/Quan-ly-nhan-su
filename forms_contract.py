from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, TextAreaField, FloatField, FileField, HiddenField
from wtforms.validators import DataRequired, Optional, ValidationError, Length, NumberRange
from flask_wtf.file import FileAllowed
from datetime import date, datetime
from models import (
    ContractType, ContractStatus, Contract, ContractAmendment,
    DocumentType, Document, Employee, EmployeeStatus, Department
)


class ContractForm(FlaskForm):
    """Form để tạo hoặc cập nhật hợp đồng lao động"""
    contract_number = StringField('Số hợp đồng', validators=[
        DataRequired(message='Vui lòng nhập số hợp đồng'),
        Length(min=3, max=50, message='Số hợp đồng phải có từ 3-50 ký tự')
    ])
    employee_id = SelectField('Nhân viên', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn nhân viên')
    ])
    contract_type = SelectField('Loại hợp đồng', choices=[
        (t.name, t.value) for t in ContractType
    ], validators=[DataRequired(message='Vui lòng chọn loại hợp đồng')])
    status = SelectField('Trạng thái', choices=[
        (s.name, s.value) for s in ContractStatus
    ], validators=[DataRequired(message='Vui lòng chọn trạng thái')])
    start_date = DateField('Ngày bắt đầu', validators=[
        DataRequired(message='Vui lòng chọn ngày bắt đầu')
    ])
    end_date = DateField('Ngày kết thúc', validators=[Optional()])
    job_title = StringField('Chức danh', validators=[
        DataRequired(message='Vui lòng nhập chức danh')
    ])
    department_id = SelectField('Phòng ban', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn phòng ban')
    ])
    base_salary = FloatField('Lương cơ bản', validators=[
        DataRequired(message='Vui lòng nhập lương cơ bản'),
        NumberRange(min=0, message='Lương không được âm')
    ])
    working_hours = StringField('Giờ làm việc', validators=[Optional()])
    contract_file = FileField('File hợp đồng', validators=[
        Optional(),
        FileAllowed(['pdf', 'doc', 'docx'], 'Chỉ chấp nhận file PDF, DOC hoặc DOCX')
    ])
    signed_date = DateField('Ngày ký', validators=[Optional()])
    notes = TextAreaField('Ghi chú', validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super(ContractForm, self).__init__(*args, **kwargs)
        # Lấy danh sách nhân viên đang làm việc
        self.employee_id.choices = [(e.id, f"{e.employee_code} - {e.full_name}") for e in 
                                  Employee.query.filter_by(status=EmployeeStatus.ACTIVE).all()]
        # Lấy danh sách phòng ban
        self.department_id.choices = [(d.id, d.name) for d in Department.query.all()]

    def validate_contract_number(self, contract_number):
        contract = Contract.query.filter_by(contract_number=contract_number.data).first()
        if contract and (not hasattr(self, 'contract_id') or contract.id != self.contract_id.data):
            raise ValidationError('Số hợp đồng đã tồn tại.')

    def validate_dates(self):
        if self.start_date.data and self.end_date.data:
            if self.start_date.data > self.end_date.data:
                self.end_date.errors.append('Ngày kết thúc phải sau ngày bắt đầu.')
                return False
        return True


class ContractEditForm(ContractForm):
    """Form để chỉnh sửa hợp đồng"""
    contract_id = HiddenField('ID')
    
    def validate_status(self, status):
        contract = Contract.query.get(self.contract_id.data)
        if contract and contract.status.name == ContractStatus.TERMINATED.name and status.data != ContractStatus.TERMINATED.name:
            raise ValidationError('Không thể thay đổi trạng thái của hợp đồng đã chấm dứt.')


class ContractTerminationForm(FlaskForm):
    """Form để chấm dứt hợp đồng"""
    contract_id = HiddenField('ID')
    terminated_date = DateField('Ngày chấm dứt', validators=[
        DataRequired(message='Vui lòng chọn ngày chấm dứt')
    ], default=date.today)
    termination_reason = TextAreaField('Lý do chấm dứt', validators=[
        DataRequired(message='Vui lòng nhập lý do chấm dứt')
    ])


class ContractAmendmentForm(FlaskForm):
    """Form để tạo phụ lục hợp đồng"""
    contract_id = SelectField('Hợp đồng', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn hợp đồng')
    ])
    amendment_number = StringField('Số phụ lục', validators=[
        DataRequired(message='Vui lòng nhập số phụ lục'),
        Length(min=1, max=50, message='Số phụ lục phải có từ 1-50 ký tự')
    ])
    amendment_date = DateField('Ngày phụ lục', validators=[
        DataRequired(message='Vui lòng chọn ngày phụ lục')
    ], default=date.today)
    effective_date = DateField('Ngày có hiệu lực', validators=[
        DataRequired(message='Vui lòng chọn ngày có hiệu lực')
    ])
    description = TextAreaField('Mô tả', validators=[
        DataRequired(message='Vui lòng nhập mô tả')
    ])
    changes = TextAreaField('Nội dung thay đổi', validators=[
        DataRequired(message='Vui lòng nhập nội dung thay đổi')
    ])
    amendment_file = FileField('File phụ lục', validators=[
        Optional(),
        FileAllowed(['pdf', 'doc', 'docx'], 'Chỉ chấp nhận file PDF, DOC hoặc DOCX')
    ])

    def __init__(self, *args, **kwargs):
        super(ContractAmendmentForm, self).__init__(*args, **kwargs)
        # Lấy danh sách hợp đồng đang có hiệu lực
        self.contract_id.choices = [(c.id, f"{c.contract_number} - {c.employee.full_name}") for c in 
                                  Contract.query.filter_by(status=ContractStatus.ACTIVE).all()]

    def validate_dates(self):
        if self.amendment_date.data and self.effective_date.data:
            if self.effective_date.data < self.amendment_date.data:
                self.effective_date.errors.append('Ngày hiệu lực không thể trước ngày phụ lục.')
                return False
        return True


class ContractAmendmentEditForm(ContractAmendmentForm):
    """Form để chỉnh sửa phụ lục hợp đồng"""
    amendment_id = HiddenField('ID')


class DocumentForm(FlaskForm):
    """Form để thêm tài liệu"""
    employee_id = SelectField('Nhân viên', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn nhân viên')
    ])
    document_type = SelectField('Loại tài liệu', choices=[
        (t.name, t.value) for t in DocumentType
    ], validators=[DataRequired(message='Vui lòng chọn loại tài liệu')])
    document_number = StringField('Số hiệu', validators=[Optional()])
    issue_date = DateField('Ngày cấp', validators=[Optional()])
    expiry_date = DateField('Ngày hết hạn', validators=[Optional()])
    issue_place = StringField('Nơi cấp', validators=[Optional()])
    file_upload = FileField('Tải lên tài liệu', validators=[
        DataRequired(message='Vui lòng chọn file'),
        FileAllowed(['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'], 'Chỉ chấp nhận các định dạng file phổ biến')
    ])
    description = TextAreaField('Mô tả', validators=[Optional()])
    is_verified = SelectField('Xác minh', choices=[
        ('False', 'Chưa xác minh'),
        ('True', 'Đã xác minh')
    ], validators=[DataRequired()], default='False')

    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)
        # Lấy tất cả nhân viên
        self.employee_id.choices = [(e.id, f"{e.employee_code} - {e.full_name}") for e in Employee.query.all()]

    def validate_dates(self):
        if self.issue_date.data and self.expiry_date.data:
            if self.issue_date.data > self.expiry_date.data:
                self.expiry_date.errors.append('Ngày hết hạn phải sau ngày cấp.')
                return False
        return True


class DocumentEditForm(DocumentForm):
    """Form để chỉnh sửa tài liệu"""
    document_id = HiddenField('ID')
    file_upload = FileField('Thay đổi tài liệu', validators=[
        Optional(),
        FileAllowed(['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'], 'Chỉ chấp nhận các định dạng file phổ biến')
    ])


class ContractFilterForm(FlaskForm):
    """Form để lọc danh sách hợp đồng"""
    keyword = StringField('Từ khóa', validators=[Optional()])
    employee_id = SelectField('Nhân viên', coerce=int, validators=[Optional()])
    department_id = SelectField('Phòng ban', coerce=int, validators=[Optional()])
    contract_type = SelectField('Loại hợp đồng', validators=[Optional()])
    status = SelectField('Trạng thái', validators=[Optional()])
    start_date_from = DateField('Ngày bắt đầu từ', validators=[Optional()])
    start_date_to = DateField('Đến ngày', validators=[Optional()])
    end_date_from = DateField('Ngày hết hạn từ', validators=[Optional()])
    end_date_to = DateField('Đến ngày', validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super(ContractFilterForm, self).__init__(*args, **kwargs)
        self.employee_id.choices = [(0, 'Tất cả nhân viên')] + [(e.id, f"{e.employee_code} - {e.full_name}") for e in Employee.query.all()]
        self.department_id.choices = [(0, 'Tất cả phòng ban')] + [(d.id, d.name) for d in Department.query.all()]
        self.contract_type.choices = [('', 'Tất cả loại')] + [(t.name, t.value) for t in ContractType]
        self.status.choices = [('', 'Tất cả trạng thái')] + [(s.name, s.value) for s in ContractStatus]

    def validate_date_ranges(self):
        valid = True
        if self.start_date_from.data and self.start_date_to.data:
            if self.start_date_from.data > self.start_date_to.data:
                self.start_date_to.errors.append('Ngày kết thúc phải sau ngày bắt đầu.')
                valid = False
        
        if self.end_date_from.data and self.end_date_to.data:
            if self.end_date_from.data > self.end_date_to.data:
                self.end_date_to.errors.append('Ngày kết thúc phải sau ngày bắt đầu.')
                valid = False
        
        return valid