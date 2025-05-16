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
    
    def has_permission(self, permission_code):
        """
        Kiểm tra xem người dùng có quyền cụ thể hay không
        
        Args:
            permission_code (str): Mã quyền cần kiểm tra
        
        Returns:
            bool: True nếu người dùng có quyền, False nếu không
        """
        # Admin luôn có tất cả các quyền
        if self.is_admin():
            return True
        
        # Kiểm tra trong các vai trò tùy chỉnh của người dùng
        for role in self.custom_roles:
            if not role.is_active:
                continue
                
            for permission in role.permissions:
                if permission.code == permission_code:
                    return True
        
        return False
    
    def has_role(self, role_name):
        """
        Kiểm tra xem người dùng có vai trò cụ thể hay không
        
        Args:
            role_name (str): Tên vai trò cần kiểm tra
        
        Returns:
            bool: True nếu người dùng có vai trò, False nếu không
        """
        # Admin được coi là có tất cả các vai trò
        if self.is_admin():
            return True
            
        for role in self.custom_roles:
            if role.name == role_name and role.is_active:
                return True
                
        return False
    
    def get_all_permissions(self):
        """
        Lấy danh sách tất cả các quyền của người dùng
        
        Returns:
            list: Danh sách các đối tượng Permission
        """
        if self.is_admin():
            return Permission.query.all()
            
        permissions = []
        for role in self.custom_roles:
            if role.is_active:
                permissions.extend(role.permissions)
                
        # Loại bỏ các quyền trùng lặp
        unique_permissions = list({p.id: p for p in permissions}.values())
        return unique_permissions
    
    def __repr__(self):
        return f'<User {self.username}>'


class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employees = db.relationship('Employee', backref='department', lazy=True)
    job_positions = db.relationship('JobPosition', back_populates='department', lazy='dynamic')
    
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
    id_card_number = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    position = db.Column(db.String(100), default="Nhân viên")
    join_date = db.Column(db.Date, nullable=False)
    salary_grade = db.Column(db.String(20))
    salary_coefficient = db.Column(db.Float)
    contract_start_date = db.Column(db.Date)
    contract_end_date = db.Column(db.Date)
    education_level = db.Column(db.Enum(EducationLevel), default=EducationLevel.OTHER)
    university_name = db.Column(db.String(200))
    university_major = db.Column(db.String(200))
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
    
    # Asset Management relationships
    asset_assignments = db.relationship('AssetAssignment', back_populates='employee', lazy='dynamic')
    
    # Contract Management relationships
    contracts = db.relationship('Contract', back_populates='employee', lazy='dynamic')
    
    # Document Management relationships
    documents = db.relationship('Document', back_populates='employee', lazy='dynamic')
    
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


class TaskStatus(enum.Enum):
    """Trạng thái nhiệm vụ trong kanban"""
    TODO = "Cần làm"
    IN_PROGRESS = "Đang thực hiện"
    REVIEW = "Đang kiểm tra"
    DONE = "Hoàn thành"
    

class TaskPriority(enum.Enum):
    """Mức độ ưu tiên của nhiệm vụ"""
    LOW = "Thấp"
    NORMAL = "Bình thường"
    HIGH = "Cao"
    URGENT = "Khẩn cấp"


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


