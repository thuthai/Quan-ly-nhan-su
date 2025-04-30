from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, DateField, DateTimeField, TextAreaField, FloatField, FileField, HiddenField, BooleanField, SelectMultipleField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError
from models import (Gender, EmployeeStatus, LeaveType, Department, User, Employee, 
              AwardType, EducationLevel, VIETNAM_PROVINCES, SalaryGrade, WorkScheduleType, WorkScheduleStatus)
from flask_wtf.file import FileAllowed
from datetime import date, datetime, timedelta


class LoginForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired(message='Vui lòng nhập tên đăng nhập')])
    password = PasswordField('Mật khẩu', validators=[DataRequired(message='Vui lòng nhập mật khẩu')])


class RegisterForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired(message='Vui lòng nhập tên đăng nhập'), Length(min=4, max=64, message='Tên đăng nhập phải có từ 4-64 ký tự')])
    email = StringField('Email', validators=[DataRequired(message='Vui lòng nhập email'), Email(message='Email không hợp lệ')])
    password = PasswordField('Mật khẩu', validators=[DataRequired(message='Vui lòng nhập mật khẩu'), Length(min=6, message='Mật khẩu phải có ít nhất 6 ký tự')])
    confirm_password = PasswordField('Xác nhận mật khẩu', validators=[DataRequired(message='Vui lòng xác nhận mật khẩu'), EqualTo('password', message='Mật khẩu xác nhận không khớp')])

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Tên đăng nhập đã tồn tại.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email này đã được đăng ký.')


class DepartmentForm(FlaskForm):
    name = StringField('Tên phòng ban', validators=[DataRequired(message='Vui lòng nhập tên phòng ban')])
    description = TextAreaField('Mô tả', validators=[Optional()])


class EmployeeForm(FlaskForm):
    employee_code = StringField('Mã nhân viên', validators=[DataRequired(message='Vui lòng nhập mã nhân viên')])
    full_name = StringField('Họ và tên', validators=[DataRequired(message='Vui lòng nhập họ và tên')])
    gender = SelectField('Giới tính', choices=[(g.name, g.value) for g in Gender], validators=[DataRequired(message='Vui lòng chọn giới tính')])
    date_of_birth = DateField('Ngày sinh', validators=[DataRequired(message='Vui lòng nhập ngày sinh')])
    home_town = SelectField('Quê quán', validators=[Optional()])
    address = StringField('Địa chỉ', validators=[Optional()])
    phone_number = StringField('Số điện thoại', validators=[Optional()])
    email = StringField('Email', validators=[DataRequired(message='Vui lòng nhập email'), Email(message='Email không hợp lệ')])
    department_id = SelectField('Phòng ban', coerce=int, validators=[DataRequired(message='Vui lòng chọn phòng ban')])
    position = StringField('Chức vụ', validators=[Optional()])
    join_date = DateField('Ngày vào công ty', validators=[DataRequired(message='Vui lòng nhập ngày vào công ty')])
    salary_grade = StringField('Bậc lương', validators=[Optional()])
    salary_coefficient = FloatField('Hệ số lương', validators=[Optional()])
    contract_start_date = DateField('Ngày bắt đầu hợp đồng', validators=[Optional()])
    contract_end_date = DateField('Ngày kết thúc hợp đồng', validators=[Optional()])
    education_level = StringField('Trình độ học vấn', validators=[Optional()])
    skills = TextAreaField('Kỹ năng', validators=[Optional()])
    profile_image = FileField('Ảnh đại diện', validators=[Optional(), FileAllowed(['jpg', 'png', 'jpeg'], 'Chỉ chấp nhận file hình ảnh')])
    status = SelectField('Trạng thái', choices=[(s.name, s.value) for s in EmployeeStatus], validators=[DataRequired(message='Vui lòng chọn trạng thái')])
    
    def __init__(self, *args, **kwargs):
        super(EmployeeForm, self).__init__(*args, **kwargs)
        self.department_id.choices = [(d.id, d.name) for d in Department.query.all()]
        self.home_town.choices = [('', '-- Chọn quê quán --')] + [(province, province) for province in VIETNAM_PROVINCES]

    def validate_employee_code(self, employee_code):
        employee = Employee.query.filter_by(employee_code=employee_code.data).first()
        if employee and (not hasattr(self, 'employee_id') or employee.id != self.employee_id.data):
            raise ValidationError('Mã nhân viên đã tồn tại.')

    def validate_email(self, email):
        employee = Employee.query.filter_by(email=email.data).first()
        if employee and (not hasattr(self, 'employee_id') or employee.id != self.employee_id.data):
            raise ValidationError('Email này đã được sử dụng.')

    def validate_contract_dates(self):
        if self.contract_start_date.data and self.contract_end_date.data:
            if self.contract_start_date.data > self.contract_end_date.data:
                self.contract_end_date.errors.append('Ngày kết thúc phải sau ngày bắt đầu hợp đồng.')
                return False
        return True


