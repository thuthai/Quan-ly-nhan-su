from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, DateField, DateTimeField, TextAreaField, FloatField, FileField, HiddenField, BooleanField, SelectMultipleField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError, NumberRange
from models import (Gender, EmployeeStatus, LeaveType, Department, User, Employee, UserRole,
              AwardType, EducationLevel, Position, VIETNAM_PROVINCES, SalaryGrade, WorkScheduleType, WorkScheduleStatus,
              PerformanceRatingPeriod, PerformanceRatingStatus, PerformanceEvaluationCriteria, CustomPosition,
              TaskStatus, TaskPriority, Task, WorkSchedule)
from app import db
from flask_wtf.file import FileAllowed
from datetime import date, datetime, timedelta


class EditUserForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired(message='Vui lòng nhập tên đăng nhập'), Length(min=4, max=64, message='Tên đăng nhập phải có từ 4-64 ký tự')])
    email = StringField('Email', validators=[DataRequired(message='Vui lòng nhập email'), Email(message='Email không hợp lệ')])
    password = PasswordField('Mật khẩu mới', validators=[Optional(), Length(min=6, message='Mật khẩu phải có ít nhất 6 ký tự')])
    confirm_password = PasswordField('Xác nhận mật khẩu mới', validators=[EqualTo('password', message='Mật khẩu xác nhận không khớp')])
    role = SelectField('Vai trò', choices=[(role.name, role.value) for role in UserRole], validators=[DataRequired(message='Vui lòng chọn vai trò')])
    employee_id = SelectField('Liên kết với nhân viên', coerce=int, validators=[Optional()])
    
    def __init__(self, original_username, original_email, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
        
        # Lấy danh sách nhân viên chưa có tài khoản (+ nhân viên hiện tại nếu có)
        current_employee_id = kwargs.get('obj') and kwargs['obj'].employee and kwargs['obj'].employee.id
        
        query = Employee.query.filter(
            db.or_(
                Employee.user_id.is_(None),
                Employee.user_id == kwargs.get('obj', {}).id if kwargs.get('obj') else False
            )
        )
        
        employees = query.all()
        self.employee_id.choices = [(0, '-- Không liên kết --')] + [(e.id, f"{e.employee_code} - {e.full_name}") for e in employees]
    
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Tên đăng nhập đã tồn tại.')
    
    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email này đã được đăng ký.')


class LoginForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired(message='Vui lòng nhập tên đăng nhập')])
    password = PasswordField('Mật khẩu', validators=[DataRequired(message='Vui lòng nhập mật khẩu')])


class RegisterForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired(message='Vui lòng nhập tên đăng nhập'), Length(min=4, max=64, message='Tên đăng nhập phải có từ 4-64 ký tự')])
    email = StringField('Email', validators=[DataRequired(message='Vui lòng nhập email'), Email(message='Email không hợp lệ')])
    password = PasswordField('Mật khẩu', validators=[DataRequired(message='Vui lòng nhập mật khẩu'), Length(min=6, message='Mật khẩu phải có ít nhất 6 ký tự')])
    confirm_password = PasswordField('Xác nhận mật khẩu', validators=[DataRequired(message='Vui lòng xác nhận mật khẩu'), EqualTo('password', message='Mật khẩu xác nhận không khớp')])
    employee_id = SelectField('Liên kết với nhân viên', coerce=int, validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        # Lấy danh sách nhân viên chưa có tài khoản
        unlinked_employees = Employee.query.filter(Employee.user_id.is_(None)).all()
        self.employee_id.choices = [(0, '-- Không liên kết --')] + [(e.id, f"{e.employee_code} - {e.full_name}") for e in unlinked_employees]

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
    id_card_number = StringField('Số căn cước công dân', validators=[Optional()])
    email = StringField('Email', validators=[DataRequired(message='Vui lòng nhập email'), Email(message='Email không hợp lệ')])
    department_id = SelectField('Phòng ban', coerce=int, validators=[DataRequired(message='Vui lòng chọn phòng ban')])
    position = SelectField('Chức vụ', validators=[Optional()])
    join_date = DateField('Ngày vào công ty', validators=[DataRequired(message='Vui lòng nhập ngày vào công ty')])
    salary_grade = StringField('Bậc lương', validators=[Optional()])
    salary_coefficient = FloatField('Hệ số lương', validators=[Optional()])
    contract_start_date = DateField('Ngày bắt đầu hợp đồng', validators=[Optional()])
    contract_end_date = DateField('Ngày kết thúc hợp đồng', validators=[Optional()])
    education_level = SelectField('Trình độ học vấn', choices=[(e.name, e.value) for e in EducationLevel], validators=[Optional()])
    university_name = StringField('Tên trường đại học', validators=[Optional()])
    university_major = StringField('Chuyên ngành', validators=[Optional()])
    skills = TextAreaField('Kỹ năng', validators=[Optional()])
    profile_image = FileField('Ảnh đại diện', validators=[Optional(), FileAllowed(['jpg', 'png', 'jpeg'], 'Chỉ chấp nhận file hình ảnh')])
    status = SelectField('Trạng thái', choices=[(s.name, s.value) for s in EmployeeStatus], validators=[DataRequired(message='Vui lòng chọn trạng thái')])
    
    def __init__(self, *args, **kwargs):
        super(EmployeeForm, self).__init__(*args, **kwargs)
        self.department_id.choices = [(d.id, d.name) for d in Department.query.all()]
        self.home_town.choices = [('', '-- Chọn quê quán --')] + [(province, province) for province in VIETNAM_PROVINCES]
        
        # Lấy danh sách vị trí mặc định từ enum Position
        default_positions = [(pos.value, pos.value) for pos in Position]
        
        # Lấy danh sách vị trí tùy chỉnh từ database
        custom_positions = [(pos.name, pos.name) for pos in CustomPosition.query.all()]
        
        # Kết hợp và gán cho choices của trường position
        self.position.choices = [('', '-- Chọn chức vụ --')] + default_positions + custom_positions

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
    education_level = SelectField('Trình độ học vấn', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(EmployeeFilterForm, self).__init__(*args, **kwargs)
        self.department_id.choices = [(0, 'Tất cả phòng ban')] + [(d.id, d.name) for d in Department.query.all()]
        self.gender.choices = [('', 'Tất cả')] + [(g.name, g.value) for g in Gender]
        self.status.choices = [('', 'Tất cả')] + [(s.name, s.value) for s in EmployeeStatus]
        self.home_town.choices = [('', 'Tất cả tỉnh thành')] + [(province, province) for province in VIETNAM_PROVINCES]
        self.education_level.choices = [('', 'Tất cả')] + [(e.name, e.value) for e in EducationLevel]
        
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


class CustomPositionForm(FlaskForm):
    """Form để thêm mới vị trí/chức vụ tùy chỉnh"""
    name = StringField('Tên vị trí/chức vụ', validators=[DataRequired(message='Vui lòng nhập tên vị trí')])
    description = TextAreaField('Mô tả', validators=[Optional()])
    
    def validate_name(self, name):
        # Kiểm tra nếu tên vị trí đã tồn tại
        custom_position = CustomPosition.query.filter_by(name=name.data).first()
        if custom_position and (not hasattr(self, 'custom_position_id') or custom_position.id != self.custom_position_id.data):
            raise ValidationError('Tên vị trí này đã tồn tại.')
            
        # Kiểm tra xem tên vị trí có trùng với Position enum không
        for pos in Position:
            if pos.value == name.data:
                raise ValidationError('Tên vị trí này đã tồn tại trong danh sách vị trí mặc định.')


class CustomPositionEditForm(CustomPositionForm):
    """Form để chỉnh sửa vị trí/chức vụ tùy chỉnh"""
    custom_position_id = HiddenField('ID')


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


class WorkScheduleForm(FlaskForm):
    """Form tạo lịch công tác"""
    title = StringField('Tiêu đề', validators=[DataRequired(message='Vui lòng nhập tiêu đề')])
    description = TextAreaField('Mô tả', validators=[Optional()])
    schedule_type = SelectField('Loại lịch công tác', choices=[(t.name, t.value) for t in WorkScheduleType], validators=[DataRequired(message='Vui lòng chọn loại lịch công tác')])
    location = StringField('Địa điểm', validators=[DataRequired(message='Vui lòng nhập địa điểm')])
    start_time = DateTimeField('Thời gian bắt đầu', format='%Y-%m-%dT%H:%M', validators=[DataRequired(message='Vui lòng chọn thời gian bắt đầu')])
    end_time = DateTimeField('Thời gian kết thúc', format='%Y-%m-%dT%H:%M', validators=[DataRequired(message='Vui lòng chọn thời gian kết thúc')])
    participants = SelectMultipleField('Người tham gia', coerce=int, validators=[DataRequired(message='Vui lòng chọn ít nhất một người tham gia')])
    
    def __init__(self, *args, **kwargs):
        super(WorkScheduleForm, self).__init__(*args, **kwargs)
        self.participants.choices = [(e.id, f"{e.employee_code} - {e.full_name}") for e in Employee.query.filter_by(status=EmployeeStatus.ACTIVE).all()]
    
    def validate_end_time(self, end_time):
        if self.start_time.data and end_time.data:
            if self.start_time.data >= end_time.data:
                raise ValidationError('Thời gian kết thúc phải sau thời gian bắt đầu.')


class WorkScheduleEditForm(WorkScheduleForm):
    """Form chỉnh sửa lịch công tác"""
    schedule_id = HiddenField('ID')


class WorkScheduleApprovalForm(FlaskForm):
    """Form phê duyệt lịch công tác"""
    status = SelectField('Trạng thái', choices=[(s.name, s.value) for s in WorkScheduleStatus if s != WorkScheduleStatus.PENDING], validators=[DataRequired(message='Vui lòng chọn trạng thái')])
    feedback = TextAreaField('Phản hồi', validators=[Optional()])


class WorkScheduleFilterForm(FlaskForm):
    """Form lọc lịch công tác"""
    keyword = StringField('Từ khóa', validators=[Optional()])
    schedule_type = SelectField('Loại lịch công tác', validators=[Optional()])
    status = SelectField('Trạng thái', validators=[Optional()])
    start_date = DateField('Từ ngày', validators=[Optional()])
    end_date = DateField('Đến ngày', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(WorkScheduleFilterForm, self).__init__(*args, **kwargs)
        self.schedule_type.choices = [('', 'Tất cả loại')] + [(t.name, t.value) for t in WorkScheduleType]
        self.status.choices = [('', 'Tất cả trạng thái')] + [(s.name, s.value) for s in WorkScheduleStatus]
    
    def validate_dates(self):
        if self.start_date.data and self.end_date.data:
            if self.start_date.data > self.end_date.data:
                self.end_date.errors.append('Ngày kết thúc phải sau ngày bắt đầu.')
                return False
        return True


class PerformanceCriteriaForm(FlaskForm):
    """Form tạo tiêu chí đánh giá hiệu suất"""
    name = StringField('Tên tiêu chí', validators=[DataRequired(message='Vui lòng nhập tên tiêu chí')])
    description = TextAreaField('Mô tả', validators=[Optional()])
    max_score = StringField('Điểm tối đa', validators=[DataRequired(message='Vui lòng nhập điểm tối đa')], default='10')
    weight = FloatField('Trọng số', validators=[DataRequired(message='Vui lòng nhập trọng số')], default=1.0)
    department_id = SelectField('Áp dụng cho phòng ban', coerce=int, validators=[Optional()])
    is_active = BooleanField('Kích hoạt', default=True)
    
    def __init__(self, *args, **kwargs):
        super(PerformanceCriteriaForm, self).__init__(*args, **kwargs)
        self.department_id.choices = [(0, 'Tất cả phòng ban')] + [(d.id, d.name) for d in Department.query.all()]
    
    def validate_max_score(self, max_score):
        try:
            score = int(max_score.data)
            if score <= 0:
                raise ValidationError('Điểm tối đa phải là số nguyên dương.')
        except ValueError:
            raise ValidationError('Điểm tối đa phải là số nguyên.')
    
    def validate_weight(self, weight):
        if weight.data <= 0:
            raise ValidationError('Trọng số phải lớn hơn 0.')


class PerformanceEvaluationForm(FlaskForm):
    """Form tạo đánh giá hiệu suất nhân viên"""
    employee_id = SelectField('Nhân viên', coerce=int, validators=[DataRequired(message='Vui lòng chọn nhân viên')])
    evaluation_period = SelectField('Kỳ đánh giá', choices=[(p.name, p.value) for p in PerformanceRatingPeriod], validators=[DataRequired(message='Vui lòng chọn kỳ đánh giá')])
    start_date = DateField('Từ ngày', validators=[DataRequired(message='Vui lòng chọn ngày bắt đầu')])
    end_date = DateField('Đến ngày', validators=[DataRequired(message='Vui lòng chọn ngày kết thúc')])
    comments = TextAreaField('Nhận xét tổng quát', validators=[Optional()])
    strengths = TextAreaField('Điểm mạnh', validators=[Optional()])
    areas_for_improvement = TextAreaField('Lĩnh vực cần cải thiện', validators=[Optional()])
    goals_for_next_period = TextAreaField('Mục tiêu cho kỳ tiếp theo', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(PerformanceEvaluationForm, self).__init__(*args, **kwargs)
        self.employee_id.choices = [(e.id, f"{e.employee_code} - {e.full_name}") for e in Employee.query.filter_by(status=EmployeeStatus.ACTIVE).all()]
    
    def validate_dates(self):
        if self.start_date.data and self.end_date.data:
            if self.start_date.data > self.end_date.data:
                self.end_date.errors.append('Ngày kết thúc phải sau ngày bắt đầu.')
                return False
        return True


class PerformanceCriteriaScoreForm(FlaskForm):
    """Form điền điểm cho tiêu chí"""
    score = FloatField('Điểm số', validators=[Optional()])
    comments = TextAreaField('Nhận xét', validators=[Optional()])
    
    def __init__(self, criteria=None, *args, **kwargs):
        super(PerformanceCriteriaScoreForm, self).__init__(*args, **kwargs)
        self.criteria = criteria
    
    def validate_score(self, score):
        if score.data is not None:
            if hasattr(self, 'criteria') and self.criteria and score.data > self.criteria.max_score:
                raise ValidationError(f'Điểm số không thể vượt quá {self.criteria.max_score}.')
            if score.data < 0:
                raise ValidationError('Điểm số không thể âm.')


class EmployeePerformanceFeedbackForm(FlaskForm):
    """Form phản hồi của nhân viên về kết quả đánh giá"""
    employee_comments = TextAreaField('Phản hồi của bạn', validators=[Optional()])


class PerformanceApprovalForm(FlaskForm):
    """Form phê duyệt đánh giá hiệu suất"""
    status = SelectField('Trạng thái', choices=[(s.name, s.value) for s in PerformanceRatingStatus if s != PerformanceRatingStatus.DRAFT], validators=[DataRequired(message='Vui lòng chọn trạng thái')])
    comments = TextAreaField('Nhận xét', validators=[Optional()])


class PerformanceFilterForm(FlaskForm):
    """Form lọc đánh giá hiệu suất"""
    employee_id = SelectField('Nhân viên', coerce=int, validators=[Optional()])
    evaluation_period = SelectField('Kỳ đánh giá', validators=[Optional()])
    status = SelectField('Trạng thái', validators=[Optional()])
    start_date = DateField('Từ ngày', validators=[Optional()])
    end_date = DateField('Đến ngày', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(PerformanceFilterForm, self).__init__(*args, **kwargs)
        self.employee_id.choices = [(0, 'Tất cả nhân viên')] + [(e.id, f"{e.employee_code} - {e.full_name}") for e in Employee.query.filter_by(status=EmployeeStatus.ACTIVE).all()]
        self.evaluation_period.choices = [('', 'Tất cả kỳ đánh giá')] + [(p.name, p.value) for p in PerformanceRatingPeriod]
        self.status.choices = [('', 'Tất cả trạng thái')] + [(s.name, s.value) for s in PerformanceRatingStatus]
    
    def validate_dates(self):
        if self.start_date.data and self.end_date.data:
            if self.start_date.data > self.end_date.data:
                self.end_date.errors.append('Ngày kết thúc phải sau ngày bắt đầu.')
                return False
        return True

class CustomPositionForm(FlaskForm):
    """Form cho việc thêm chức vụ tùy chỉnh"""
    name = StringField('Tên chức vụ', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Mô tả', validators=[Optional()])
    submit = SubmitField('Lưu chức vụ')
    
    def validate_name(self, name):
        """Xác nhận tên chức vụ không trùng lặp"""
        # Kiểm tra xem tên chức vụ đã tồn tại trong các chức vụ mặc định hay chưa
        for pos in Position:
            if pos.value == name.data:
                raise ValidationError('Tên chức vụ này đã tồn tại trong danh sách mặc định.')
        
        # Kiểm tra xem tên chức vụ đã tồn tại trong các chức vụ tùy chỉnh hay chưa
        position = CustomPosition.query.filter_by(name=name.data).first()
        if position:
            raise ValidationError('Tên chức vụ này đã tồn tại trong danh sách tùy chỉnh.')


# Lớp này đã bị trùng lặp nên đã được gỡ bỏ


class TaskForm(FlaskForm):
    """Form tạo nhiệm vụ mới cho Kanban board"""
    title = StringField('Tiêu đề', validators=[DataRequired(message='Vui lòng nhập tiêu đề nhiệm vụ')])
    description = TextAreaField('Mô tả', validators=[Optional()])
    status = SelectField('Trạng thái', choices=[(s.name, s.value) for s in TaskStatus], validators=[DataRequired(message='Vui lòng chọn trạng thái')])
    priority = SelectField('Mức độ ưu tiên', choices=[(p.name, p.value) for p in TaskPriority], validators=[DataRequired(message='Vui lòng chọn mức độ ưu tiên')])
    assigned_to = SelectField('Người được giao', coerce=int, validators=[Optional()])
    department_id = SelectField('Phòng ban', coerce=int, validators=[Optional()])
    work_schedule_id = SelectField('Lịch công tác liên quan', coerce=int, validators=[Optional()])
    deadline = DateTimeField('Hạn chót', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    estimated_hours = FloatField('Số giờ dự kiến', validators=[Optional(), NumberRange(min=0, message='Số giờ phải lớn hơn hoặc bằng 0')])
    labels = StringField('Nhãn', validators=[Optional()], description='Nhập các nhãn cách nhau bằng dấu phẩy (,)')
    progress = IntegerField('Tiến độ (%)', validators=[Optional(), NumberRange(min=0, max=100, message='Tiến độ phải từ 0 đến 100%')])
    dependent_tasks = SelectMultipleField('Nhiệm vụ phụ thuộc', coerce=int, validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        self.assigned_to.choices = [(0, 'Chưa phân công')] + [(e.id, f"{e.employee_code} - {e.full_name}") for e in Employee.query.filter_by(status=EmployeeStatus.ACTIVE).all()]
        self.department_id.choices = [(0, 'Không thuộc phòng ban cụ thể')] + [(d.id, d.name) for d in Department.query.all()]
        self.work_schedule_id.choices = [(0, 'Không liên kết với lịch công tác')] + [(w.id, f"{w.title} ({w.start_time.strftime('%d/%m/%Y')})") for w in WorkSchedule.query.filter(WorkSchedule.end_time > datetime.utcnow()).all()]
        # Chỉ hiển thị các nhiệm vụ đang làm và đang xét duyệt để tránh phụ thuộc vòng
        self.dependent_tasks.choices = [(t.id, f"{t.title} ({t.status_display})") for t in Task.query.filter(Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.REVIEW])).all()]
        
    def validate_deadline(self, deadline):
        if deadline.data and deadline.data < datetime.utcnow():
            raise ValidationError('Hạn chót không thể là thời gian trong quá khứ.')


class TaskEditForm(TaskForm):
    """Form chỉnh sửa nhiệm vụ"""
    task_id = HiddenField('ID')
    actual_hours = FloatField('Số giờ thực tế', validators=[Optional(), NumberRange(min=0, message='Số giờ phải lớn hơn hoặc bằng 0')])
    

class TaskCommentForm(FlaskForm):
    """Form thêm bình luận cho nhiệm vụ"""
    content = TextAreaField('Bình luận', validators=[DataRequired(message='Vui lòng nhập nội dung bình luận')])
    task_id = HiddenField('Task ID', validators=[DataRequired()])


class TaskSearchForm(FlaskForm):
    """Form tìm kiếm nhiệm vụ"""
    keyword = StringField('Từ khóa', validators=[Optional()])
    status = SelectField('Trạng thái', choices=[('', 'Tất cả')] + [(s.name, s.value) for s in TaskStatus], validators=[Optional()])
    priority = SelectField('Mức độ ưu tiên', choices=[('', 'Tất cả')] + [(p.name, p.value) for p in TaskPriority], validators=[Optional()])
    assigned_to = SelectField('Người được giao', coerce=int, validators=[Optional()])
    department_id = SelectField('Phòng ban', coerce=int, validators=[Optional()])
    label = StringField('Nhãn', validators=[Optional()])
    overdue = BooleanField('Chỉ hiện nhiệm vụ quá hạn', default=False)
    
    def __init__(self, *args, **kwargs):
        super(TaskSearchForm, self).__init__(*args, **kwargs)
        self.assigned_to.choices = [('', 'Tất cả')] + [(e.id, f"{e.employee_code} - {e.full_name}") for e in Employee.query.all()]
        self.department_id.choices = [('', 'Tất cả')] + [(d.id, d.name) for d in Department.query.all()]


class TaskBulkActionForm(FlaskForm):
    """Form thực hiện hành động hàng loạt trên nhiều nhiệm vụ"""
    task_ids = HiddenField('Task IDs', validators=[DataRequired()])
    action = SelectField('Hành động', choices=[
        ('status', 'Cập nhật trạng thái'),
        ('priority', 'Cập nhật mức độ ưu tiên'),
        ('assigned_to', 'Gán người thực hiện'),
        ('department', 'Chuyển phòng ban'),
        ('delete', 'Xóa nhiệm vụ')
    ], validators=[DataRequired()])
    status = SelectField('Trạng thái mới', choices=[(s.name, s.value) for s in TaskStatus], validators=[Optional()])
    priority = SelectField('Mức độ ưu tiên mới', choices=[(p.name, p.value) for p in TaskPriority], validators=[Optional()])
    assigned_to = SelectField('Người được giao mới', coerce=int, validators=[Optional()])
    department_id = SelectField('Phòng ban mới', coerce=int, validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(TaskBulkActionForm, self).__init__(*args, **kwargs)
        self.assigned_to.choices = [(0, 'Chưa phân công')] + [(e.id, f"{e.employee_code} - {e.full_name}") for e in Employee.query.filter_by(status=EmployeeStatus.ACTIVE).all()]
        self.department_id.choices = [(0, 'Không thuộc phòng ban cụ thể')] + [(d.id, d.name) for d in Department.query.all()]
