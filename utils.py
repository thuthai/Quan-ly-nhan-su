import os
from datetime import datetime, timedelta
import random
from werkzeug.utils import secure_filename
from models import User, Department, Employee, Gender, EmployeeStatus, UserRole, LeaveRequest, LeaveType, LeaveStatus, Attendance, CareerPath
from app import db
import pandas as pd
import uuid
from flask import current_app


def today_date():
    """Return today's date as a datetime.date object"""
    return datetime.now().date()

def seed_database():
    """Seed the database with initial data if it's empty"""
    # Check if database is already seeded
    if Department.query.count() > 0:
        return
    
    # Create departments
    departments = [
        {"name": "Ban Giám đốc", "description": "Ban quản lý cấp cao nhất của công ty"},
        {"name": "Phòng Nhân sự", "description": "Quản lý nhân viên và tuyển dụng"},
        {"name": "Phòng Kế toán", "description": "Quản lý tài chính và kế toán"},
        {"name": "Phòng Kinh doanh", "description": "Bán hàng và phát triển kinh doanh"},
        {"name": "Phòng IT", "description": "Phát triển phần mềm và hỗ trợ kỹ thuật"}
    ]
    
    for dept in departments:
        department = Department(name=dept["name"], description=dept["description"])
        db.session.add(department)
    
    db.session.commit()
    
    # Create admin user
    admin = User(
        username="admin",
        email="admin@company.com",
        role=UserRole.ADMIN
    )
    admin.set_password("admin123")
    db.session.add(admin)
    
    # Create sample employees
    sample_employees = [
        {
            "username": "nguyenvan",
            "email": "nguyenvan@company.com",
            "password": "password123",
            "employee_data": {
                "employee_code": "NV001",
                "full_name": "Nguyễn Văn A",
                "gender": Gender.MALE,
                "date_of_birth": datetime(1985, 5, 15).date(),
                "home_town": "Hà Nội",
                "address": "123 Đường Lê Lợi, Hà Nội",
                "phone_number": "0912345678",
                "department_id": 2,  # Phòng Nhân sự
                "position": "Trưởng phòng Nhân sự",
                "join_date": datetime(2015, 1, 10).date(),
                "salary_grade": "A2",
                "salary_coefficient": 4.5,
                "contract_start_date": datetime(2020, 1, 1).date(),
                "contract_end_date": datetime(2023, 12, 31).date(),
                "education_level": "Đại học",
                "skills": "Quản lý nhân sự, Tuyển dụng, Đào tạo",
                "profile_image": "https://images.unsplash.com/photo-1522071820081-009f0129c71c",
                "status": EmployeeStatus.ACTIVE
            }
        },
        {
            "username": "tranthiB",
            "email": "tranthib@company.com",
            "password": "password123",
            "employee_data": {
                "employee_code": "NV002",
                "full_name": "Trần Thị B",
                "gender": Gender.FEMALE,
                "date_of_birth": datetime(1990, 8, 20).date(),
                "home_town": "Hồ Chí Minh",
                "address": "456 Đường Nguyễn Huệ, TP.HCM",
                "phone_number": "0987654321",
                "department_id": 3,  # Phòng Kế toán
                "position": "Kế toán trưởng",
                "join_date": datetime(2017, 3, 15).date(),
                "salary_grade": "B1",
                "salary_coefficient": 3.8,
                "contract_start_date": datetime(2021, 4, 1).date(),
                "contract_end_date": datetime(2024, 3, 31).date(),
                "education_level": "Thạc sĩ",
                "skills": "Kế toán, Kiểm toán, Tài chính",
                "profile_image": "https://images.unsplash.com/photo-1523240795612-9a054b0db644",
                "status": EmployeeStatus.ACTIVE
            }
        },
        {
            "username": "lequoc",
            "email": "lequoc@company.com",
            "password": "password123",
            "employee_data": {
                "employee_code": "NV003",
                "full_name": "Lê Quốc C",
                "gender": Gender.MALE,
                "date_of_birth": datetime(1988, 12, 5).date(),
                "home_town": "Đà Nẵng",
                "address": "789 Đường Trần Phú, Đà Nẵng",
                "phone_number": "0965432109",
                "department_id": 4,  # Phòng Kinh doanh
                "position": "Giám đốc kinh doanh",
                "join_date": datetime(2016, 7, 1).date(),
                "salary_grade": "A1",
                "salary_coefficient": 5.0,
                "contract_start_date": datetime(2019, 8, 1).date(),
                "contract_end_date": datetime(2023, 7, 31).date(),
                "education_level": "Đại học",
                "skills": "Quản lý bán hàng, Đàm phán, Phát triển thị trường",
                "profile_image": "https://images.unsplash.com/photo-1552581234-26160f608093",
                "status": EmployeeStatus.ACTIVE
            }
        },
        {
            "username": "phamthid",
            "email": "phamthid@company.com",
            "password": "password123",
            "employee_data": {
                "employee_code": "NV004",
                "full_name": "Phạm Thị D",
                "gender": Gender.FEMALE,
                "date_of_birth": datetime(1992, 4, 25).date(),
                "home_town": "Cần Thơ",
                "address": "101 Đường 30/4, Cần Thơ",
                "phone_number": "0932156789",
                "department_id": 5,  # Phòng IT
                "position": "Lập trình viên senior",
                "join_date": datetime(2018, 9, 1).date(),
                "salary_grade": "B2",
                "salary_coefficient": 4.2,
                "contract_start_date": datetime(2022, 1, 1).date(),
                "contract_end_date": datetime(2024, 12, 31).date(),
                "education_level": "Đại học",
                "skills": "Python, React, Node.js, SQL, DevOps",
                "profile_image": "https://images.unsplash.com/photo-1553877522-43269d4ea984",
                "status": EmployeeStatus.ACTIVE
            }
        },
        {
            "username": "hoanganh",
            "email": "hoanganh@company.com",
            "password": "password123",
            "employee_data": {
                "employee_code": "NV005",
                "full_name": "Hoàng Anh E",
                "gender": Gender.MALE,
                "date_of_birth": datetime(1980, 2, 10).date(),
                "home_town": "Hải Phòng",
                "address": "222 Đường Lê Chân, Hải Phòng",
                "phone_number": "0978123456",
                "department_id": 1,  # Ban Giám đốc
                "position": "Giám đốc điều hành",
                "join_date": datetime(2010, 1, 5).date(),
                "salary_grade": "S1",
                "salary_coefficient": 8.0,
                "contract_start_date": datetime(2020, 1, 1).date(),
                "contract_end_date": datetime(2025, 12, 31).date(),
                "education_level": "Tiến sĩ",
                "skills": "Quản lý cấp cao, Chiến lược kinh doanh, Tài chính",
                "profile_image": "https://images.unsplash.com/photo-1552793494-111afe03d0ca",
                "status": EmployeeStatus.ACTIVE
            }
        }
    ]
    
    for employee_data in sample_employees:
        user = User(
            username=employee_data["username"],
            email=employee_data["email"],
            role=UserRole.EMPLOYEE
        )
        user.set_password(employee_data["password"])
        db.session.add(user)
        db.session.flush()  # To get the user ID
        
        employee = Employee(
            user_id=user.id,
            **employee_data["employee_data"]
        )
        db.session.add(employee)
        
        # Create sample career path entries
        career_path = CareerPath(
            employee_id=employee.id,
            position=employee_data["employee_data"]["position"],
            start_date=employee_data["employee_data"]["join_date"],
            description="Vị trí ban đầu khi gia nhập công ty"
        )
        db.session.add(career_path)
    
    db.session.commit()
    
    # Create sample attendance data for the past month
    employees = Employee.query.all()
    today = datetime.now().date()
    one_month_ago = today - timedelta(days=30)
    
    for employee in employees:
        current_date = one_month_ago
        while current_date <= today:
            # Skip weekends
            if current_date.weekday() < 5:  # Monday to Friday
                # Random check-in time between 7:30 and 9:00
                check_in_hour = random.randint(7, 8)
                check_in_minute = random.randint(30, 59) if check_in_hour == 7 else random.randint(0, 30)
                check_in = datetime.combine(current_date, datetime.min.time().replace(hour=check_in_hour, minute=check_in_minute))
                
                # Random check-out time between 17:00 and 18:30
                check_out_hour = random.randint(17, 18)
                check_out_minute = random.randint(0, 30) if check_out_hour == 18 else random.randint(0, 59)
                check_out = datetime.combine(current_date, datetime.min.time().replace(hour=check_out_hour, minute=check_out_minute))
                
                total_hours = (check_out - check_in).total_seconds() / 3600
                
                attendance = Attendance(
                    employee_id=employee.id,
                    date=current_date,
                    check_in=check_in,
                    check_out=check_out,
                    total_hours=round(total_hours, 2)
                )
                db.session.add(attendance)
            
            current_date += timedelta(days=1)
    
    # Create sample leave requests
    leave_types = [LeaveType.ANNUAL, LeaveType.SICK, LeaveType.UNPAID]
    for employee in employees:
        # Past leave requests (approved)
        start_date = today - timedelta(days=random.randint(15, 25))
        end_date = start_date + timedelta(days=random.randint(1, 3))
        
        leave_request = LeaveRequest(
            employee_id=employee.id,
            leave_type=random.choice(leave_types),
            start_date=start_date,
            end_date=end_date,
            reason="Nghỉ phép cá nhân",
            status=LeaveStatus.APPROVED,
            reviewed_by=1,  # Admin user ID
            reviewed_at=datetime.now() - timedelta(days=random.randint(26, 30))
        )
        db.session.add(leave_request)
        
        # Future leave requests (pending)
        if random.random() > 0.5:  # 50% chance to have a pending request
            start_date = today + timedelta(days=random.randint(5, 15))
            end_date = start_date + timedelta(days=random.randint(1, 5))
            
            leave_request = LeaveRequest(
                employee_id=employee.id,
                leave_type=random.choice(leave_types),
                start_date=start_date,
                end_date=end_date,
                reason="Xin nghỉ phép theo kế hoạch",
                status=LeaveStatus.PENDING
            )
            db.session.add(leave_request)
    
    db.session.commit()