class EmployeeEditForm(EmployeeForm):
    employee_id = HiddenField('ID')


class LeaveRequestForm(FlaskForm):
    leave_type = SelectField('Loại phép', choices=[(t.name, t.value) for t in LeaveType], validators=[DataRequired(message='Vui lòng chọn loại phép')])
    start_date = DateField('Từ ngày', validators=[DataRequired(message='Vui lòng chọn ngày bắt đầu')])
    end_date = DateField('Đến ngày', validators=[DataRequired(message='Vui lòng chọn ngày kết thúc')])
    reason = TextAreaField('Lý do', validators=[DataRequired(message='Vui lòng nhập lý do')])

    def validate_dates(self):
        if self.start_date.data and self.end_date.data:
            if self.start_date.data > self.end_date.data:
                self.end_date.errors.append('Ngày kết thúc phải sau ngày bắt đầu.')
                return False
            if self.start_date.data < date.today():
                self.start_date.errors.append('Ngày bắt đầu không thể trong quá khứ.')
                return False
        return True


class CareerPathForm(FlaskForm):
    position = StringField('Vị trí', validators=[DataRequired(message='Vui lòng nhập vị trí')])
    start_date = DateField('Ngày bắt đầu', validators=[DataRequired(message='Vui lòng chọn ngày bắt đầu')])
    end_date = DateField('Ngày kết thúc', validators=[Optional()])
    description = TextAreaField('Mô tả', validators=[Optional()])

    def validate_dates(self):
        if self.start_date.data and self.end_date.data:
            if self.start_date.data > self.end_date.data:
                self.end_date.errors.append('Ngày kết thúc phải sau ngày bắt đầu.')
                return False
        return True


