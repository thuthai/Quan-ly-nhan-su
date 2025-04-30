from flask import render_template, redirect, url_for, flash, request, jsonify, send_from_directory, abort, Response
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from datetime import datetime, date, timedelta
import os
import json
import pandas as pd
from sqlalchemy import func, desc

from app import app, db
from models import User, Department, Employee, Attendance, LeaveRequest, CareerPath, Gender, EmployeeStatus, UserRole, LeaveStatus, LeaveType, Award, AwardType, SalaryGrade, EmployeeSalary
from forms import (LoginForm, RegisterForm, DepartmentForm, EmployeeForm, EmployeeEditForm, 
                  LeaveRequestForm, CareerPathForm, AttendanceReportForm, EmployeeImportForm,
                  AwardForm, AwardEditForm, EmployeeFilterForm, 
                  SalaryGradeForm, SalaryGradeEditForm, EmployeeSalaryForm, EmployeeSalaryEditForm)
from utils import save_profile_image, export_employees_to_excel, export_attendance_to_excel, process_employee_import, create_sample_import_file


# Admin required decorator
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Bạn không có quyền truy cập trang này.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return login_required(decorated_function)


# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        # Get contract expiring alerts
        expiring_contracts = []
        if current_user.is_admin():
            expiring_contracts = Employee.query.filter(
                Employee.contract_end_date.isnot(None),
                Employee.contract_end_date > date.today(),
                Employee.contract_end_date <= date.today() + timedelta(days=30),
                Employee.status == EmployeeStatus.ACTIVE
            ).all()
        
        # Get pending leave requests
        pending_requests = []
        if current_user.is_admin():
            pending_requests = LeaveRequest.query.filter_by(status=LeaveStatus.PENDING).count()
        else:
            # Get employee ID
            employee = Employee.query.filter_by(user_id=current_user.id).first()
            if employee:
                # Check if employee has checked in today
                today_attendance = Attendance.query.filter_by(
                    employee_id=employee.id,
                    date=date.today()
                ).first()
                
                return render_template(
                    'index.html', 
                    employee=employee,
                    today_attendance=today_attendance,
                    today=date.today()
                )
        
        return render_template(
            'index.html', 
            expiring_contracts=expiring_contracts,
            pending_requests=pending_requests
        )
    
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Tên đăng nhập hoặc mật khẩu không chính xác.', 'danger')
            return redirect(url_for('login'))
        
        login_user(user)
        
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('index')
        
        return redirect(next_page)
    
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
@admin_required
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=UserRole.EMPLOYEE
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Tài khoản đã được tạo thành công!', 'success')
        return redirect(url_for('users'))
    
    return render_template('register.html', form=form)


@app.route('/admin')
@admin_required
def admin():
    # Số liệu người dùng
    user_count = User.query.count()
    admin_count = User.query.filter_by(role=UserRole.ADMIN).count()
    employee_user_count = User.query.filter_by(role=UserRole.EMPLOYEE).count()
    
    # Số liệu giả lập cho demo
    login_count = 15
    action_count = 78
    error_count = 2
    
    return render_template(
        'admin.html',
        user_count=user_count,
        admin_count=admin_count,
        employee_user_count=employee_user_count,
        login_count=login_count,
        action_count=action_count,
        error_count=error_count,
        today=date.today()
    )

@app.route('/users')
@admin_required
def users():
    users = User.query.all()
    return render_template('users.html', users=users)


@app.route('/dashboard')
@login_required
def dashboard():
    # Department statistics
    departments = Department.query.all()
    dept_stats = []
    
    for dept in departments:
        employee_count = Employee.query.filter_by(department_id=dept.id, status=EmployeeStatus.ACTIVE).count()
        dept_stats.append({
            'name': dept.name,
            'count': employee_count
        })
    
    # Gender statistics
    male_count = Employee.query.filter_by(gender=Gender.MALE, status=EmployeeStatus.ACTIVE).count()
    female_count = Employee.query.filter_by(gender=Gender.FEMALE, status=EmployeeStatus.ACTIVE).count()
    other_count = Employee.query.filter_by(gender=Gender.OTHER, status=EmployeeStatus.ACTIVE).count()
    
    gender_stats = {
        'male': male_count,
        'female': female_count,
        'other': other_count
    }
    
    # Overall statistics
    total_employees = Employee.query.filter_by(status=EmployeeStatus.ACTIVE).count()
    total_departments = Department.query.count()
    leave_requests = LeaveRequest.query.filter_by(status=LeaveStatus.PENDING).count()
    
    # Get employees with contracts expiring in the next 30 days
    expiring_contracts = Employee.query.filter(
        Employee.contract_end_date.isnot(None),
        Employee.contract_end_date > date.today(),
        Employee.contract_end_date <= date.today() + timedelta(days=30),
        Employee.status == EmployeeStatus.ACTIVE
    ).count()
    
    overall_stats = {
        'total_employees': total_employees,
        'total_departments': total_departments,
        'leave_requests': leave_requests,
        'expiring_contracts': expiring_contracts
    }
    
    # Get attendance data for the past 30 days
    thirty_days_ago = date.today() - timedelta(days=30)
    attendance_data = db.session.query(
        Attendance.date, 
        db.func.count(Attendance.id).label('count')
    ).filter(
        Attendance.date >= thirty_days_ago
    ).group_by(
        Attendance.date
    ).order_by(
        Attendance.date
    ).all()
    
    attendance_stats = {
        'dates': [record.date.strftime('%d/%m') for record in attendance_data],
        'counts': [record.count for record in attendance_data]
    }
    
    return render_template(
        'dashboard.html',
        dept_stats=dept_stats,
        gender_stats=gender_stats,
        overall_stats=overall_stats,
        attendance_stats=attendance_stats
    )


# Department routes
@app.route('/departments')
@login_required
def departments():
    departments = Department.query.all()
    return render_template('departments/index.html', departments=departments)


