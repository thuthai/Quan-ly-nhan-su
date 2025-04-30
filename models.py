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


class LeaveStatus(enum.Enum):
    PENDING = "Đang chờ xét duyệt"
    APPROVED = "Đã duyệt"
    REJECTED = "Từ chối"


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
    position = db.Column(db.String(100))
    join_date = db.Column(db.Date, nullable=False)
    salary_grade = db.Column(db.String(20))
    salary_coefficient = db.Column(db.Float)
    contract_start_date = db.Column(db.Date)
    contract_end_date = db.Column(db.Date)
    education_level = db.Column(db.String(100))
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