class AttendanceReportForm(FlaskForm):
    start_date = DateField('Từ ngày', validators=[DataRequired(message='Vui lòng chọn ngày bắt đầu')])
    end_date = DateField('Đến ngày', validators=[DataRequired(message='Vui lòng chọn ngày kết thúc')])
    employee_id = SelectField('Nhân viên', coerce=int, validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(AttendanceReportForm, self).__init__(*args, **kwargs)
        self.employee_id.choices = [(0, 'Tất cả nhân viên')] + [(e.id, f"{e.employee_code} - {e.full_name}") for e in Employee.query.filter_by(status=EmployeeStatus.ACTIVE).all()]

    def validate_dates(self):
        if self.start_date.data and self.end_date.data:
            if self.start_date.data > self.end_date.data:
                self.end_date.errors.append('Ngày kết thúc phải sau ngày bắt đầu.')
                return False
        return True


class EmployeeImportForm(FlaskForm):
    import_file = FileField('File dữ liệu (.xlsx, .xls, .csv)', validators=[
        DataRequired(message='Vui lòng chọn file để tải lên'),
        FileAllowed(['xlsx', 'xls', 'csv'], 'Chỉ chấp nhận file Excel hoặc CSV')
    ])
    skip_header = BooleanField('Bỏ qua dòng đầu tiên (tiêu đề)', default=True)
    update_existing = BooleanField('Cập nhật nhân viên đã tồn tại', default=True)
    department_id = SelectField('Phòng ban mặc định', coerce=int, validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(EmployeeImportForm, self).__init__(*args, **kwargs)
        self.department_id.choices = [(0, 'Không chọn')] + [(d.id, d.name) for d in Department.query.all()]


class AwardForm(FlaskForm):
    name = StringField('Tên danh hiệu', validators=[DataRequired(message='Vui lòng nhập tên danh hiệu')])
    award_type = SelectField('Loại danh hiệu', choices=[(t.name, t.value) for t in AwardType], validators=[DataRequired(message='Vui lòng chọn loại danh hiệu')])
    year = StringField('Năm đạt được', validators=[DataRequired(message='Vui lòng nhập năm đạt được')])
    date_received = DateField('Ngày nhận', validators=[Optional()])
    description = TextAreaField('Mô tả', validators=[Optional()])
    certificate_number = StringField('Số giấy chứng nhận', validators=[Optional()])
    issued_by = StringField('Đơn vị cấp', validators=[Optional()])
    
    def validate_year(self, year):
        try:
            year_value = int(year.data)
            current_year = date.today().year
            if year_value < 1900 or year_value > current_year + 1:
                raise ValidationError(f'Năm phải trong khoảng từ 1900 đến {current_year + 1}.')
        except ValueError:
            raise ValidationError('Năm phải là một số nguyên.')


class AwardEditForm(AwardForm):
    award_id = HiddenField('ID')


class EmployeeFilterForm(FlaskForm):
    keyword = StringField('Từ khóa', validators=[Optional()])
    department_id = SelectField('Phòng ban', coerce=int, validators=[Optional()])
    gender = SelectField('Giới tính', validators=[Optional()])
    status = SelectField('Trạng thái', validators=[Optional()])
    home_town = SelectField('Quê quán', validators=[Optional()])
    age_min = StringField('Tuổi từ', validators=[Optional()])
    age_max = StringField('Đến', validators=[Optional()])
    join_date_from = DateField('Ngày vào làm từ', validators=[Optional()])
    join_date_to = DateField('Đến ngày', validators=[Optional()])
    education_level = StringField('Trình độ học vấn', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(EmployeeFilterForm, self).__init__(*args, **kwargs)
        self.department_id.choices = [(0, 'Tất cả phòng ban')] + [(d.id, d.name) for d in Department.query.all()]
        self.gender.choices = [('', 'Tất cả')] + [(g.name, g.value) for g in Gender]
        self.status.choices = [('', 'Tất cả')] + [(s.name, s.value) for s in EmployeeStatus]
        self.home_town.choices = [('', 'Tất cả tỉnh thành')] + [(province, province) for province in VIETNAM_PROVINCES]
        
    def validate_age_min(self, age_min):
        if age_min.data:
            try:
                age = int(age_min.data)
                if age < 0 or age > 100:
                    raise ValidationError('Tuổi phải từ 0 đến 100.')
            except ValueError:
                raise ValidationError('Tuổi phải là số nguyên.')
                
    def validate_age_max(self, age_max):
        if age_max.data:
            try:
                age = int(age_max.data)
                if age < 0 or age > 100:
                    raise ValidationError('Tuổi phải từ 0 đến 100.')
            except ValueError:
                raise ValidationError('Tuổi phải là số nguyên.')
                
    def validate_dates(self):
        if self.join_date_from.data and self.join_date_to.data:
            if self.join_date_from.data > self.join_date_to.data:
                self.join_date_to.errors.append('Ngày kết thúc phải sau ngày bắt đầu.')
                return False
        return True


class SalaryGradeForm(FlaskForm):
    code = StringField('Mã bậc lương', validators=[DataRequired(message='Vui lòng nhập mã bậc lương')])
    name = StringField('Tên bậc lương', validators=[DataRequired(message='Vui lòng nhập tên bậc lương')])
    base_coefficient = FloatField('Hệ số cơ bản', validators=[DataRequired(message='Vui lòng nhập hệ số cơ bản')])
    base_salary = StringField('Lương cơ sở', validators=[DataRequired(message='Vui lòng nhập lương cơ sở')])
    description = TextAreaField('Mô tả', validators=[Optional()])
    
    def validate_code(self, code):
        grade = SalaryGrade.query.filter_by(code=code.data).first()
        if grade and (not hasattr(self, 'salary_grade_id') or grade.id != int(self.salary_grade_id.data)):
            raise ValidationError('Mã bậc lương đã tồn tại.')
    
    def validate_base_coefficient(self, base_coefficient):
        if base_coefficient.data and base_coefficient.data <= 0:
            raise ValidationError('Hệ số cơ bản phải lớn hơn 0.')
    
    def validate_base_salary(self, base_salary):
        try:
            value = int(base_salary.data)
            if value <= 0:
                raise ValidationError('Lương cơ sở phải lớn hơn 0.')
        except ValueError:
            raise ValidationError('Lương cơ sở phải là một số nguyên.')


class SalaryGradeEditForm(SalaryGradeForm):
    salary_grade_id = HiddenField('ID')


class EmployeeSalaryForm(FlaskForm):
    employee_id = SelectField('Nhân viên', coerce=int, validators=[DataRequired(message='Vui lòng chọn nhân viên')])
    salary_grade_id = SelectField('Bậc lương', coerce=int, validators=[DataRequired(message='Vui lòng chọn bậc lương')])
    effective_date = DateField('Ngày hiệu lực', validators=[DataRequired(message='Vui lòng chọn ngày hiệu lực')])
    end_date = DateField('Ngày kết thúc', validators=[Optional()])
    additional_coefficient = FloatField('Hệ số phụ cấp', validators=[Optional()], default=0)
    reason = TextAreaField('Lý do', validators=[Optional()])
    decision_number = StringField('Số quyết định', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(EmployeeSalaryForm, self).__init__(*args, **kwargs)
        self.employee_id.choices = [(e.id, f"{e.employee_code} - {e.full_name}") for e in Employee.query.filter_by(status=EmployeeStatus.ACTIVE).all()]
        self.salary_grade_id.choices = [(g.id, f"{g.code} - {g.name} (Hệ số: {g.base_coefficient})") for g in SalaryGrade.query.all()]
    
    def validate_dates(self):
        if self.effective_date.data and self.end_date.data:
            if self.effective_date.data > self.end_date.data:
                self.end_date.errors.append('Ngày kết thúc phải sau ngày hiệu lực.')
                return False
        return True
    
    def validate_additional_coefficient(self, additional_coefficient):
        if additional_coefficient.data and additional_coefficient.data < 0:
            raise ValidationError('Hệ số phụ cấp không được âm.')


class EmployeeSalaryEditForm(EmployeeSalaryForm):
    salary_id = HiddenField('ID')