@app.route('/departments/create', methods=['GET', 'POST'])
@admin_required
def create_department():
    form = DepartmentForm()
    if form.validate_on_submit():
        department = Department(
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(department)
        db.session.commit()
        flash('Phòng ban mới đã được tạo thành công!', 'success')
        return redirect(url_for('departments'))
    
    return render_template('departments/create.html', form=form)


@app.route('/departments/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_department(id):
    department = Department.query.get_or_404(id)
    form = DepartmentForm(obj=department)
    
    if form.validate_on_submit():
        department.name = form.name.data
        department.description = form.description.data
        db.session.commit()
        flash('Phòng ban đã được cập nhật thành công!', 'success')
        return redirect(url_for('departments'))
    
    return render_template('departments/edit.html', form=form, department=department)


@app.route('/departments/<int:id>/delete', methods=['POST'])
@admin_required
def delete_department(id):
    department = Department.query.get_or_404(id)
    
    # Check if department has employees
    if Employee.query.filter_by(department_id=id).count() > 0:
        flash('Không thể xóa phòng ban vì có nhân viên đang thuộc phòng ban này.', 'danger')
        return redirect(url_for('departments'))
    
    db.session.delete(department)
    db.session.commit()
    flash('Phòng ban đã được xóa thành công!', 'success')
    return redirect(url_for('departments'))


# Employee routes
@app.route('/employees')
@login_required
def employees():
    # Create the employee filter form
    filter_form = EmployeeFilterForm(request.args)
    
    # Get filter parameters
    search = request.args.get('search', '')
    keyword = request.args.get('keyword', '')
    department_id = request.args.get('department_id', type=int)
    gender = request.args.get('gender', '')
    status = request.args.get('status', '')
    home_town = request.args.get('home_town', '')
    age_min = request.args.get('age_min', '')
    age_max = request.args.get('age_max', '')
    join_date_from = request.args.get('join_date_from', '')
    join_date_to = request.args.get('join_date_to', '')
    education_level = request.args.get('education_level', '')
    
    query = Employee.query
    
    # Apply filters
    if search:
        # Legacy search support
        query = query.filter(
            db.or_(
                Employee.full_name.ilike(f'%{search}%'),
                Employee.employee_code.ilike(f'%{search}%')
            )
        )
    
    if keyword:
        # Advanced keyword search
        query = query.filter(
            db.or_(
                Employee.full_name.ilike(f'%{keyword}%'),
                Employee.employee_code.ilike(f'%{keyword}%'),
                Employee.position.ilike(f'%{keyword}%'),
                Employee.skills.ilike(f'%{keyword}%'),
                Employee.email.ilike(f'%{keyword}%')
            )
        )
    
    if department_id and department_id > 0:
        query = query.filter_by(department_id=department_id)
    
    if gender:
        query = query.filter_by(gender=Gender[gender])
    
    if status:
        query = query.filter_by(status=EmployeeStatus[status])
        
    if home_town:
        query = query.filter(Employee.home_town == home_town)
    
    # Filter by age
    if age_min:
        try:
            min_age = int(age_min)
            # Calculate the date for this age
            max_birth_date = date.today().replace(year=date.today().year - min_age)
            query = query.filter(Employee.date_of_birth <= max_birth_date)
        except ValueError:
            pass
    
    if age_max:
        try:
            max_age = int(age_max)
            # Calculate the date for this age
            min_birth_date = date.today().replace(year=date.today().year - max_age - 1)
            min_birth_date = min_birth_date.replace(year=min_birth_date.year + 1)
            query = query.filter(Employee.date_of_birth >= min_birth_date)
        except ValueError:
            pass
    
    # Filter by join date
    if join_date_from:
        try:
            from_date = datetime.strptime(join_date_from, '%Y-%m-%d').date()
            query = query.filter(Employee.join_date >= from_date)
        except ValueError:
            pass
    
    if join_date_to:
        try:
            to_date = datetime.strptime(join_date_to, '%Y-%m-%d').date()
            query = query.filter(Employee.join_date <= to_date)
        except ValueError:
            pass
            
    if education_level:
        query = query.filter(Employee.education_level.ilike(f'%{education_level}%'))
    
    # Get all employees with filters applied
    employees = query.all()
    
    # Get all departments for filter dropdown
    departments = Department.query.all()
    
    # Get all statuses for filter dropdown
    statuses = [(s.name, s.value) for s in EmployeeStatus]
    
    # Tính toán dữ liệu thống kê
    # 1. Thống kê theo giới tính
    gender_stats = {}
    for g in Gender:
        gender_stats[str(g.value)] = len([e for e in employees if e.gender == g])
    
    # 2. Thống kê theo trình độ học vấn
    education_stats = {}
    all_education_levels = db.session.query(Employee.education_level).distinct().all()
    for level in all_education_levels:
        if level[0]:  # Kiểm tra không phải None hoặc chuỗi rỗng
            # Chuyển enum thành chuỗi để tương thích với JSON
            level_key = level[0].name if hasattr(level[0], 'name') else str(level[0])
            education_stats[level_key] = len([e for e in employees if e.education_level == level[0]])
    
    # 3. Thống kê theo độ tuổi
    age_groups = {
        "Dưới 25 tuổi": 0,
        "25-35 tuổi": 0,
        "36-45 tuổi": 0,
        "Trên 45 tuổi": 0
    }
    
    for employee in employees:
        if employee.date_of_birth:
            age = date.today().year - employee.date_of_birth.year
            if age < 25:
                age_groups["Dưới 25 tuổi"] += 1
            elif age <= 35:
                age_groups["25-35 tuổi"] += 1
            elif age <= 45:
                age_groups["36-45 tuổi"] += 1
            else:
                age_groups["Trên 45 tuổi"] += 1
    
    return render_template(
        'employees/index.html', 
        employees=employees, 
        departments=departments,
        statuses=statuses,
        search=search,
        filter_form=filter_form,
        department_id=department_id,
        status=status,
        keyword=keyword,
        gender=gender,
        home_town=home_town,
        age_min=age_min,
        age_max=age_max,
        join_date_from=join_date_from,
        join_date_to=join_date_to,
        education_level=education_level,
        # Truyền dữ liệu thống kê cho template
        gender_stats=gender_stats,
        education_stats=education_stats,
        age_groups=age_groups
    )


@app.route('/employees/create', methods=['GET', 'POST'])
@admin_required
def create_employee():
    form = EmployeeForm()
    
    if form.validate_on_submit() and form.validate_contract_dates():
        # Handle profile image upload
        profile_image_path = None
        if form.profile_image.data:
            profile_image_path = save_profile_image(form.profile_image.data)
        
        # Create new employee
        employee = Employee(
            employee_code=form.employee_code.data,
            full_name=form.full_name.data,
            gender=Gender[form.gender.data],
            date_of_birth=form.date_of_birth.data,
            home_town=form.home_town.data,
            address=form.address.data,
            phone_number=form.phone_number.data,
            email=form.email.data,
            department_id=form.department_id.data,
            position=form.position.data,
            join_date=form.join_date.data,
            salary_grade=form.salary_grade.data,
            salary_coefficient=form.salary_coefficient.data,
            contract_start_date=form.contract_start_date.data,
            contract_end_date=form.contract_end_date.data,
            education_level=form.education_level.data,
            skills=form.skills.data,
            status=EmployeeStatus[form.status.data]
        )
        
        if profile_image_path:
            employee.profile_image = profile_image_path
        
        db.session.add(employee)
        db.session.commit()
        
        # Create initial career path entry
        career_path = CareerPath(
            employee_id=employee.id,
            position=form.position.data,
            start_date=form.join_date.data,
            description="Vị trí ban đầu khi gia nhập công ty"
        )
        db.session.add(career_path)
        db.session.commit()
        
        flash('Nhân viên mới đã được tạo thành công!', 'success')
        return redirect(url_for('employees'))
    
    return render_template('employees/create.html', form=form)


@app.route('/employees/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_employee(id):
    employee = Employee.query.get_or_404(id)
    form = EmployeeEditForm(obj=employee)
    form.employee_id.data = employee.id
    
    if form.validate_on_submit() and form.validate_contract_dates():
        # Handle profile image upload
        if form.profile_image.data:
            profile_image_path = save_profile_image(form.profile_image.data)
            if profile_image_path:
                employee.profile_image = profile_image_path
        
        # Update employee data
        employee.employee_code = form.employee_code.data
        employee.full_name = form.full_name.data
        employee.gender = Gender[form.gender.data]
        employee.date_of_birth = form.date_of_birth.data
        employee.home_town = form.home_town.data
        employee.address = form.address.data
        employee.phone_number = form.phone_number.data
        employee.email = form.email.data
        employee.department_id = form.department_id.data
        employee.position = form.position.data
        employee.join_date = form.join_date.data
        employee.salary_grade = form.salary_grade.data
        employee.salary_coefficient = form.salary_coefficient.data
        employee.contract_start_date = form.contract_start_date.data
        employee.contract_end_date = form.contract_end_date.data
        employee.education_level = form.education_level.data
        employee.skills = form.skills.data
        employee.status = EmployeeStatus[form.status.data]
        
        db.session.commit()
        flash('Thông tin nhân viên đã được cập nhật thành công!', 'success')
        return redirect(url_for('view_employee', id=employee.id))
    
    return render_template('employees/edit.html', form=form, employee=employee)


@app.route('/employees/<int:id>')
@login_required
def view_employee(id):
    employee = Employee.query.get_or_404(id)
    
    # Check if the current user has permission to view this employee
    if not current_user.is_admin() and (not current_user.employee or current_user.employee.id != id):
        flash('Bạn không có quyền xem thông tin của nhân viên này.', 'danger')
        return redirect(url_for('index'))
    
    career_paths = CareerPath.query.filter_by(employee_id=id).order_by(CareerPath.start_date.desc()).all()
    leave_requests = LeaveRequest.query.filter_by(employee_id=id).order_by(LeaveRequest.created_at.desc()).all()
    
    return render_template(
        'employees/view.html', 
        employee=employee, 
        career_paths=career_paths, 
        leave_requests=leave_requests
    )


@app.route('/employees/<int:id>/delete', methods=['POST'])
@admin_required
def delete_employee(id):
    employee = Employee.query.get_or_404(id)
    
    # Update status to LEAVE instead of deleting
    employee.status = EmployeeStatus.LEAVE
    db.session.commit()
    
    flash('Nhân viên đã được chuyển sang trạng thái nghỉ việc!', 'success')
    return redirect(url_for('employees'))


@app.route('/employees/export', methods=['GET'])
@admin_required
def export_employees():
    file_path = export_employees_to_excel()
    flash('Xuất dữ liệu thành công!', 'success')
    return redirect(url_for('download_file', filename=file_path))


@app.route('/employees/import', methods=['GET', 'POST'])
@admin_required
def import_employees():
    """Import employees from Excel/CSV"""
    form = EmployeeImportForm()
    import_results = None
    
    if form.validate_on_submit():
        # Process the import
        import_results = process_employee_import(
            file=form.import_file.data,
            skip_header=form.skip_header.data,
            update_existing=form.update_existing.data,
            default_department_id=form.department_id.data if form.department_id.data > 0 else None
        )
        
        if import_results['added'] > 0 or import_results['updated'] > 0:
            flash(f"Nhập dữ liệu thành công! Đã thêm {import_results['added']} và cập nhật {import_results['updated']} nhân viên.", 'success')
        else:
            flash("Không có nhân viên nào được thêm hoặc cập nhật.", 'warning')
    
    return render_template('employees/import.html', form=form, import_results=import_results)


@app.route('/employees/download-sample-import')
@admin_required
def download_sample_import():
    """Download sample import file"""
    file_path = create_sample_import_file()
    return redirect(url_for('download_file', filename=file_path))


# Career path routes
@app.route('/employees/<int:employee_id>/career_path/add', methods=['GET', 'POST'])
@admin_required
def add_career_path(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    form = CareerPathForm()
    
    if form.validate_on_submit() and form.validate_dates():
        career_path = CareerPath(
            employee_id=employee_id,
            position=form.position.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            description=form.description.data
        )
        db.session.add(career_path)
        db.session.commit()
        flash('Lộ trình công danh đã được thêm thành công!', 'success')
        return redirect(url_for('view_employee', id=employee_id))
    
    return render_template('employees/career_path_form.html', form=form, employee=employee, action='add')


@app.route('/career_path/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_career_path(id):
    career_path = CareerPath.query.get_or_404(id)
    form = CareerPathForm(obj=career_path)
    
    if form.validate_on_submit() and form.validate_dates():
        career_path.position = form.position.data
        career_path.start_date = form.start_date.data
        career_path.end_date = form.end_date.data
        career_path.description = form.description.data
        db.session.commit()
        flash('Lộ trình công danh đã được cập nhật thành công!', 'success')
        return redirect(url_for('view_employee', id=career_path.employee_id))
    
    return render_template('employees/career_path_form.html', form=form, career_path=career_path, employee=career_path.employee, action='edit')


@app.route('/career_path/<int:id>/delete', methods=['POST'])
@admin_required
def delete_career_path(id):
    career_path = CareerPath.query.get_or_404(id)
    employee_id = career_path.employee_id
    
    db.session.delete(career_path)
    db.session.commit()
    flash('Lộ trình công danh đã được xóa thành công!', 'success')
    return redirect(url_for('view_employee', id=employee_id))


# Attendance routes
@app.route('/attendance')
@login_required
def attendance():
    if current_user.is_admin():
        # Admin view - show all attendance records for today
        today = date.today()
        attendances = db.session.query(
            Attendance,
            Employee
        ).join(
            Employee, Attendance.employee_id == Employee.id
        ).filter(
            Attendance.date == today
        ).all()
        
        # Get employees who haven't checked in today
        checked_in_employees = db.session.query(Attendance.employee_id).filter(Attendance.date == today).all()
        checked_in_ids = [emp[0] for emp in checked_in_employees]
        
        not_checked_in = Employee.query.filter(
            Employee.status == EmployeeStatus.ACTIVE,
            ~Employee.id.in_(checked_in_ids) if checked_in_ids else True
        ).all()
        
        return render_template(
            'attendance/index.html', 
            attendances=attendances, 
            not_checked_in=not_checked_in,
            today=today
        )
    else:
        # Employee view - show their attendance
        employee = Employee.query.filter_by(user_id=current_user.id).first()
        
        if not employee:
            flash('Không tìm thấy thông tin nhân viên liên kết với tài khoản của bạn.', 'danger')
            return redirect(url_for('index'))
        
        # Get current month's attendance
        current_month = date.today().replace(day=1)
        next_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)
        
        attendances = Attendance.query.filter(
            Attendance.employee_id == employee.id,
            Attendance.date >= current_month,
            Attendance.date < next_month
        ).order_by(Attendance.date.desc()).all()
        
        # Check if the employee has checked in today
        today_attendance = Attendance.query.filter_by(
            employee_id=employee.id,
            date=date.today()
        ).first()
        
        return render_template(
            'attendance/employee_view.html', 
            employee=employee, 
            attendances=attendances,
            today_attendance=today_attendance,
            today=date.today()
        )


@app.route('/attendance/check_in', methods=['POST'])
@login_required
def check_in():
    if current_user.is_admin():
        # Admin check-in for an employee
        employee_id = request.form.get('employee_id', type=int)
        employee = Employee.query.get_or_404(employee_id)
    else:
        # Employee checks in themselves
        employee = Employee.query.filter_by(user_id=current_user.id).first()
        
        if not employee:
            flash('Không tìm thấy thông tin nhân viên liên kết với tài khoản của bạn.', 'danger')
            return redirect(url_for('index'))
    
    # Check if employee has already checked in today
    today_attendance = Attendance.query.filter_by(
        employee_id=employee.id,
        date=date.today()
    ).first()
    
    if today_attendance:
        if today_attendance.check_in:
            flash('Nhân viên đã check-in hôm nay rồi.', 'warning')
        else:
            today_attendance.check_in = datetime.now()
            db.session.commit()
            flash('Check-in thành công!', 'success')
    else:
        # Create new attendance record
        attendance = Attendance(
            employee_id=employee.id,
            date=date.today(),
            check_in=datetime.now()
        )
        db.session.add(attendance)
        db.session.commit()
        flash('Check-in thành công!', 'success')
    
    return redirect(url_for('attendance'))


@app.route('/attendance/check_out', methods=['POST'])
@login_required
def check_out():
    if current_user.is_admin():
        # Admin check-out for an employee
        attendance_id = request.form.get('attendance_id', type=int)
        attendance = Attendance.query.get_or_404(attendance_id)
    else:
        # Employee checks out themselves
        employee = Employee.query.filter_by(user_id=current_user.id).first()
        
        if not employee:
            flash('Không tìm thấy thông tin nhân viên liên kết với tài khoản của bạn.', 'danger')
            return redirect(url_for('index'))
        
        attendance = Attendance.query.filter_by(
            employee_id=employee.id,
            date=date.today()
        ).first()
    
    if not attendance:
        flash('Không tìm thấy bản ghi chấm công cho hôm nay. Vui lòng check-in trước.', 'danger')
    elif attendance.check_out:
        flash('Nhân viên đã check-out hôm nay rồi.', 'warning')
    else:
        attendance.check_out = datetime.now()
        
        # Calculate total hours
        if attendance.check_in:
            total_hours = (attendance.check_out - attendance.check_in).total_seconds() / 3600
            attendance.total_hours = round(total_hours, 2)
        
        db.session.commit()
        flash('Check-out thành công!', 'success')
    
    return redirect(url_for('attendance'))


@app.route('/attendance/report', methods=['GET', 'POST'])
@admin_required
def attendance_report():
    form = AttendanceReportForm()
    
    if form.validate_on_submit() and form.validate_dates():
        # Query attendance data for the report
        query = db.session.query(
            Attendance,
            Employee,
            Department
        ).join(
            Employee, Attendance.employee_id == Employee.id
        ).join(
            Department, Employee.department_id == Department.id
        ).filter(
            Attendance.date.between(form.start_date.data, form.end_date.data)
        )
        
        if form.employee_id.data and form.employee_id.data > 0:
            query = query.filter(Attendance.employee_id == form.employee_id.data)
        
        attendances = query.order_by(Attendance.date.desc(), Employee.full_name).all()
        
        return render_template(
            'attendance/report.html',
            form=form,
            attendances=attendances,
            has_results=True
        )
    
    return render_template('attendance/report.html', form=form, has_results=False)


@app.route('/attendance/export', methods=['POST'])
@admin_required
def export_attendance():
    form = AttendanceReportForm()
    
    if form.validate_on_submit() and form.validate_dates():
        file_path = export_attendance_to_excel(
            form.start_date.data, 
            form.end_date.data, 
            form.employee_id.data
        )
        return redirect(url_for('download_file', filename=file_path))
    
    flash('Có lỗi xảy ra khi tạo báo cáo. Vui lòng thử lại.', 'danger')
    return redirect(url_for('attendance_report'))


# Leave request routes
@app.route('/leave_requests')
@login_required
def leave_requests():
    if current_user.is_admin():
        # Admin view - show all leave requests
        pending_requests = LeaveRequest.query.filter_by(status=LeaveStatus.PENDING).order_by(LeaveRequest.created_at.desc()).all()
        other_requests = LeaveRequest.query.filter(LeaveRequest.status != LeaveStatus.PENDING).order_by(LeaveRequest.created_at.desc()).limit(20).all()
        
        return render_template(
            'leave/admin.html',
            pending_requests=pending_requests,
            other_requests=other_requests
        )
    else:
        # Employee view - show their leave requests
        employee = Employee.query.filter_by(user_id=current_user.id).first()
        
        if not employee:
            flash('Không tìm thấy thông tin nhân viên liên kết với tài khoản của bạn.', 'danger')
            return redirect(url_for('index'))
        
        leave_requests = LeaveRequest.query.filter_by(employee_id=employee.id).order_by(LeaveRequest.created_at.desc()).all()
        
        return render_template(
            'leave/index.html',
            employee=employee,
            leave_requests=leave_requests
        )


@app.route('/leave_requests/create', methods=['GET', 'POST'])
@login_required
def create_leave_request():
    if current_user.is_admin():
        # Admin can create leave requests for any employee
        employee_id = request.args.get('employee_id', type=int)
        if employee_id:
            employee = Employee.query.get_or_404(employee_id)
        else:
            employees = Employee.query.filter_by(status=EmployeeStatus.ACTIVE).all()
            return render_template('leave/select_employee.html', employees=employees)
    else:
        # Regular employee can only create for themselves
        employee = Employee.query.filter_by(user_id=current_user.id).first()
        
        if not employee:
            flash('Không tìm thấy thông tin nhân viên liên kết với tài khoản của bạn.', 'danger')
            return redirect(url_for('index'))
    
    form = LeaveRequestForm()
    
    if form.validate_on_submit() and form.validate_dates():
        leave_request = LeaveRequest(
            employee_id=employee.id,
            leave_type=LeaveType[form.leave_type.data],
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            reason=form.reason.data,
            status=LeaveStatus.PENDING
        )
        db.session.add(leave_request)
        db.session.commit()
        flash('Yêu cầu nghỉ phép đã được gửi thành công!', 'success')
        return redirect(url_for('leave_requests'))
    
    return render_template('leave/create.html', form=form, employee=employee)


@app.route('/leave_requests/<int:id>/approve', methods=['POST'])
@admin_required
def approve_leave_request(id):
    leave_request = LeaveRequest.query.get_or_404(id)
    
    if leave_request.status != LeaveStatus.PENDING:
        flash('Yêu cầu nghỉ phép này đã được xử lý.', 'warning')
    else:
        leave_request.status = LeaveStatus.APPROVED
        leave_request.reviewed_by = current_user.id
        leave_request.reviewed_at = datetime.now()
        db.session.commit()
        flash('Yêu cầu nghỉ phép đã được phê duyệt!', 'success')
    
    return redirect(url_for('leave_requests'))


@app.route('/leave_requests/<int:id>/reject', methods=['POST'])
@admin_required
def reject_leave_request(id):
    leave_request = LeaveRequest.query.get_or_404(id)
    
    if leave_request.status != LeaveStatus.PENDING:
        flash('Yêu cầu nghỉ phép này đã được xử lý.', 'warning')
    else:
        leave_request.status = LeaveStatus.REJECTED
        leave_request.reviewed_by = current_user.id
        leave_request.reviewed_at = datetime.now()
        db.session.commit()
        flash('Yêu cầu nghỉ phép đã bị từ chối!', 'warning')
    
    return redirect(url_for('leave_requests'))


@app.route('/leave_requests/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_leave_request(id):
    leave_request = LeaveRequest.query.get_or_404(id)
    
    # Check if the current user owns this leave request or is an admin
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    if not current_user.is_admin() and (not employee or employee.id != leave_request.employee_id):
        flash('Bạn không có quyền hủy yêu cầu nghỉ phép này.', 'danger')
        return redirect(url_for('leave_requests'))
    
    if leave_request.status != LeaveStatus.PENDING:
        flash('Chỉ có thể hủy yêu cầu đang chờ xét duyệt.', 'warning')
    else:
        db.session.delete(leave_request)
        db.session.commit()
        flash('Yêu cầu nghỉ phép đã được hủy!', 'success')
    
    return redirect(url_for('leave_requests'))


# File download route
@app.route('/download/<path:filename>')
@login_required
def download_file(filename):
    # Check that the filename is an export file (for security)
    if not filename.startswith('exports/'):
        abort(404)
    
    directory = os.path.join('static')
    return send_from_directory(directory, filename, as_attachment=True)


# API routes for Ajax requests
@app.route('/api/employee/<int:id>')
@login_required
def get_employee(id):
    employee = Employee.query.get_or_404(id)
    
    # Check permissions
    if not current_user.is_admin() and (not current_user.employee or current_user.employee.id != id):
        return jsonify({"error": "Unauthorized"}), 403
    
    department = Department.query.get(employee.department_id)
    
    return jsonify({
        "id": employee.id,
        "employee_code": employee.employee_code,
        "full_name": employee.full_name,
        "gender": employee.gender.value,
        "date_of_birth": employee.date_of_birth.strftime('%Y-%m-%d'),
        "department_name": department.name if department else "",
        "position": employee.position,
        "join_date": employee.join_date.strftime('%Y-%m-%d'),
        "email": employee.email,
        "phone_number": employee.phone_number or "",
        "status": employee.status.value
    })


@app.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    if not current_user.is_admin():
        return jsonify({"error": "Unauthorized"}), 403
    
    # Department statistics
    departments = Department.query.all()
    dept_stats = []
    
    for dept in departments:
        employee_count = Employee.query.filter_by(department_id=dept.id, status=EmployeeStatus.ACTIVE).count()
        dept_stats.append({
            'name': dept.name,
            'count': employee_count
        })
    
    # Gender statistics
    male_count = Employee.query.filter_by(gender=Gender.MALE, status=EmployeeStatus.ACTIVE).count()
    female_count = Employee.query.filter_by(gender=Gender.FEMALE, status=EmployeeStatus.ACTIVE).count()
    other_count = Employee.query.filter_by(gender=Gender.OTHER, status=EmployeeStatus.ACTIVE).count()
    
    # Overall statistics
    total_employees = Employee.query.filter_by(status=EmployeeStatus.ACTIVE).count()
    total_departments = Department.query.count()
    
    return jsonify({
        "departments": dept_stats,
        "gender": {
            "male": male_count,
            "female": female_count,
            "other": other_count
        },
        "total_employees": total_employees,
        "total_departments": total_departments
    })


# Error handlers
# Salary Grade Management
@app.route('/salary-grades')
@admin_required
def salary_grades():
    grades = SalaryGrade.query.order_by(SalaryGrade.code).all()
    return render_template('salary_grades/index.html', grades=grades)


@app.route('/salary-grades/create', methods=['GET', 'POST'])
@admin_required
def create_salary_grade():
    form = SalaryGradeForm()
    if form.validate_on_submit():
        try:
            salary_grade = SalaryGrade(
                code=form.code.data,
                name=form.name.data,
                base_coefficient=form.base_coefficient.data,
                base_salary=int(form.base_salary.data),
                description=form.description.data
            )
            db.session.add(salary_grade)
            db.session.commit()
            flash('Bậc lương mới đã được tạo thành công!', 'success')
            return redirect(url_for('salary_grades'))
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi tạo bậc lương: {str(e)}', 'danger')
    
    return render_template('salary_grades/create.html', form=form)


@app.route('/salary-grades/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_salary_grade(id):
    salary_grade = SalaryGrade.query.get_or_404(id)
    form = SalaryGradeEditForm(obj=salary_grade)
    
    if form.validate_on_submit():
        try:
            salary_grade.code = form.code.data
            salary_grade.name = form.name.data
            salary_grade.base_coefficient = form.base_coefficient.data
            salary_grade.base_salary = int(form.base_salary.data)
            salary_grade.description = form.description.data
            db.session.commit()
            flash('Bậc lương đã được cập nhật thành công!', 'success')
            return redirect(url_for('salary_grades'))
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi cập nhật bậc lương: {str(e)}', 'danger')
    
    return render_template('salary_grades/edit.html', form=form, salary_grade=salary_grade)


@app.route('/salary-grades/<int:id>/delete', methods=['POST'])
@admin_required
def delete_salary_grade(id):
    salary_grade = SalaryGrade.query.get_or_404(id)
    
    # Check if grade is being used
    if EmployeeSalary.query.filter_by(salary_grade_id=id).count() > 0:
        flash('Không thể xóa bậc lương vì đang được sử dụng cho nhân viên.', 'danger')
        return redirect(url_for('salary_grades'))
    
    try:
        db.session.delete(salary_grade)
        db.session.commit()
        flash('Bậc lương đã được xóa thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi xóa bậc lương: {str(e)}', 'danger')
        
    return redirect(url_for('salary_grades'))


# Employee Salary Management
@app.route('/employee-salaries')
@admin_required
def employee_salaries():
    salaries = db.session.query(
        EmployeeSalary, 
        Employee, 
        SalaryGrade
    ).join(
        Employee, 
        EmployeeSalary.employee_id == Employee.id
    ).join(
        SalaryGrade, 
        EmployeeSalary.salary_grade_id == SalaryGrade.id
    ).order_by(
        desc(EmployeeSalary.effective_date)
    ).all()
    
    return render_template('employee_salaries/index.html', salaries=salaries)


@app.route('/employee-salaries/create', methods=['GET', 'POST'])
@admin_required
def create_employee_salary():
    form = EmployeeSalaryForm()
    if form.validate_on_submit() and form.validate_dates():
        try:
            employee_salary = EmployeeSalary(
                employee_id=form.employee_id.data,
                salary_grade_id=form.salary_grade_id.data,
                effective_date=form.effective_date.data,
                end_date=form.end_date.data,
                additional_coefficient=form.additional_coefficient.data or 0,
                reason=form.reason.data,
                decision_number=form.decision_number.data
            )
            
            # Đánh dấu các hồ sơ lương hiện có của nhân viên là kết thúc
            if not form.end_date.data:
                # Nếu không có ngày kết thúc, chúng ta cần cập nhật các hồ sơ hiện có
                existing_salaries = EmployeeSalary.query.filter(
                    EmployeeSalary.employee_id == form.employee_id.data,
                    (EmployeeSalary.end_date.is_(None) | 
                     (EmployeeSalary.end_date >= form.effective_date.data))
                ).all()
                
                for existing in existing_salaries:
                    # Cập nhật ngày kết thúc của hồ sơ hiện có
                    existing.end_date = form.effective_date.data - timedelta(days=1)
            
            db.session.add(employee_salary)
            db.session.commit()
            flash('Thông tin lương mới của nhân viên đã được tạo thành công!', 'success')
            return redirect(url_for('employee_salaries'))
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi tạo thông tin lương: {str(e)}', 'danger')
    
    return render_template('employee_salaries/create.html', form=form)


@app.route('/employee-salaries/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_employee_salary(id):
    employee_salary = EmployeeSalary.query.get_or_404(id)
    form = EmployeeSalaryEditForm(obj=employee_salary)
    
    if form.validate_on_submit() and form.validate_dates():
        try:
            employee_salary.employee_id = form.employee_id.data
            employee_salary.salary_grade_id = form.salary_grade_id.data
            employee_salary.effective_date = form.effective_date.data
            employee_salary.end_date = form.end_date.data
            employee_salary.additional_coefficient = form.additional_coefficient.data or 0
            employee_salary.reason = form.reason.data
            employee_salary.decision_number = form.decision_number.data
            
            db.session.commit()
            flash('Thông tin lương của nhân viên đã được cập nhật thành công!', 'success')
            return redirect(url_for('employee_salaries'))
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi cập nhật thông tin lương: {str(e)}', 'danger')
    
    return render_template('employee_salaries/edit.html', form=form, employee_salary=employee_salary)


@app.route('/employee-salaries/<int:id>/delete', methods=['POST'])
@admin_required
def delete_employee_salary(id):
    employee_salary = EmployeeSalary.query.get_or_404(id)
    
    try:
        db.session.delete(employee_salary)
        db.session.commit()
        flash('Thông tin lương đã được xóa thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi xóa thông tin lương: {str(e)}', 'danger')
        
    return redirect(url_for('employee_salaries'))


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500


# Quản lý tiêu chí đánh giá hiệu suất
@app.route('/performance/criteria')
@login_required
def performance_criteria():
    if not current_user.is_admin:
        flash('Bạn không có quyền truy cập trang này.', 'danger')
        return redirect(url_for('dashboard'))
    
    criterias = PerformanceEvaluationCriteria.query.all()
    return render_template('performance/criteria_index.html', criterias=criterias)


@app.route('/performance/criteria/create', methods=['GET', 'POST'])
@login_required
def create_performance_criteria():
    if not current_user.is_admin:
        flash('Bạn không có quyền truy cập trang này.', 'danger')
        return redirect(url_for('dashboard'))
    
    form = PerformanceCriteriaForm()
    
    if form.validate_on_submit():
        criteria = PerformanceEvaluationCriteria(
            name=form.name.data,
            description=form.description.data,
            max_score=int(form.max_score.data),
            weight=form.weight.data,
            is_active=form.is_active.data,
            created_by=current_user.id
        )
        
        if form.department_id.data != 0:  # 0 means "All departments"
            criteria.department_id = form.department_id.data
        
        db.session.add(criteria)
        db.session.commit()
        
        flash('Tiêu chí đánh giá đã được tạo thành công.', 'success')
        return redirect(url_for('performance_criteria'))
    
    return render_template('performance/criteria_create.html', form=form)


@app.route('/performance/criteria/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_performance_criteria(id):
    if not current_user.is_admin:
        flash('Bạn không có quyền truy cập trang này.', 'danger')
        return redirect(url_for('dashboard'))
    
    criteria = PerformanceEvaluationCriteria.query.get_or_404(id)
    form = PerformanceCriteriaForm(obj=criteria)
    
    if form.validate_on_submit():
        criteria.name = form.name.data
        criteria.description = form.description.data
        criteria.max_score = int(form.max_score.data)
        criteria.weight = form.weight.data
        criteria.is_active = form.is_active.data
        
        if form.department_id.data != 0:  # 0 means "All departments"
            criteria.department_id = form.department_id.data
        else:
            criteria.department_id = None
            
        db.session.commit()
        
        flash('Tiêu chí đánh giá đã được cập nhật thành công.', 'success')
        return redirect(url_for('performance_criteria'))
    
    # Nếu department_id là None, set form field thành 0 (Tất cả phòng ban)
    if criteria.department_id is None:
        form.department_id.data = 0
        
    return render_template('performance/criteria_edit.html', form=form, criteria=criteria)


@app.route('/performance/criteria/<int:id>/delete')
@login_required
def delete_performance_criteria(id):
    if not current_user.is_admin:
        flash('Bạn không có quyền thực hiện thao tác này.', 'danger')
        return redirect(url_for('dashboard'))
    
    criteria = PerformanceEvaluationCriteria.query.get_or_404(id)
    
    # Kiểm tra xem tiêu chí này đã được sử dụng trong đánh giá nào chưa
    details = PerformanceEvaluationDetail.query.filter_by(criteria_id=id).first()
    if details:
        flash('Không thể xóa tiêu chí này vì nó đã được sử dụng trong các đánh giá.', 'danger')
        return redirect(url_for('performance_criteria'))
    
    db.session.delete(criteria)
    db.session.commit()
    
    flash('Tiêu chí đánh giá đã được xóa thành công.', 'success')
    return redirect(url_for('performance_criteria'))


# Quản lý đánh giá hiệu suất
@app.route('/performance/evaluations')
@login_required
def performance_evaluations():
    filter_form = PerformanceFilterForm(request.args)
    
    # Tạo query cơ sở
    query = PerformanceEvaluation.query
    
    # Áp dụng các bộ lọc
    if request.args.get('employee_id') and int(request.args.get('employee_id')) != 0:
        query = query.filter(PerformanceEvaluation.employee_id == request.args.get('employee_id'))
    
    if request.args.get('evaluation_period'):
        query = query.filter(PerformanceEvaluation.evaluation_period == request.args.get('evaluation_period'))
        
    if request.args.get('status'):
        query = query.filter(PerformanceEvaluation.status == request.args.get('status'))
        
    if request.args.get('start_date'):
        query = query.filter(PerformanceEvaluation.start_date >= request.args.get('start_date'))
        
    if request.args.get('end_date'):
        query = query.filter(PerformanceEvaluation.end_date <= request.args.get('end_date'))
    
    # Nếu không phải admin, chỉ xem đánh giá của mình
    if not current_user.is_admin:
        # Kiểm tra xem user có thông tin employee không
        if hasattr(current_user, 'employee'):
            query = query.filter(PerformanceEvaluation.employee_id == current_user.employee.id)
        else:
            # Nếu không có thông tin employee, không có đánh giá nào được hiển thị
            evaluations = []
            return render_template('performance/evaluation_index.html', evaluations=evaluations, filter_form=filter_form)
    
    evaluations = query.order_by(PerformanceEvaluation.id.desc()).all()
    return render_template('performance/evaluation_index.html', evaluations=evaluations, filter_form=filter_form)


@app.route('/performance/evaluations/create', methods=['GET', 'POST'])
@login_required
def create_performance_evaluation():
    if not current_user.is_admin and not hasattr(current_user, 'employee'):
        flash('Bạn không có quyền thực hiện thao tác này.', 'danger')
        return redirect(url_for('dashboard'))
    
    form = PerformanceEvaluationForm()
    
    if form.validate_on_submit():
        # Validate dates
        if not form.validate_dates():
            return render_template('performance/evaluation_create.html', form=form)
        
        evaluation = PerformanceEvaluation(
            employee_id=form.employee_id.data,
            evaluator_id=current_user.id,
            evaluation_period=form.evaluation_period.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            comments=form.comments.data,
            strengths=form.strengths.data,
            areas_for_improvement=form.areas_for_improvement.data,
            goals_for_next_period=form.goals_for_next_period.data,
            status=PerformanceRatingStatus.DRAFT
        )
        
        db.session.add(evaluation)
        db.session.commit()
        
        # Nếu người dùng nhấp vào nút "Tiếp tục điền điểm"
        if 'submit' in request.form:
            flash('Đánh giá hiệu suất đã được tạo. Vui lòng tiếp tục điền điểm đánh giá.', 'success')
            return redirect(url_for('score_performance_evaluation', id=evaluation.id))
        else:
            flash('Đánh giá hiệu suất đã được lưu dưới dạng bản nháp.', 'success')
            return redirect(url_for('performance_evaluations'))
        
    return render_template('performance/evaluation_create.html', form=form)


@app.route('/performance/evaluations/<int:id>', methods=['GET'])
@login_required
def view_performance_evaluation(id):
    evaluation = PerformanceEvaluation.query.get_or_404(id)
    
    # Kiểm tra quyền truy cập
    if not current_user.is_admin and (not hasattr(current_user, 'employee') or current_user.employee.id != evaluation.employee_id):
        flash('Bạn không có quyền xem đánh giá này.', 'danger')
        return redirect(url_for('dashboard'))
    
    criteria_scores = PerformanceEvaluationDetail.query.filter_by(evaluation_id=id).all()
    feedback_form = EmployeePerformanceFeedbackForm()
    approval_form = PerformanceApprovalForm()
    
    return render_template(
        'performance/evaluation_view.html', 
        evaluation=evaluation, 
        criteria_scores=criteria_scores,
        feedback_form=feedback_form,
        approval_form=approval_form
    )


@app.route('/performance/evaluations/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_performance_evaluation(id):
    evaluation = PerformanceEvaluation.query.get_or_404(id)
    
    # Kiểm tra quyền truy cập
    if not current_user.is_admin and (not hasattr(current_user, 'employee') or current_user.employee.id != evaluation.employee_id):
        flash('Bạn không có quyền chỉnh sửa đánh giá này.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Nếu không phải admin và đánh giá không ở trạng thái nháp
    if not current_user.is_admin and evaluation.status != PerformanceRatingStatus.DRAFT:
        flash('Đánh giá này không thể chỉnh sửa vì đã được gửi đi.', 'danger')
        return redirect(url_for('view_performance_evaluation', id=evaluation.id))
    
    form = PerformanceEvaluationForm(obj=evaluation)
    
    if form.validate_on_submit():
        # Validate dates
        if not form.validate_dates():
            return render_template('performance/evaluation_create.html', form=form)
        
        evaluation.employee_id = form.employee_id.data
        evaluation.evaluation_period = form.evaluation_period.data
        evaluation.start_date = form.start_date.data
        evaluation.end_date = form.end_date.data
        evaluation.comments = form.comments.data
        evaluation.strengths = form.strengths.data
        evaluation.areas_for_improvement = form.areas_for_improvement.data
        evaluation.goals_for_next_period = form.goals_for_next_period.data
        
        db.session.commit()
        
        # Nếu người dùng nhấp vào nút "Tiếp tục điền điểm"
        if 'submit' in request.form:
            flash('Đánh giá hiệu suất đã được cập nhật. Vui lòng tiếp tục điền điểm đánh giá.', 'success')
            return redirect(url_for('score_performance_evaluation', id=evaluation.id))
        else:
            flash('Đánh giá hiệu suất đã được cập nhật thành công.', 'success')
            return redirect(url_for('view_performance_evaluation', id=evaluation.id))
    
    return render_template('performance/evaluation_create.html', form=form, evaluation=evaluation)


@app.route('/performance/evaluations/<int:id>/score', methods=['GET', 'POST'])
@login_required
def score_performance_evaluation(id):
    evaluation = PerformanceEvaluation.query.get_or_404(id)
    
    # Kiểm tra quyền truy cập
    if not current_user.is_admin and (not hasattr(current_user, 'employee') or current_user.id != evaluation.evaluator_id):
        flash('Bạn không có quyền điền điểm cho đánh giá này.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Kiểm tra trạng thái
    if not current_user.is_admin and evaluation.status != PerformanceRatingStatus.DRAFT:
        flash('Đánh giá này không thể điều chỉnh điểm vì đã được gửi đi.', 'danger')
        return redirect(url_for('view_performance_evaluation', id=evaluation.id))
    
    # Lấy danh sách các tiêu chí đánh giá
    criteria_list = PerformanceEvaluationCriteria.query.filter_by(is_active=True).all()
    
    # Tạo form với các trường động cho từng tiêu chí
    class CriteriaScoreForm(FlaskForm):
        pass
    
    for i, criteria in enumerate(criteria_list):
        setattr(CriteriaScoreForm, f'criteria_{i}_score', FloatField(f'Điểm ({criteria.name})', validators=[Optional()]))
        setattr(CriteriaScoreForm, f'criteria_{i}_comments', TextAreaField(f'Nhận xét ({criteria.name})', validators=[Optional()]))
    
    form = FlaskForm()
    form.criteria_forms = []
    
    # Lấy các điểm đánh giá hiện có
    existing_scores = {}
    for detail in PerformanceEvaluationDetail.query.filter_by(evaluation_id=id).all():
        existing_scores[detail.criteria_id] = {
            'score': detail.score,
            'comments': detail.comments
        }
    
    # Tạo form cho từng tiêu chí
    for criteria in criteria_list:
        criteria_form = PerformanceCriteriaScoreForm(criteria=criteria)
        
        # Nếu đã có điểm, hiển thị thông tin
        if criteria.id in existing_scores:
            criteria_form.score.data = existing_scores[criteria.id]['score']
            criteria_form.comments.data = existing_scores[criteria.id]['comments']
            
        form.criteria_forms.append(criteria_form)
    
    if request.method == 'POST':
        # Xử lý dữ liệu gửi lên
        for i, criteria in enumerate(criteria_list):
            score_value = request.form.get(f'criteria_forms-{i}-score', '')
            comments_value = request.form.get(f'criteria_forms-{i}-comments', '')
            
            # Tìm hoặc tạo mới chi tiết đánh giá
            detail = PerformanceEvaluationDetail.query.filter_by(
                evaluation_id=id, 
                criteria_id=criteria.id
            ).first()
            
            if not detail:
                detail = PerformanceEvaluationDetail(
                    evaluation_id=id,
                    criteria_id=criteria.id
                )
                db.session.add(detail)
            
            # Cập nhật giá trị
            if score_value.strip():
                try:
                    score_float = float(score_value)
                    if 0 <= score_float <= criteria.max_score:
                        detail.score = score_float
                    else:
                        flash(f'Điểm cho tiêu chí "{criteria.name}" phải từ 0 đến {criteria.max_score}.', 'danger')
                        return redirect(url_for('score_performance_evaluation', id=id))
                except ValueError:
                    flash(f'Điểm cho tiêu chí "{criteria.name}" phải là số.', 'danger')
                    return redirect(url_for('score_performance_evaluation', id=id))
            else:
                detail.score = None
                
            detail.comments = comments_value
        
        # Tính toán điểm tổng hợp
        evaluation.overall_score = evaluation.calculate_overall_score()
        
        # Cập nhật trạng thái nếu người dùng nhấp vào nút "Hoàn thành đánh giá"
        if 'submit' in request.form:
            evaluation.status = PerformanceRatingStatus.SUBMITTED
            db.session.commit()
            flash('Đánh giá hiệu suất đã được hoàn thành và gửi đi.', 'success')
        else:
            db.session.commit()
            flash('Điểm đánh giá đã được lưu thành công.', 'success')
            
        return redirect(url_for('view_performance_evaluation', id=id))
    
    return render_template(
        'performance/evaluation_score.html',
        form=form,
        evaluation=evaluation,
        criteria_list=criteria_list,
        enumerate=enumerate
    )


@app.route('/performance/evaluations/<int:id>/feedback', methods=['POST'])
@login_required
def employee_feedback_evaluation(id):
    evaluation = PerformanceEvaluation.query.get_or_404(id)
    
    # Chỉ nhân viên được đánh giá mới có thể gửi phản hồi
    if not hasattr(current_user, 'employee') or current_user.employee.id != evaluation.employee_id:
        flash('Bạn không có quyền gửi phản hồi cho đánh giá này.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Đánh giá phải không phải ở trạng thái nháp
    if evaluation.status == PerformanceRatingStatus.DRAFT:
        flash('Bạn không thể gửi phản hồi cho đánh giá ở trạng thái nháp.', 'danger')
        return redirect(url_for('view_performance_evaluation', id=id))
    
    form = EmployeePerformanceFeedbackForm()
    
    if form.validate_on_submit():
        evaluation.employee_comments = form.employee_comments.data
        db.session.commit()
        
        flash('Phản hồi của bạn đã được gửi thành công.', 'success')
        
    return redirect(url_for('view_performance_evaluation', id=id))


@app.route('/performance/evaluations/<int:id>/approve', methods=['POST'])
@login_required
def approve_performance_evaluation(id):
    if not current_user.is_admin:
        flash('Bạn không có quyền thực hiện thao tác này.', 'danger')
        return redirect(url_for('dashboard'))
    
    evaluation = PerformanceEvaluation.query.get_or_404(id)
    form = PerformanceApprovalForm()
    
    if form.validate_on_submit():
        evaluation.status = form.status.data
        
        if form.comments.data:
            if evaluation.comments:
                evaluation.comments += f"\n\nNhận xét của quản lý ({current_user.username}) - {datetime.now().strftime('%d/%m/%Y %H:%M')}:\n{form.comments.data}"
            else:
                evaluation.comments = f"Nhận xét của quản lý ({current_user.username}) - {datetime.now().strftime('%d/%m/%Y %H:%M')}:\n{form.comments.data}"
        
        evaluation.approved_by = current_user.id
        evaluation.approved_at = datetime.now()
        
        db.session.commit()
        
        flash('Trạng thái đánh giá đã được cập nhật thành công.', 'success')
        
    return redirect(url_for('view_performance_evaluation', id=id))


@app.route('/performance/evaluations/<int:id>/delete')
@login_required
def delete_performance_evaluation(id):
    if not current_user.is_admin:
        flash('Bạn không có quyền thực hiện thao tác này.', 'danger')
        return redirect(url_for('dashboard'))
    
    evaluation = PerformanceEvaluation.query.get_or_404(id)
    
    # Xóa các chi tiết đánh giá liên quan
    details = PerformanceEvaluationDetail.query.filter_by(evaluation_id=id).all()
    for detail in details:
        db.session.delete(detail)
    
    db.session.delete(evaluation)
    db.session.commit()
    
    flash('Đánh giá hiệu suất đã được xóa thành công.', 'success')
    return redirect(url_for('performance_evaluations'))
