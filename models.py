from datetime import datetime, date
import enum
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os


def load_user(user_id):
    return User.query.get(int(user_id))


class UserRole(enum.Enum):
    ADMIN = "admin"
    EMPLOYEE = "employee"


class Gender(enum.Enum):
    MALE = "Nam"
    FEMALE = "Nữ" 
    OTHER = "Khác"


class EmployeeStatus(enum.Enum):
    ACTIVE = "Đang làm việc"
    LEAVE = "Nghỉ việc"
    SUSPENDED = "Tạm ngưng"


class LeaveType(enum.Enum):
    ANNUAL = "Nghỉ phép năm"
    SICK = "Nghỉ ốm"
    MATERNITY = "Nghỉ thai sản"
    BEREAVEMENT = "Nghỉ tang"
    UNPAID = "Nghỉ không lương"
    OTHER = "Khác"


class EducationLevel(enum.Enum):
    """Trình độ học vấn"""
    SECONDARY = "Trung học cơ sở"
    HIGH_SCHOOL = "Trung học phổ thông" 
    VOCATIONAL = "Trung cấp nghề"
    COLLEGE = "Cao đẳng"
    UNIVERSITY = "Đại học"
    MASTER = "Thạc sĩ"
    DOCTORATE = "Tiến sĩ"
    OTHER = "Khác"


class Position(enum.Enum):
    """Chức vụ"""
    BOARD_CHAIRMAN = "Chủ tịch HĐQT"
    BOARD_MEMBER = "Thành viên HĐQT"
    DIRECTOR = "Giám đốc"
    DEPUTY_DIRECTOR = "Phó giám đốc"
    HEAD_DEPARTMENT = "Trưởng phòng"
    DEPUTY_HEAD_DEPARTMENT = "Phó phòng"
    TEAM_LEAD = "Trưởng nhóm"
    STAFF = "Nhân viên"
    OTHER = "Khác"


class LeaveStatus(enum.Enum):
    PENDING = "Đang chờ xét duyệt"
    APPROVED = "Đã duyệt"
    REJECTED = "Từ chối"