class Task(db.Model):
    """Mô hình nhiệm vụ cho Kanban board"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.Enum(TaskStatus), default=TaskStatus.TODO, nullable=False)
    priority = db.Column(db.Enum(TaskPriority), default=TaskPriority.NORMAL, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('employee.id'))
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    work_schedule_id = db.Column(db.Integer, db.ForeignKey('work_schedule.id'))
    deadline = db.Column(db.DateTime)
    estimated_hours = db.Column(db.Float)  # Số giờ dự kiến
    actual_hours = db.Column(db.Float)  # Số giờ thực tế
    order_in_status = db.Column(db.Integer, default=0)  # Thứ tự trong cột
    labels = db.Column(db.String(255))  # Nhãn phân loại, lưu dạng chuỗi phân tách bằng dấu phẩy
    progress = db.Column(db.Integer, default=0)  # Tiến độ (%)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Mối quan hệ
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_tasks')
    assignee = db.relationship('Employee', foreign_keys=[assigned_to], backref='assigned_tasks')
    department = db.relationship('Department', backref='department_tasks')
    work_schedule = db.relationship('WorkSchedule', backref='related_tasks')
    comments = db.relationship('TaskComment', backref='task', lazy=True, cascade="all, delete-orphan")
    attachments = db.relationship('TaskAttachment', backref='task', lazy=True, cascade="all, delete-orphan")
    
    @property
    def is_overdue(self):
        """Kiểm tra xem nhiệm vụ có bị quá hạn không"""
        if not self.deadline:
            return False
        return self.deadline < datetime.utcnow() and self.status != TaskStatus.DONE
    
    @property
    def days_remaining(self):
        """Số ngày còn lại đến deadline"""
        if not self.deadline:
            return None
        remaining = self.deadline - datetime.utcnow()
        return max(0, remaining.days)
    
    @property
    def status_display(self):
        """Hiển thị trạng thái"""
        return self.status.value if self.status else ""
    
    @property
    def priority_display(self):
        """Hiển thị mức độ ưu tiên"""
        return self.priority.value if self.priority else ""
    
    @property
    def labels_list(self):
        """Chuyển đổi chuỗi nhãn thành danh sách"""
        if not self.labels:
            return []
        return [label.strip() for label in self.labels.split(',')]
        
    def get_dependent_tasks(self):
        """Lấy danh sách các nhiệm vụ phụ thuộc vào nhiệm vụ này"""
        dependencies = TaskDependency.query.filter_by(task_id=self.id).all()
        dependent_task_ids = [dep.dependent_task_id for dep in dependencies]
        return Task.query.filter(Task.id.in_(dependent_task_ids)).all()
    
    def get_blocking_tasks(self):
        """Lấy danh sách các nhiệm vụ mà nhiệm vụ này phụ thuộc vào"""
        dependencies = TaskDependency.query.filter_by(dependent_task_id=self.id).all()
        blocking_task_ids = [dep.task_id for dep in dependencies]
        return Task.query.filter(Task.id.in_(blocking_task_ids)).all()
    
    def __repr__(self):
        return f'<Task {self.id}: {self.title} - {self.status_display}>'


class TaskComment(db.Model):
    """Bình luận cho nhiệm vụ"""
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Mối quan hệ
    author = db.relationship('User', backref='task_comments')
    
    def __repr__(self):
        return f'<TaskComment {self.id} - Task {self.task_id}>'


class TaskAttachment(db.Model):
    """Tệp đính kèm cho nhiệm vụ"""
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # Kích thước tệp (bytes)
    file_type = db.Column(db.String(100))  # Loại tệp (pdf, doc, jpg, ...)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Mối quan hệ
    uploader = db.relationship('User', backref='uploaded_attachments')
    
    def __repr__(self):
        return f'<TaskAttachment {self.id} - {self.file_name}>'


class TaskDependency(db.Model):
    """Quan hệ phụ thuộc giữa các nhiệm vụ"""
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)  # Nhiệm vụ gốc
    dependent_task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)  # Nhiệm vụ phụ thuộc
    dependency_type = db.Column(db.String(50), default="blocks")  # Loại phụ thuộc: 'blocks', 'relates_to', 'duplicates', etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TaskDependency {self.task_id} -> {self.dependent_task_id} ({self.dependency_type})>'


# Asset Management Models
class AssetCategory(enum.Enum):
    """
    Danh mục tài sản (Enum cũ, giữ lại để tương thích)
    """
    COMPUTER = "Máy tính"
    LAPTOP = "Laptop"
    SMARTPHONE = "Điện thoại"
    TABLET = "Máy tính bảng"
    PRINTER = "Máy in"
    SCANNER = "Máy quét"
    FURNITURE = "Nội thất văn phòng"
    OTHER = "Khác"
    
class AssetCategoryModel(db.Model):
    """
    Mô hình danh mục tài sản (thay thế Enum)
    """
    __tablename__ = 'asset_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Các tài sản sẽ được liên kết sau khi mô hình Asset được cập nhật
    
    def __repr__(self):
        return f'<AssetCategory {self.name}>'
    
class MaintenanceType(enum.Enum):
    """Loại bảo trì"""
    PREVENTIVE = "Bảo trì định kỳ"
    CORRECTIVE = "Sửa chữa"
    UPGRADE = "Nâng cấp"
    INSPECTION = "Kiểm tra"
    OTHER = "Khác"


class MaintenanceStatus(enum.Enum):
    """Trạng thái bảo trì"""
    SCHEDULED = "Đã lên lịch"
    IN_PROGRESS = "Đang thực hiện"
    COMPLETED = "Hoàn thành"
    CANCELLED = "Đã hủy"


class AssetStatus(enum.Enum):
    AVAILABLE = "Sẵn sàng sử dụng"
    ASSIGNED = "Đã bàn giao"
    UNDER_MAINTENANCE = "Đang bảo trì"
    BROKEN = "Hỏng"
    DISCARDED = "Đã thanh lý"


class Asset(db.Model):
    __tablename__ = 'assets'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.Enum(AssetCategory), nullable=False)
    status = db.Column(db.Enum(AssetStatus), default=AssetStatus.AVAILABLE, nullable=False)
    serial_number = db.Column(db.String(50), nullable=True)
    purchase_date = db.Column(db.Date, nullable=True)
    purchase_price = db.Column(db.Float, nullable=True)
    warranty_expiry = db.Column(db.Date, nullable=True)
    warranty_info = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(255), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    assignee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    assignments = db.relationship('AssetAssignment', back_populates='asset', lazy='dynamic')
    maintenance_records = db.relationship('AssetMaintenance', back_populates='asset', lazy='dynamic')
    department = db.relationship('Department', backref=db.backref('assets', lazy='dynamic'))
    assignee = db.relationship('Employee', backref=db.backref('assigned_assets', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Asset {self.asset_code}: {self.name}>'


class AssetAssignment(db.Model):
    __tablename__ = 'asset_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    assigned_date = db.Column(db.Date, nullable=False, default=date.today)
    return_date = db.Column(db.Date, nullable=True)
    assigned_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    condition_on_assignment = db.Column(db.Text, nullable=True)
    condition_on_return = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    is_returned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    asset = db.relationship('Asset', back_populates='assignments')
    employee = db.relationship('Employee', back_populates='asset_assignments')
    assigned_by = db.relationship('User')
    
    def __repr__(self):
        return f'<AssetAssignment {self.asset.name} to {self.employee.full_name}>'


class AssetMaintenance(db.Model):
    __tablename__ = 'asset_maintenance'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    maintenance_date = db.Column(db.Date, nullable=False)
    maintenance_type = db.Column(db.String(50), nullable=False)
    performed_by = db.Column(db.String(100), nullable=True)
    cost = db.Column(db.Float, nullable=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="Hoàn thành", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    asset = db.relationship('Asset', back_populates='maintenance_records')
    
    def __repr__(self):
        return f'<AssetMaintenance {self.asset.name} on {self.maintenance_date}>'


# Recruitment Management Models
class JobOpeningStatus(enum.Enum):
    DRAFT = "Nháp"
    OPEN = "Đang mở"
    CLOSED = "Đã đóng"
    ON_HOLD = "Tạm hoãn"


class JobPosition(db.Model):
    __tablename__ = 'job_positions'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    required_experience = db.Column(db.String(100), nullable=True)
    education_requirement = db.Column(db.String(100), nullable=True)
    job_description = db.Column(db.Text, nullable=True)
    responsibilities = db.Column(db.Text, nullable=True)
    skills_required = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    department = db.relationship('Department', back_populates='job_positions')
    job_openings = db.relationship('JobOpening', back_populates='position', lazy='dynamic')
    
    def __repr__(self):
        return f'<JobPosition {self.title}>'


class JobOpening(db.Model):
    __tablename__ = 'job_openings'
    
    id = db.Column(db.Integer, primary_key=True)
    position_id = db.Column(db.Integer, db.ForeignKey('job_positions.id'), nullable=False)
    number_of_openings = db.Column(db.Integer, default=1, nullable=False)
    status = db.Column(db.Enum(JobOpeningStatus), default=JobOpeningStatus.OPEN, nullable=False)
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    end_date = db.Column(db.Date, nullable=True)
    salary_range = db.Column(db.String(100), nullable=True)
    work_location = db.Column(db.String(100), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    position = db.relationship('JobPosition', back_populates='job_openings')
    created_by = db.relationship('User')
    candidates = db.relationship('Candidate', back_populates='job_opening', lazy='dynamic')
    
    def __repr__(self):
        return f'<JobOpening {self.position.title} - {self.status.value}>'


class CandidateStatus(enum.Enum):
    APPLIED = "Đã ứng tuyển"
    SCREENING = "Đang sàng lọc"
    INTERVIEW_SCHEDULED = "Đã lên lịch phỏng vấn"
    INTERVIEWED = "Đã phỏng vấn"
    OFFER_SENT = "Đã gửi đề nghị"
    HIRED = "Đã tuyển dụng"
    REJECTED = "Từ chối"
    WITHDRAWN = "Ứng viên rút lui"


class Candidate(db.Model):
    __tablename__ = 'candidates'
    
    id = db.Column(db.Integer, primary_key=True)
    job_opening_id = db.Column(db.Integer, db.ForeignKey('job_openings.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    cv_file = db.Column(db.String(255), nullable=True)
    cover_letter = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum(CandidateStatus), default=CandidateStatus.APPLIED, nullable=False)
    application_date = db.Column(db.Date, default=date.today, nullable=False)
    evaluation = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    job_opening = db.relationship('JobOpening', back_populates='candidates')
    interviews = db.relationship('Interview', back_populates='candidate', lazy='dynamic')
    
    def __repr__(self):
        return f'<Candidate {self.full_name} for {self.job_opening.position.title}>'


class InterviewType(enum.Enum):
    PHONE = "Phỏng vấn điện thoại"
    VIDEO = "Phỏng vấn video"
    IN_PERSON = "Phỏng vấn trực tiếp"
    TECHNICAL = "Phỏng vấn kỹ thuật"
    GROUP = "Phỏng vấn nhóm"


class InterviewStatus(enum.Enum):
    SCHEDULED = "Đã lên lịch"
    COMPLETED = "Đã hoàn thành"
    CANCELED = "Đã hủy"
    RESCHEDULED = "Đã lên lịch lại"


class Interview(db.Model):
    __tablename__ = 'interviews'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    scheduled_date = db.Column(db.DateTime, nullable=False)
    interview_type = db.Column(db.Enum(InterviewType), nullable=False)
    interviewers = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    status = db.Column(db.Enum(InterviewStatus), default=InterviewStatus.SCHEDULED, nullable=False)
    feedback = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Integer, nullable=True)  # 1-5 rating
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    candidate = db.relationship('Candidate', back_populates='interviews')
    
    def __repr__(self):
        return f'<Interview for {self.candidate.full_name} on {self.scheduled_date}>'


# Contract Management Models
class ContractType(enum.Enum):
    PROBATION = "Thử việc"
    FIXED_TERM = "Xác định thời hạn"
    INDEFINITE = "Không xác định thời hạn"
    PART_TIME = "Bán thời gian"
    SEASONAL = "Thời vụ"


class ContractStatus(enum.Enum):
    DRAFT = "Bản nháp"
    ACTIVE = "Đang hiệu lực"
    EXPIRED = "Hết hạn"
    TERMINATED = "Chấm dứt"


class Contract(db.Model):
    __tablename__ = 'contracts'
    
    id = db.Column(db.Integer, primary_key=True)
    contract_number = db.Column(db.String(50), unique=True, nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    contract_type = db.Column(db.Enum(ContractType), nullable=False)
    status = db.Column(db.Enum(ContractStatus), default=ContractStatus.DRAFT, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    job_title = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    base_salary = db.Column(db.Float, nullable=False)
    working_hours = db.Column(db.String(50), nullable=True)
    contract_file = db.Column(db.String(255), nullable=True)
    signed_date = db.Column(db.Date, nullable=True)
    terminated_date = db.Column(db.Date, nullable=True)
    termination_reason = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    employee = db.relationship('Employee', back_populates='contracts')
    department = db.relationship('Department')
    created_by = db.relationship('User')
    amendments = db.relationship('ContractAmendment', back_populates='contract', lazy='dynamic')
    
    def __repr__(self):
        return f'<Contract {self.contract_number} for {self.employee.full_name}>'


class ContractAmendment(db.Model):
    __tablename__ = 'contract_amendments'
    
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), nullable=False)
    amendment_number = db.Column(db.String(50), nullable=False)
    amendment_date = db.Column(db.Date, nullable=False)
    effective_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=False)
    changes = db.Column(db.Text, nullable=False)
    amendment_file = db.Column(db.String(255), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    contract = db.relationship('Contract', back_populates='amendments')
    created_by = db.relationship('User')
    
    def __repr__(self):
        return f'<ContractAmendment {self.amendment_number} for Contract {self.contract.contract_number}>'


class DocumentType(enum.Enum):
    CV = "Sơ yếu lý lịch"
    ID_CARD = "CMND/CCCD"
    DEGREE = "Bằng cấp"
    CERTIFICATE = "Chứng chỉ"
    HEALTH_CERTIFICATE = "Giấy khám sức khỏe"
    TAX_CODE = "Mã số thuế"
    INSURANCE_CARD = "Thẻ bảo hiểm"
    OTHER = "Khác"


class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    document_type = db.Column(db.Enum(DocumentType), nullable=False)
    document_number = db.Column(db.String(100), nullable=True)
    issue_date = db.Column(db.Date, nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)
    issue_place = db.Column(db.String(100), nullable=True)
    file_path = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    verified_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    verified_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    employee = db.relationship('Employee', back_populates='documents')
    verified_by = db.relationship('User')
    
    def __repr__(self):
        return f'<Document {self.document_type.value} for {self.employee.full_name}>'


class NotificationEmail(db.Model):
    """Model để lưu danh sách email nhận thông báo"""
    __tablename__ = 'notification_emails'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    notification_types = db.Column(db.String(255), nullable=False, default="all")  # all, contracts, employees, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    created_by = db.relationship('User')
    
    def __repr__(self):
        return f'<NotificationEmail {self.email}>'


# Bảng quan hệ nhiều-nhiều giữa vai trò và quyền
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
)

# Bảng quan hệ nhiều-nhiều giữa người dùng và vai trò
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)


class Permission(db.Model):
    """Mô hình lưu trữ quyền hạn trong hệ thống"""
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    module = db.Column(db.String(100), nullable=False)  # Phân loại theo module
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Permission {self.name}>'


class Role(db.Model):
    """Mô hình lưu trữ vai trò trong hệ thống"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    permissions = db.relationship('Permission', secondary=role_permissions, 
                                 backref=db.backref('roles', lazy='dynamic'))
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    users = db.relationship('User', secondary=user_roles, 
                           backref=db.backref('custom_roles', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Role {self.name}>'

