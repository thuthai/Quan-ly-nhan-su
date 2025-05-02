from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, TextAreaField, FloatField, FileField, HiddenField, IntegerField
from wtforms.validators import DataRequired, Optional, ValidationError, Length, Email, NumberRange
from flask_wtf.file import FileAllowed
from datetime import date, datetime
from models import (
    JobPosition, JobOpeningStatus, JobOpening, 
    CandidateStatus, Candidate, 
    InterviewType, InterviewStatus, 
    Department
)


class JobPositionForm(FlaskForm):
    """Form để tạo hoặc cập nhật vị trí công việc"""
    title = StringField('Tên vị trí', validators=[
        DataRequired(message='Vui lòng nhập tên vị trí'),
        Length(min=3, max=100, message='Tên vị trí phải có từ 3-100 ký tự')
    ])
    department_id = SelectField('Phòng ban', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn phòng ban')
    ])
    required_experience = StringField('Kinh nghiệm yêu cầu', validators=[Optional()])
    education_requirement = StringField('Yêu cầu học vấn', validators=[Optional()])
    job_description = TextAreaField('Mô tả công việc', validators=[Optional()])
    responsibilities = TextAreaField('Trách nhiệm', validators=[Optional()])
    skills_required = TextAreaField('Kỹ năng yêu cầu', validators=[Optional()])
    is_active = SelectField('Trạng thái', choices=[
        ('True', 'Đang hoạt động'),
        ('False', 'Không hoạt động')
    ], validators=[DataRequired(message='Vui lòng chọn trạng thái')])

    def __init__(self, *args, **kwargs):
        super(JobPositionForm, self).__init__(*args, **kwargs)
        # Lấy danh sách phòng ban
        self.department_id.choices = [(d.id, d.name) for d in Department.query.all()]


class JobPositionEditForm(JobPositionForm):
    """Form để chỉnh sửa vị trí công việc"""
    position_id = HiddenField('ID')