class ApproverRole(enum.Enum):
    """Vai trò người phê duyệt trong quy trình"""
    MANAGER = "Quản lý trực tiếp"
    DEPARTMENT_HEAD = "Trưởng phòng"
    HR_MANAGER = "Quản lý nhân sự"
    DIRECTOR = "Giám đốc"
    CEO = "Tổng giám đốc"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.EMPLOYEE, nullable=False)
    
    # Relationship with Employee
    employee = db.relationship('Employee', backref='user', uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == UserRole.ADMIN
    
    def __repr__(self):
        return f'<User {self.username}>'


class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with Employee
    employees = db.relationship('Employee', backref='department', lazy=True)
    
    def __repr__(self):
        return f'<Department {self.name}>'


class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    employee_code = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.Enum(Gender), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    home_town = db.Column(db.String(100))
    address = db.Column(db.String(200))
    phone_number = db.Column(db.String(20))
    email = db.Column(db.String(120), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    position = db.Column(db.Enum(Position), default=Position.STAFF)
    join_date = db.Column(db.Date, nullable=False)
    salary_grade = db.Column(db.String(20))
    salary_coefficient = db.Column(db.Float)
    contract_start_date = db.Column(db.Date)
    contract_end_date = db.Column(db.Date)
    education_level = db.Column(db.Enum(EducationLevel), default=EducationLevel.OTHER)
    skills = db.Column(db.Text)
    profile_image = db.Column(db.String(255), default='https://images.unsplash.com/photo-1522071820081-009f0129c71c')
    status = db.Column(db.Enum(EmployeeStatus), default=EmployeeStatus.ACTIVE)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attendances = db.relationship('Attendance', backref='employee', lazy=True)
    leave_requests = db.relationship('LeaveRequest', backref='employee', lazy=True)
    career_paths = db.relationship('CareerPath', backref='employee', lazy=True)
    awards = db.relationship('Award', backref='employee', lazy=True)
    
    def is_contract_expiring_soon(self):
        if not self.contract_end_date:
            return False
        
        days_remaining = (self.contract_end_date - date.today()).days
        return 0 <= days_remaining <= 30
    
    def contract_days_remaining(self):
        if not self.contract_end_date:
            return None
        
        return (self.contract_end_date - date.today()).days
    
    def __repr__(self):
        return f'<Employee {self.employee_code} - {self.full_name}>'


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    check_in = db.Column(db.DateTime)
    check_out = db.Column(db.DateTime)
    total_hours = db.Column(db.Float)
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Attendance {self.employee_id} - {self.date}>'


class LeaveRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    leave_type = db.Column(db.Enum(LeaveType), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.Enum(LeaveStatus), default=LeaveStatus.PENDING)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    
    def __repr__(self):
        return f'<LeaveRequest {self.employee_id} - {self.start_date} to {self.end_date}>'


class CareerPath(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CareerPath {self.employee_id} - {self.position}>'


class AwardType(enum.Enum):
    INDIVIDUAL = "Danh hiệu cá nhân"
    COLLECTIVE = "Danh hiệu tập thể"
    CERTIFICATE = "Giấy chứng nhận"
    COMPETITION = "Giải thưởng cuộc thi"
    OTHER = "Khác"
    
# Danh sách các tỉnh thành Việt Nam để sử dụng cho dropdown quê quán
VIETNAM_PROVINCES = [
    "An Giang", "Bà Rịa - Vũng Tàu", "Bắc Giang", "Bắc Kạn", "Bạc Liêu",
    "Bắc Ninh", "Bến Tre", "Bình Định", "Bình Dương", "Bình Phước",
    "Bình Thuận", "Cà Mau", "Cần Thơ", "Cao Bằng", "Đà Nẵng",
    "Đắk Lắk", "Đắk Nông", "Điện Biên", "Đồng Nai", "Đồng Tháp",
    "Gia Lai", "Hà Giang", "Hà Nam", "Hà Nội", "Hà Tĩnh",
    "Hải Dương", "Hải Phòng", "Hậu Giang", "Hòa Bình", "Hưng Yên",
    "Khánh Hòa", "Kiên Giang", "Kon Tum", "Lai Châu", "Lâm Đồng",
    "Lạng Sơn", "Lào Cai", "Long An", "Nam Định", "Nghệ An",
    "Ninh Bình", "Ninh Thuận", "Phú Thọ", "Phú Yên", "Quảng Bình",
    "Quảng Nam", "Quảng Ngãi", "Quảng Ninh", "Quảng Trị", "Sóc Trăng",
    "Sơn La", "Tây Ninh", "Thái Bình", "Thái Nguyên", "Thanh Hóa",
    "Thừa Thiên Huế", "Tiền Giang", "TP Hồ Chí Minh", "Trà Vinh", "Tuyên Quang",
    "Vĩnh Long", "Vĩnh Phúc", "Yên Bái"
]


class CustomPosition(db.Model):
    """Quản lý vị trí/chức vụ tùy chỉnh ngoài enum Position"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CustomPosition {self.name}>'


class Award(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    award_type = db.Column(db.Enum(AwardType), default=AwardType.INDIVIDUAL, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    date_received = db.Column(db.Date)
    description = db.Column(db.Text)
    certificate_number = db.Column(db.String(100))
    issued_by = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Award {self.name} - {self.year}>'
        

class SalaryGrade(db.Model):
    """Bậc lương và hệ số lương"""
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    base_coefficient = db.Column(db.Float, nullable=False)
    base_salary = db.Column(db.Integer, nullable=False, default=1490000)  # Lương cơ sở mặc định
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Mối quan hệ với bảng nhân viên
    employees = db.relationship('EmployeeSalary', backref='salary_grade', lazy=True)
    
    def __repr__(self):
        return f'<SalaryGrade {self.code} - {self.name}>'
        
    @property
    def calculated_salary(self):
        """Tính toán mức lương dựa trên hệ số và lương cơ sở"""
        return int(self.base_coefficient * self.base_salary)


class EmployeeSalary(db.Model):
    """Lưu trữ lịch sử áp dụng bậc lương cho nhân viên"""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    salary_grade_id = db.Column(db.Integer, db.ForeignKey('salary_grade.id'), nullable=False)
    effective_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    additional_coefficient = db.Column(db.Float, default=0)  # Hệ số phụ cấp thêm
    reason = db.Column(db.Text)
    decision_number = db.Column(db.String(50))  # Số quyết định
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Mối quan hệ với bảng nhân viên
    employee = db.relationship('Employee', backref='salary_history', lazy=True)
    
    def __repr__(self):
        return f'<EmployeeSalary {self.employee_id} - {self.salary_grade_id}>'
        
    @property
    def total_coefficient(self):
        """Tổng hệ số lương (hệ số cơ bản + hệ số phụ cấp)"""
        return self.salary_grade.base_coefficient + self.additional_coefficient
        
    @property
    def calculated_salary(self):
        """Tính toán mức lương dựa trên tổng hệ số và lương cơ sở"""
        return int(self.total_coefficient * self.salary_grade.base_salary)


class WorkScheduleStatus(enum.Enum):
    """Trạng thái lịch công tác"""
    PENDING = "Chờ phê duyệt"
    APPROVED = "Đã duyệt"
    REJECTED = "Từ chối"
    COMPLETED = "Đã hoàn thành"
    CANCELLED = "Đã hủy"


class WorkScheduleType(enum.Enum):
    """Loại lịch công tác"""
    MEETING = "Cuộc họp"
    BUSINESS_TRIP = "Công tác"
    TRAINING = "Đào tạo"
    CUSTOMER_VISIT = "Gặp khách hàng"
    FIELD_WORK = "Công việc hiện trường"
    OTHER = "Khác"


class WorkSchedule(db.Model):
    """Lịch công tác"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    schedule_type = db.Column(db.Enum(WorkScheduleType), default=WorkScheduleType.OTHER, nullable=False)
    location = db.Column(db.String(200))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.Enum(WorkScheduleStatus), default=WorkScheduleStatus.PENDING, nullable=False)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    reviewed_at = db.Column(db.DateTime)
    feedback = db.Column(db.Text)  # Phản hồi từ người duyệt
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Mối quan hệ
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_schedules')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    participants = db.relationship('WorkScheduleParticipant', backref='work_schedule', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<WorkSchedule {self.title} - {self.start_time.strftime("%Y-%m-%d")}>)>'


class WorkScheduleParticipant(db.Model):
    """Người tham gia lịch công tác"""
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('work_schedule.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    is_required = db.Column(db.Boolean, default=True)  # Bắt buộc hay không bắt buộc
    confirmation_status = db.Column(db.Boolean, default=None)  # None: Chưa phản hồi, True: Đồng ý, False: Từ chối
    confirmation_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Mối quan hệ
    employee = db.relationship('Employee', backref='schedule_participations')
    
    def __repr__(self):
        return f'<WorkScheduleParticipant {self.employee_id} - {self.schedule_id}>'


class PerformanceRatingPeriod(enum.Enum):
    """Kỳ đánh giá hiệu suất"""
    MONTHLY = "Hàng tháng"
    QUARTERLY = "Hàng quý"
    BIANNUAL = "Nửa năm"
    ANNUAL = "Hàng năm"
    OTHER = "Khác"


class PerformanceRatingStatus(enum.Enum):
    """Trạng thái đánh giá"""
    DRAFT = "Bản nháp"
    SUBMITTED = "Đã nộp"
    MANAGER_REVIEWED = "Quản lý đã xem xét"
    COMPLETED = "Hoàn thành"
    CANCELLED = "Đã hủy"


class PerformanceEvaluationCriteria(db.Model):
    """Tiêu chí đánh giá hiệu suất"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    max_score = db.Column(db.Integer, default=10)
    weight = db.Column(db.Float, default=1.0)  # Trọng số
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))  # Có thể đặc thù theo phòng ban
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Mối quan hệ
    department = db.relationship('Department', backref='performance_criterias')
    creator = db.relationship('User', backref='created_criterias')
    
    def __repr__(self):
        return f'<PerformanceEvaluationCriteria {self.name}>'


class PerformanceEvaluation(db.Model):
    """Đánh giá hiệu suất nhân viên"""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Người đánh giá
    evaluation_period = db.Column(db.Enum(PerformanceRatingPeriod), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    overall_score = db.Column(db.Float)  # Điểm tổng hợp
    status = db.Column(db.Enum(PerformanceRatingStatus), default=PerformanceRatingStatus.DRAFT)
    comments = db.Column(db.Text)  # Nhận xét tổng quát
    employee_comments = db.Column(db.Text)  # Phản hồi của nhân viên
    strengths = db.Column(db.Text)  # Điểm mạnh
    areas_for_improvement = db.Column(db.Text)  # Lĩnh vực cần cải thiện
    goals_for_next_period = db.Column(db.Text)  # Mục tiêu cho kỳ tiếp theo
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # Người phê duyệt
    approved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Mối quan hệ
    employee = db.relationship('Employee', backref='performance_evaluations', foreign_keys=[employee_id])
    evaluator = db.relationship('User', backref='evaluations_given', foreign_keys=[evaluator_id])
    approver = db.relationship('User', backref='evaluations_approved', foreign_keys=[approved_by])
    criteria_scores = db.relationship('PerformanceEvaluationDetail', backref='evaluation', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<PerformanceEvaluation {self.employee_id} - {self.start_date} to {self.end_date}>'
    
    def calculate_overall_score(self):
        """Tính điểm tổng hợp dựa trên điểm và trọng số của từng tiêu chí"""
        if not self.criteria_scores:
            return None
            
        weighted_scores = [detail.score * detail.criteria.weight for detail in self.criteria_scores if detail.score is not None]
        total_weight = sum([detail.criteria.weight for detail in self.criteria_scores if detail.score is not None])
        
        if not weighted_scores or total_weight == 0:
            return None
            
        return sum(weighted_scores) / total_weight


class PerformanceEvaluationDetail(db.Model):
    """Chi tiết đánh giá theo từng tiêu chí"""
    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('performance_evaluation.id'), nullable=False)
    criteria_id = db.Column(db.Integer, db.ForeignKey('performance_evaluation_criteria.id'), nullable=False)
    score = db.Column(db.Float)  # Điểm số
    comments = db.Column(db.Text)  # Nhận xét cho tiêu chí này
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Mối quan hệ
    criteria = db.relationship('PerformanceEvaluationCriteria')
    
    def __repr__(self):
        return f'<PerformanceEvaluationDetail {self.evaluation_id} - {self.criteria_id}>'