def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_profile_image(file):
    """Save profile image and return the path"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Generate a unique filename
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Ensure upload directory exists
        upload_dir = os.path.join('static', 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Return the path to be stored in the database
        return os.path.join('uploads', unique_filename)
    
    return None


def export_employees_to_excel():
    """Export employees data to Excel"""
    employees = Employee.query.all()
    departments = {dept.id: dept.name for dept in Department.query.all()}
    
    data = []
    for employee in employees:
        data.append({
            'Mã nhân viên': employee.employee_code,
            'Họ và tên': employee.full_name,
            'Giới tính': employee.gender.value,
            'Ngày sinh': employee.date_of_birth,
            'Quê quán': employee.home_town,
            'Địa chỉ': employee.address,
            'Số điện thoại': employee.phone_number,
            'Email': employee.email,
            'Phòng ban': departments.get(employee.department_id, ''),
            'Chức vụ': employee.position,
            'Ngày vào công ty': employee.join_date,
            'Bậc lương': employee.salary_grade,
            'Hệ số lương': employee.salary_coefficient,
            'Ngày bắt đầu hợp đồng': employee.contract_start_date,
            'Ngày kết thúc hợp đồng': employee.contract_end_date,
            'Trình độ học vấn': employee.education_level,
            'Kỹ năng': employee.skills,
            'Trạng thái': employee.status.value,
        })
    
    df = pd.DataFrame(data)
    
    # Ensure export directory exists
    export_dir = os.path.join('static', 'exports')
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
        
    # Generate unique filename
    filename = f"employees_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    file_path = os.path.join(export_dir, filename)
    
    # Export to Excel
    df.to_excel(file_path, index=False)
    
    return os.path.join('exports', filename)


def export_attendance_to_excel(start_date, end_date, employee_id=None):
    """Export attendance data to Excel"""
    query = db.session.query(
        Attendance.date,
        Employee.employee_code,
        Employee.full_name,
        Department.name.label('department_name'),
        Attendance.check_in,
        Attendance.check_out,
        Attendance.total_hours
    ).join(
        Employee, Attendance.employee_id == Employee.id
    ).join(
        Department, Employee.department_id == Department.id
    ).filter(
        Attendance.date.between(start_date, end_date)
    )
    
    if employee_id and employee_id > 0:
        query = query.filter(Attendance.employee_id == employee_id)
    
    attendances = query.order_by(Attendance.date.desc(), Employee.full_name).all()
    
    data = []
    for attendance in attendances:
        data.append({
            'Ngày': attendance.date,
            'Mã nhân viên': attendance.employee_code,
            'Họ và tên': attendance.full_name,
            'Phòng ban': attendance.department_name,
            'Giờ vào': attendance.check_in.strftime('%H:%M:%S') if attendance.check_in else '',
            'Giờ ra': attendance.check_out.strftime('%H:%M:%S') if attendance.check_out else '',
            'Tổng giờ': attendance.total_hours
        })
    
    df = pd.DataFrame(data)
    
    # Ensure export directory exists
    export_dir = os.path.join('static', 'exports')
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
        
    # Generate unique filename
    filename = f"attendance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    file_path = os.path.join(export_dir, filename)
    
    # Export to Excel
    df.to_excel(file_path, index=False)
    
    return os.path.join('exports', filename)


def process_employee_import(file, skip_header=True, update_existing=True, default_department_id=None):
    """Process employee import from Excel or CSV file
    
    Args:
        file: The uploaded file object
        skip_header: Whether to skip the first row as header
        update_existing: Whether to update existing employees
        default_department_id: Default department ID to use if not specified in file
        
    Returns:
        dict: Import results statistics and errors
    """
    # Save the uploaded file temporarily
    filename = secure_filename(file.filename)
    temp_path = os.path.join('static', 'uploads', f"temp_{filename}")
    file.save(temp_path)
    
    # Determine file type and read accordingly
    if filename.endswith('.csv'):
        df = pd.read_csv(temp_path)
    else:  # Excel files
        df = pd.read_excel(temp_path)
    
    # Skip header if needed
    if skip_header and len(df) > 0:
        df = df.iloc[1:]
        df = df.reset_index(drop=True)
    
    # Initialize counters and error list
    added = 0
    updated = 0
    skipped = 0
    errors = []
    
    # Define required fields
    required_fields = ['employee_code', 'full_name', 'email', 'gender', 'date_of_birth', 'join_date']
    
    # Process each row
    for index, row in df.iterrows():
        try:
            # Check for required fields
            missing_fields = [field for field in required_fields if field not in row or pd.isna(row[field])]
            if missing_fields:
                errors.append({
                    'row': index + 2 if skip_header else index + 1,  # +2 to account for 1-indexing and header
                    'message': f"Thiếu các trường bắt buộc: {', '.join(missing_fields)}"
                })
                skipped += 1
                continue
            
            # Check if employee already exists
            existing_employee = Employee.query.filter_by(employee_code=row['employee_code']).first()
            
            if existing_employee and not update_existing:
                errors.append({
                    'row': index + 2 if skip_header else index + 1,
                    'message': f"Nhân viên với mã {row['employee_code']} đã tồn tại và tùy chọn cập nhật không được chọn"
                })
                skipped += 1
                continue
            
            # Process gender - accept both enum name and values
            gender_value = str(row['gender']).strip()
            gender = None
            for g in Gender:
                if gender_value == g.name or gender_value == g.value:
                    gender = g
                    break
            
            if not gender:
                errors.append({
                    'row': index + 2 if skip_header else index + 1,
                    'message': f"Giới tính không hợp lệ: {gender_value}. Phải là một trong: {', '.join([g.value for g in Gender])}"
                })
                skipped += 1
                continue
            
            # Parse dates
            try:
                dob = pd.to_datetime(row['date_of_birth']).date()
                join_date = pd.to_datetime(row['join_date']).date()
            except:
                errors.append({
                    'row': index + 2 if skip_header else index + 1,
                    'message': "Lỗi định dạng ngày tháng. Vui lòng sử dụng định dạng YYYY-MM-DD"
                })
                skipped += 1
                continue
            
            # Process contract dates if provided
            contract_start_date = None
            contract_end_date = None
            if 'contract_start_date' in row and not pd.isna(row['contract_start_date']):
                try:
                    contract_start_date = pd.to_datetime(row['contract_start_date']).date()
                except:
                    errors.append({
                        'row': index + 2 if skip_header else index + 1,
                        'message': "Lỗi định dạng ngày bắt đầu hợp đồng. Vui lòng sử dụng định dạng YYYY-MM-DD"
                    })
            
            if 'contract_end_date' in row and not pd.isna(row['contract_end_date']):
                try:
                    contract_end_date = pd.to_datetime(row['contract_end_date']).date()
                except:
                    errors.append({
                        'row': index + 2 if skip_header else index + 1,
                        'message': "Lỗi định dạng ngày kết thúc hợp đồng. Vui lòng sử dụng định dạng YYYY-MM-DD"
                    })
            
            # Validate contract dates
            if contract_start_date and contract_end_date and contract_start_date > contract_end_date:
                errors.append({
                    'row': index + 2 if skip_header else index + 1,
                    'message': "Ngày kết thúc hợp đồng phải sau ngày bắt đầu"
                })
                skipped += 1
                continue
            
            # Determine department ID
            department_id = None
            if 'department_id' in row and not pd.isna(row['department_id']):
                try:
                    dept_id = int(row['department_id'])
                    # Verify department exists
                    if Department.query.get(dept_id):
                        department_id = dept_id
                    else:
                        errors.append({
                            'row': index + 2 if skip_header else index + 1,
                            'message': f"Phòng ban với ID {dept_id} không tồn tại"
                        })
                except:
                    errors.append({
                        'row': index + 2 if skip_header else index + 1,
                        'message': f"ID phòng ban không hợp lệ: {row['department_id']}"
                    })
            
            # Use default department if provided and no department in the file
            if not department_id and default_department_id and default_department_id > 0:
                department_id = default_department_id
            
            # If no department ID available, skip the record
            if not department_id:
                errors.append({
                    'row': index + 2 if skip_header else index + 1,
                    'message': "Không có ID phòng ban được chỉ định và không có mặc định"
                })
                skipped += 1
                continue
            
            # Create or update employee
            if existing_employee and update_existing:
                # Update existing employee
                existing_employee.full_name = row['full_name']
                existing_employee.gender = gender
                existing_employee.date_of_birth = dob
                existing_employee.email = row['email']
                existing_employee.department_id = department_id
                existing_employee.join_date = join_date
                
                # Update optional fields if provided
                if 'home_town' in row and not pd.isna(row['home_town']):
                    existing_employee.home_town = row['home_town']
                if 'address' in row and not pd.isna(row['address']):
                    existing_employee.address = row['address'] 
                if 'phone_number' in row and not pd.isna(row['phone_number']):
                    existing_employee.phone_number = row['phone_number']
                if 'position' in row and not pd.isna(row['position']):
                    existing_employee.position = row['position']
                if 'salary_grade' in row and not pd.isna(row['salary_grade']):
                    existing_employee.salary_grade = row['salary_grade']
                if 'salary_coefficient' in row and not pd.isna(row['salary_coefficient']):
                    try:
                        existing_employee.salary_coefficient = float(row['salary_coefficient'])
                    except:
                        pass
                if contract_start_date:
                    existing_employee.contract_start_date = contract_start_date
                if contract_end_date:
                    existing_employee.contract_end_date = contract_end_date
                if 'education_level' in row and not pd.isna(row['education_level']):
                    existing_employee.education_level = row['education_level']
                if 'skills' in row and not pd.isna(row['skills']):
                    existing_employee.skills = row['skills']
                if 'status' in row and not pd.isna(row['status']):
                    status_value = str(row['status']).strip()
                    for s in EmployeeStatus:
                        if status_value == s.name or status_value == s.value:
                            existing_employee.status = s
                            break
                
                updated += 1
            else:
                # Create new employee
                employee = Employee(
                    employee_code=row['employee_code'],
                    full_name=row['full_name'],
                    gender=gender,
                    date_of_birth=dob,
                    email=row['email'],
                    department_id=department_id,
                    join_date=join_date,
                    status=EmployeeStatus.ACTIVE  # Default status
                )
                
                # Set optional fields if provided
                if 'home_town' in row and not pd.isna(row['home_town']):
                    employee.home_town = row['home_town']
                if 'address' in row and not pd.isna(row['address']):
                    employee.address = row['address'] 
                if 'phone_number' in row and not pd.isna(row['phone_number']):
                    employee.phone_number = row['phone_number']
                if 'position' in row and not pd.isna(row['position']):
                    employee.position = row['position']
                if 'salary_grade' in row and not pd.isna(row['salary_grade']):
                    employee.salary_grade = row['salary_grade']
                if 'salary_coefficient' in row and not pd.isna(row['salary_coefficient']):
                    try:
                        employee.salary_coefficient = float(row['salary_coefficient'])
                    except:
                        pass
                if contract_start_date:
                    employee.contract_start_date = contract_start_date
                if contract_end_date:
                    employee.contract_end_date = contract_end_date
                if 'education_level' in row and not pd.isna(row['education_level']):
                    employee.education_level = row['education_level']
                if 'skills' in row and not pd.isna(row['skills']):
                    employee.skills = row['skills']
                if 'status' in row and not pd.isna(row['status']):
                    status_value = str(row['status']).strip()
                    for s in EmployeeStatus:
                        if status_value == s.name or status_value == s.value:
                            employee.status = s
                            break
                
                db.session.add(employee)
                added += 1
        
        except Exception as e:
            # Catch any other errors
            errors.append({
                'row': index + 2 if skip_header else index + 1,
                'message': f"Lỗi không xác định: {str(e)}"
            })
            skipped += 1
    
    # Commit changes to database
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        errors.append({
            'row': 0,
            'message': f"Lỗi cơ sở dữ liệu: {str(e)}"
        })
    
    # Delete temporary file
    try:
        os.remove(temp_path)
    except:
        pass
    
    # Return results
    return {
        'total': len(df),
        'added': added,
        'updated': updated,
        'skipped': skipped,
        'errors': errors
    }


def create_sample_import_file():
    """Create a sample import file with headers and example rows
    
    Returns:
        str: Path to the created sample file
    """
    # Define sample data
    data = {
        'employee_code': ['NV001', 'NV002'],
        'full_name': ['Nguyễn Văn A', 'Trần Thị B'],
        'gender': ['Nam', 'Nữ'],
        'date_of_birth': ['1990-01-15', '1992-05-20'],
        'home_town': ['Hà Nội', 'TP.HCM'],
        'address': ['123 Đường Lê Lợi, Hà Nội', '456 Đường Nguyễn Huệ, TP.HCM'],
        'phone_number': ['0912345678', '0987654321'],
        'email': ['nguyenvana@company.com', 'tranthib@company.com'],
        'department_id': [2, 3],
        'position': ['Nhân viên kinh doanh', 'Kế toán viên'],
        'join_date': ['2022-03-15', '2022-06-01'],
        'salary_grade': ['A1', 'B2'],
        'salary_coefficient': [3.5, 4.0],
        'contract_start_date': ['2022-03-15', '2022-06-01'],
        'contract_end_date': ['2025-03-14', '2025-05-31'],
        'education_level': ['Đại học', 'Cao đẳng'],
        'skills': ['Quản lý bán hàng, Tiếng Anh', 'Kế toán, Excel'],
        'status': ['Đang làm việc', 'Đang làm việc']
    }
    
    df = pd.DataFrame(data)
    
    # Ensure export directory exists
    export_dir = os.path.join('static', 'exports')
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
        
    # Generate filename
    filename = "employee_import_sample.xlsx"
    file_path = os.path.join(export_dir, filename)
    
    # Export to Excel
    df.to_excel(file_path, index=False)
    
    return os.path.join('exports', filename)