class JobOpeningForm(FlaskForm):
    """Form để tạo hoặc cập nhật tin tuyển dụng"""
    position_id = SelectField('Vị trí', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn vị trí')
    ])
    number_of_openings = IntegerField('Số lượng cần tuyển', validators=[
        DataRequired(message='Vui lòng nhập số lượng cần tuyển'),
        NumberRange(min=1, message='Số lượng phải từ 1 trở lên')
    ], default=1)
    status = SelectField('Trạng thái', choices=[
        (s.name, s.value) for s in JobOpeningStatus
    ], validators=[DataRequired(message='Vui lòng chọn trạng thái')])
    start_date = DateField('Ngày bắt đầu', validators=[
        DataRequired(message='Vui lòng chọn ngày bắt đầu')
    ], default=date.today)
    end_date = DateField('Ngày kết thúc', validators=[Optional()])
    salary_range = StringField('Mức lương', validators=[Optional()])
    work_location = StringField('Địa điểm làm việc', validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super(JobOpeningForm, self).__init__(*args, **kwargs)
        # Lấy danh sách vị trí công việc đang hoạt động
        self.position_id.choices = [(p.id, p.title) for p in JobPosition.query.filter_by(is_active=True).all()]

    def validate_dates(self):
        if self.start_date.data and self.end_date.data:
            if self.start_date.data > self.end_date.data:
                self.end_date.errors.append('Ngày kết thúc phải sau ngày bắt đầu.')
                return False
        return True


class JobOpeningEditForm(JobOpeningForm):
    """Form để chỉnh sửa tin tuyển dụng"""
    opening_id = HiddenField('ID')


class CandidateForm(FlaskForm):
    """Form để tạo hoặc cập nhật hồ sơ ứng viên"""
    job_opening_id = SelectField('Vị trí ứng tuyển', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn vị trí ứng tuyển')
    ])
    full_name = StringField('Họ và tên', validators=[
        DataRequired(message='Vui lòng nhập họ và tên'),
        Length(min=3, max=100, message='Họ và tên phải có từ 3-100 ký tự')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Vui lòng nhập email'),
        Email(message='Email không hợp lệ')
    ])
    phone = StringField('Số điện thoại', validators=[Optional()])
    cv_file = FileField('File CV', validators=[
        Optional(),
        FileAllowed(['pdf', 'doc', 'docx'], 'Chỉ chấp nhận file PDF, DOC hoặc DOCX')
    ])
    cover_letter = TextAreaField('Thư xin việc', validators=[Optional()])
    status = SelectField('Trạng thái', choices=[
        (s.name, s.value) for s in CandidateStatus
    ], validators=[DataRequired(message='Vui lòng chọn trạng thái')])
    application_date = DateField('Ngày ứng tuyển', validators=[
        DataRequired(message='Vui lòng chọn ngày ứng tuyển')
    ], default=date.today)
    evaluation = TextAreaField('Đánh giá', validators=[Optional()])
    notes = TextAreaField('Ghi chú', validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super(CandidateForm, self).__init__(*args, **kwargs)
        # Lấy danh sách tin tuyển dụng đang mở
        self.job_opening_id.choices = [(o.id, f"{o.position.title} ({o.start_date.strftime('%d/%m/%Y')} - {o.end_date.strftime('%d/%m/%Y') if o.end_date else 'Không giới hạn'})") 
                                 for o in JobOpening.query.filter(JobOpening.status == JobOpeningStatus.OPEN).all()]


class CandidateEditForm(CandidateForm):
    """Form để chỉnh sửa hồ sơ ứng viên"""
    candidate_id = HiddenField('ID')


class InterviewForm(FlaskForm):
    """Form để tạo hoặc cập nhật buổi phỏng vấn"""
    candidate_id = SelectField('Ứng viên', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn ứng viên')
    ])
    scheduled_date = DateField('Ngày phỏng vấn', validators=[
        DataRequired(message='Vui lòng chọn ngày phỏng vấn')
    ])
    scheduled_time = StringField('Giờ phỏng vấn', validators=[
        DataRequired(message='Vui lòng nhập giờ phỏng vấn')
    ])
    interview_type = SelectField('Loại phỏng vấn', choices=[
        (t.name, t.value) for t in InterviewType
    ], validators=[DataRequired(message='Vui lòng chọn loại phỏng vấn')])
    interviewers = StringField('Người phỏng vấn', validators=[Optional()])
    location = StringField('Địa điểm', validators=[Optional()])
    status = SelectField('Trạng thái', choices=[
        (s.name, s.value) for s in InterviewStatus
    ], validators=[DataRequired(message='Vui lòng chọn trạng thái')])
    feedback = TextAreaField('Phản hồi', validators=[Optional()])
    rating = SelectField('Đánh giá', choices=[
        ('', '-- Chọn đánh giá --'),
        ('1', '1 - Kém'),
        ('2', '2 - Trung bình'),
        ('3', '3 - Khá'),
        ('4', '4 - Tốt'),
        ('5', '5 - Xuất sắc')
    ], validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super(InterviewForm, self).__init__(*args, **kwargs)
        # Lấy danh sách ứng viên đang trong quá trình tuyển dụng
        valid_statuses = [CandidateStatus.APPLIED, CandidateStatus.SCREENING, 
                         CandidateStatus.INTERVIEW_SCHEDULED, CandidateStatus.INTERVIEWED]
        self.candidate_id.choices = [(c.id, f"{c.full_name} - {c.job_opening.position.title}") 
                               for c in Candidate.query.filter(Candidate.status.in_([s.name for s in valid_statuses])).all()]


class InterviewEditForm(InterviewForm):
    """Form để chỉnh sửa buổi phỏng vấn"""
    interview_id = HiddenField('ID')


class RecruitmentFilterForm(FlaskForm):
    """Form để lọc các tin tuyển dụng"""
    keyword = StringField('Từ khóa', validators=[Optional()])
    department_id = SelectField('Phòng ban', coerce=int, validators=[Optional()])
    status = SelectField('Trạng thái', validators=[Optional()])
    date_from = DateField('Từ ngày', validators=[Optional()])
    date_to = DateField('Đến ngày', validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super(RecruitmentFilterForm, self).__init__(*args, **kwargs)
        self.department_id.choices = [(0, 'Tất cả phòng ban')] + [(d.id, d.name) for d in Department.query.all()]
        self.status.choices = [('', 'Tất cả trạng thái')] + [(s.name, s.value) for s in JobOpeningStatus]

    def validate_date_range(self):
        if self.date_from.data and self.date_to.data:
            if self.date_from.data > self.date_to.data:
                self.date_to.errors.append('Ngày kết thúc phải sau ngày bắt đầu.')
                return False
        return True