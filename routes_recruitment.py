from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from models import (
    JobPosition, JobOpening, JobOpeningStatus, 
    Candidate, CandidateStatus, 
    Interview, InterviewStatus, InterviewType,
    Department
)
from forms_recruitment import (
    JobPositionForm, JobPositionEditForm,
    JobOpeningForm, JobOpeningEditForm,
    CandidateForm, CandidateEditForm,
    InterviewForm, InterviewEditForm,
    RecruitmentFilterForm
)
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os

recruitment_bp = Blueprint('recruitment', __name__, url_prefix='/recruitment')


@recruitment_bp.route('/')
@login_required
def index():
    # Số liệu tổng quan
    active_openings = JobOpening.query.filter_by(status=JobOpeningStatus.OPEN.name).count()
    total_candidates = Candidate.query.count()
    interviews_this_week = Interview.query.filter(
        Interview.scheduled_date >= datetime.now(),
        Interview.scheduled_date <= datetime.now() + timedelta(days=7)
    ).count()
    
    # Các vị trí tuyển dụng đang mở
    openings = JobOpening.query.filter_by(status=JobOpeningStatus.OPEN.name).order_by(JobOpening.start_date.desc()).limit(5).all()
    
    # Các ứng viên mới nhất
    recent_candidates = Candidate.query.order_by(Candidate.application_date.desc()).limit(5).all()
    
    # Các cuộc phỏng vấn sắp tới
    upcoming_interviews = Interview.query.filter(
        Interview.scheduled_date >= datetime.now(),
        Interview.status.in_([InterviewStatus.SCHEDULED.name, InterviewStatus.RESCHEDULED.name])
    ).order_by(Interview.scheduled_date).limit(5).all()
    
    return render_template('recruitment/index.html',
                          active_openings=active_openings,
                          total_candidates=total_candidates,
                          interviews_this_week=interviews_this_week,
                          openings=openings,
                          recent_candidates=recent_candidates,
                          upcoming_interviews=upcoming_interviews,
                          title='Quản lý tuyển dụng')


# Job Positions
@recruitment_bp.route('/positions')
@login_required
def position_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    keyword = request.args.get('keyword', '')
    department_id = request.args.get('department_id', type=int)
    is_active = request.args.get('is_active')
    
    query = JobPosition.query
    
    if keyword:
        query = query.filter(JobPosition.title.ilike(f'%{keyword}%'))
    
    if department_id:
        query = query.filter_by(department_id=department_id)
    
    if is_active is not None:
        is_active_bool = is_active == 'true'
        query = query.filter_by(is_active=is_active_bool)
    
    pagination = query.order_by(JobPosition.title).paginate(page=page, per_page=per_page)
    positions = pagination.items
    
    departments = Department.query.all()
    
    return render_template('recruitment/positions/index.html',
                          positions=positions,
                          pagination=pagination,
                          departments=departments,
                          keyword=keyword,
                          department_id=department_id,
                          is_active=is_active,
                          title='Vị trí công việc')


@recruitment_bp.route('/positions/create', methods=['GET', 'POST'])
@login_required
def position_create():
    form = JobPositionForm()
    
    if form.validate_on_submit():
        position = JobPosition(
            title=form.title.data,
            department_id=form.department_id.data,
            required_experience=form.required_experience.data,
            education_requirement=form.education_requirement.data,
            job_description=form.job_description.data,
            responsibilities=form.responsibilities.data,
            skills_required=form.skills_required.data,
            is_active=form.is_active.data == 'True'
        )
        
        db.session.add(position)
        db.session.commit()
        
        flash('Vị trí công việc mới đã được tạo thành công!', 'success')
        return redirect(url_for('recruitment.position_list'))
    
    return render_template('recruitment/positions/create.html',
                          form=form,
                          title='Thêm vị trí công việc')


@recruitment_bp.route('/positions/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def position_edit(id):
    position = JobPosition.query.get_or_404(id)
    form = JobPositionEditForm(obj=position)
    form.position_id.data = position.id
    
    # Gán giá trị cho trường is_active
    if request.method == 'GET':
        form.is_active.data = 'True' if position.is_active else 'False'
    
    if form.validate_on_submit():
        position.title = form.title.data
        position.department_id = form.department_id.data
        position.required_experience = form.required_experience.data
        position.education_requirement = form.education_requirement.data
        position.job_description = form.job_description.data
        position.responsibilities = form.responsibilities.data
        position.skills_required = form.skills_required.data
        position.is_active = form.is_active.data == 'True'
        
        db.session.commit()
        
        flash('Vị trí công việc đã được cập nhật!', 'success')
        return redirect(url_for('recruitment.position_view', id=position.id))
    
    return render_template('recruitment/positions/edit.html',
                          form=form,
                          position=position,
                          title='Chỉnh sửa vị trí công việc')


@recruitment_bp.route('/positions/<int:id>')
@login_required
def position_view(id):
    position = JobPosition.query.get_or_404(id)
    openings = JobOpening.query.filter_by(position_id=id).order_by(JobOpening.start_date.desc()).all()
    
    return render_template('recruitment/positions/view.html',
                          position=position,
                          openings=openings,
                          title=f'Chi tiết vị trí: {position.title}')


@recruitment_bp.route('/positions/<int:id>/delete', methods=['POST'])
@login_required
def position_delete(id):
    position = JobPosition.query.get_or_404(id)
    
    # Kiểm tra xem có tin tuyển dụng nào đang sử dụng vị trí này không
    openings = JobOpening.query.filter_by(position_id=id).count()
    if openings > 0:
        flash(f'Không thể xóa vị trí này vì có {openings} tin tuyển dụng đang sử dụng!', 'danger')
        return redirect(url_for('recruitment.position_view', id=id))
    
    db.session.delete(position)
    db.session.commit()
    
    flash('Vị trí công việc đã được xóa thành công!', 'success')
    return redirect(url_for('recruitment.position_list'))


# Job Openings
@recruitment_bp.route('/openings')
@login_required
def opening_list():
    form = RecruitmentFilterForm(request.args)
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = JobOpening.query
    
    if form.keyword.data:
        query = query.join(JobPosition).filter(
            JobPosition.title.ilike(f'%{form.keyword.data}%')
        )
    
    if form.department_id.data and form.department_id.data != 0:
        query = query.join(JobPosition).filter(JobPosition.department_id == form.department_id.data)
    
    if form.status.data:
        query = query.filter(JobOpening.status == form.status.data)
    
    if form.date_from.data:
        query = query.filter(JobOpening.start_date >= form.date_from.data)
    
    if form.date_to.data:
        query = query.filter(JobOpening.start_date <= form.date_to.data)
    
    pagination = query.order_by(JobOpening.start_date.desc()).paginate(page=page, per_page=per_page)
    openings = pagination.items
    
    return render_template('recruitment/openings/index.html',
                          openings=openings,
                          pagination=pagination,
                          form=form,
                          title='Tin tuyển dụng')


@recruitment_bp.route('/openings/create', methods=['GET', 'POST'])
@login_required
def opening_create():
    form = JobOpeningForm()
    
    if form.validate_on_submit():
        if not form.validate_dates():
            return render_template('recruitment/openings/create.html',
                                  form=form,
                                  title='Thêm tin tuyển dụng')
        
        opening = JobOpening(
            position_id=form.position_id.data,
            number_of_openings=form.number_of_openings.data,
            status=form.status.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            salary_range=form.salary_range.data,
            work_location=form.work_location.data,
            created_by_id=current_user.id
        )
        
        db.session.add(opening)
        db.session.commit()
        
        flash('Tin tuyển dụng mới đã được tạo thành công!', 'success')
        return redirect(url_for('recruitment.opening_list'))
    
    return render_template('recruitment/openings/create.html',
                          form=form,
                          title='Thêm tin tuyển dụng')


@recruitment_bp.route('/openings/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def opening_edit(id):
    opening = JobOpening.query.get_or_404(id)
    form = JobOpeningEditForm(obj=opening)
    form.opening_id.data = opening.id
    
    if form.validate_on_submit():
        if not form.validate_dates():
            return render_template('recruitment/openings/edit.html',
                                  form=form,
                                  opening=opening,
                                  title='Chỉnh sửa tin tuyển dụng')
        
        opening.position_id = form.position_id.data
        opening.number_of_openings = form.number_of_openings.data
        opening.status = form.status.data
        opening.start_date = form.start_date.data
        opening.end_date = form.end_date.data
        opening.salary_range = form.salary_range.data
        opening.work_location = form.work_location.data
        
        db.session.commit()
        
        flash('Tin tuyển dụng đã được cập nhật!', 'success')
        return redirect(url_for('recruitment.opening_view', id=opening.id))
    
    return render_template('recruitment/openings/edit.html',
                          form=form,
                          opening=opening,
                          title='Chỉnh sửa tin tuyển dụng')


@recruitment_bp.route('/openings/<int:id>')
@login_required
def opening_view(id):
    opening = JobOpening.query.get_or_404(id)
    candidates = Candidate.query.filter_by(job_opening_id=id).order_by(Candidate.application_date.desc()).all()
    
    # Thống kê ứng viên theo trạng thái
    candidate_stats = {}
    for status in CandidateStatus:
        candidate_stats[status.value] = Candidate.query.filter_by(
            job_opening_id=id, 
            status=status.name
        ).count()
    
    return render_template('recruitment/openings/view.html',
                          opening=opening,
                          candidates=candidates,
                          candidate_stats=candidate_stats,
                          title=f'Chi tiết tin tuyển dụng: {opening.position.title}')


@recruitment_bp.route('/openings/<int:id>/close', methods=['POST'])
@login_required
def opening_close(id):
    opening = JobOpening.query.get_or_404(id)
    
    if opening.status == JobOpeningStatus.CLOSED.name:
        flash('Tin tuyển dụng này đã được đóng trước đó!', 'warning')
    else:
        opening.status = JobOpeningStatus.CLOSED.name
        db.session.commit()
        flash('Tin tuyển dụng đã được đóng thành công!', 'success')
    
    return redirect(url_for('recruitment.opening_view', id=id))


@recruitment_bp.route('/recruitment/openings/<int:id>/reopen', methods=['POST'])
@login_required
def opening_reopen(id):
    opening = JobOpening.query.get_or_404(id)
    
    if opening.status == JobOpeningStatus.OPEN.name:
        flash('Tin tuyển dụng này đã mở!', 'warning')
    else:
        opening.status = JobOpeningStatus.OPEN.name
        db.session.commit()
        flash('Tin tuyển dụng đã được mở lại thành công!', 'success')
    
    return redirect(url_for('recruitment.opening_view', id=id))


# Candidates
@recruitment_bp.route('/recruitment/candidates')
@login_required
def candidate_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    keyword = request.args.get('keyword', '')
    status = request.args.get('status', '')
    opening_id = request.args.get('opening_id', type=int)
    
    query = Candidate.query
    
    if keyword:
        query = query.filter(
            (Candidate.full_name.ilike(f'%{keyword}%')) | 
            (Candidate.email.ilike(f'%{keyword}%')) |
            (Candidate.phone.ilike(f'%{keyword}%'))
        )
    
    if status:
        query = query.filter(Candidate.status == status)
    
    if opening_id:
        query = query.filter(Candidate.job_opening_id == opening_id)
    
    pagination = query.order_by(Candidate.application_date.desc()).paginate(page=page, per_page=per_page)
    candidates = pagination.items
    
    openings = JobOpening.query.filter_by(status=JobOpeningStatus.OPEN.name).all()
    
    return render_template('recruitment/candidates/index.html',
                          candidates=candidates,
                          pagination=pagination,
                          openings=openings,
                          candidate_statuses=CandidateStatus,
                          keyword=keyword,
                          status=status,
                          opening_id=opening_id,
                          title='Danh sách ứng viên')


@recruitment_bp.route('/recruitment/candidates/create', methods=['GET', 'POST'])
@login_required
def candidate_create():
    form = CandidateForm()
    
    if form.validate_on_submit():
        candidate = Candidate(
            job_opening_id=form.job_opening_id.data,
            full_name=form.full_name.data,
            email=form.email.data,
            phone=form.phone.data,
            cover_letter=form.cover_letter.data,
            status=form.status.data,
            application_date=form.application_date.data,
            evaluation=form.evaluation.data,
            notes=form.notes.data
        )
        
        # Xử lý upload CV nếu có
        if form.cv_file.data:
            filename = secure_filename(form.cv_file.data.filename)
            file_ext = os.path.splitext(filename)[1]
            new_filename = f"cv_{candidate.full_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_ext}"
            
            uploads_dir = os.path.join(current_app.root_path, 'static/uploads/recruitment/cv')
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir)
                
            cv_path = os.path.join(uploads_dir, new_filename)
            form.cv_file.data.save(cv_path)
            candidate.cv_file = f"uploads/recruitment/cv/{new_filename}"
        
        db.session.add(candidate)
        db.session.commit()
        
        flash('Hồ sơ ứng viên mới đã được tạo thành công!', 'success')
        return redirect(url_for('recruitment.candidate_view', id=candidate.id))
    
    return render_template('recruitment/candidates/create.html',
                          form=form,
                          title='Thêm ứng viên mới')


@recruitment_bp.route('/recruitment/candidates/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def candidate_edit(id):
    candidate = Candidate.query.get_or_404(id)
    form = CandidateEditForm(obj=candidate)
    form.candidate_id.data = candidate.id
    
    if form.validate_on_submit():
        candidate.job_opening_id = form.job_opening_id.data
        candidate.full_name = form.full_name.data
        candidate.email = form.email.data
        candidate.phone = form.phone.data
        candidate.cover_letter = form.cover_letter.data
        candidate.status = form.status.data
        candidate.application_date = form.application_date.data
        candidate.evaluation = form.evaluation.data
        candidate.notes = form.notes.data
        
        # Xử lý upload CV mới nếu có
        if form.cv_file.data:
            # Xóa CV cũ nếu có
            if candidate.cv_file:
                old_cv_path = os.path.join(current_app.root_path, 'static', candidate.cv_file)
                if os.path.exists(old_cv_path):
                    os.remove(old_cv_path)
            
            filename = secure_filename(form.cv_file.data.filename)
            file_ext = os.path.splitext(filename)[1]
            new_filename = f"cv_{candidate.full_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_ext}"
            
            uploads_dir = os.path.join(current_app.root_path, 'static/uploads/recruitment/cv')
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir)
                
            cv_path = os.path.join(uploads_dir, new_filename)
            form.cv_file.data.save(cv_path)
            candidate.cv_file = f"uploads/recruitment/cv/{new_filename}"
        
        db.session.commit()
        
        flash('Hồ sơ ứng viên đã được cập nhật!', 'success')
        return redirect(url_for('recruitment.candidate_view', id=candidate.id))
    
    return render_template('recruitment/candidates/edit.html',
                          form=form,
                          candidate=candidate,
                          title='Chỉnh sửa hồ sơ ứng viên')


@recruitment_bp.route('/recruitment/candidates/<int:id>')
@login_required
def candidate_view(id):
    candidate = Candidate.query.get_or_404(id)
    interviews = Interview.query.filter_by(candidate_id=id).order_by(Interview.scheduled_date).all()
    
    return render_template('recruitment/candidates/view.html',
                          candidate=candidate,
                          interviews=interviews,
                          title=f'Chi tiết ứng viên: {candidate.full_name}')


@recruitment_bp.route('/recruitment/candidates/<int:id>/update-status', methods=['POST'])
@login_required
def candidate_update_status(id):
    candidate = Candidate.query.get_or_404(id)
    status = request.form.get('status')
    
    if status not in [s.name for s in CandidateStatus]:
        flash('Trạng thái không hợp lệ!', 'danger')
        return redirect(url_for('recruitment.candidate_view', id=id))
    
    candidate.status = status
    db.session.commit()
    
    flash(f'Trạng thái ứng viên đã được cập nhật thành {dict([(s.name, s.value) for s in CandidateStatus])[status]}!', 'success')
    return redirect(url_for('recruitment.candidate_view', id=id))


# Interviews
@recruitment_bp.route('/recruitment/interviews')
@login_required
def interview_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    status = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = Interview.query
    
    if status:
        query = query.filter(Interview.status == status)
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Interview.scheduled_date >= date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            date_to = date_to.replace(hour=23, minute=59, second=59)
            query = query.filter(Interview.scheduled_date <= date_to)
        except ValueError:
            pass
    
    pagination = query.order_by(Interview.scheduled_date).paginate(page=page, per_page=per_page)
    interviews = pagination.items
    
    return render_template('recruitment/interviews/index.html',
                          interviews=interviews,
                          pagination=pagination,
                          interview_statuses=InterviewStatus,
                          status=status,
                          date_from=date_from,
                          date_to=date_to,
                          title='Lịch phỏng vấn')


@recruitment_bp.route('/recruitment/interviews/create', methods=['GET', 'POST'])
@login_required
def interview_create():
    form = InterviewForm()
    
    # Pre-fill candidate_id from URL parameter
    candidate_id = request.args.get('candidate_id', type=int)
    if candidate_id and request.method == 'GET':
        form.candidate_id.data = candidate_id
    
    if form.validate_on_submit():
        # Kết hợp ngày và giờ
        scheduled_date = form.scheduled_date.data
        scheduled_time = form.scheduled_time.data
        
        try:
            hour, minute = map(int, scheduled_time.split(':'))
            scheduled_datetime = datetime.combine(scheduled_date, datetime.min.time())
            scheduled_datetime = scheduled_datetime.replace(hour=hour, minute=minute)
        except ValueError:
            flash('Định dạng giờ không hợp lệ. Vui lòng sử dụng định dạng HH:MM', 'danger')
            return render_template('recruitment/interviews/create.html',
                                  form=form,
                                  title='Lên lịch phỏng vấn')
        
        interview = Interview(
            candidate_id=form.candidate_id.data,
            scheduled_date=scheduled_datetime,
            interview_type=form.interview_type.data,
            interviewers=form.interviewers.data,
            location=form.location.data,
            status=form.status.data,
            feedback=form.feedback.data,
            rating=form.rating.data if form.rating.data else None
        )
        
        # Cập nhật trạng thái ứng viên
        candidate = Candidate.query.get(form.candidate_id.data)
        if candidate.status == CandidateStatus.APPLIED.name or candidate.status == CandidateStatus.SCREENING.name:
            candidate.status = CandidateStatus.INTERVIEW_SCHEDULED.name
        
        db.session.add(interview)
        db.session.commit()
        
        flash('Lịch phỏng vấn đã được tạo thành công!', 'success')
        return redirect(url_for('recruitment.interview_view', id=interview.id))
    
    return render_template('recruitment/interviews/create.html',
                          form=form,
                          title='Lên lịch phỏng vấn')


@recruitment_bp.route('/recruitment/interviews/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def interview_edit(id):
    interview = Interview.query.get_or_404(id)
    form = InterviewEditForm(obj=interview)
    form.interview_id.data = interview.id
    
    # Pre-fill scheduled_time
    if request.method == 'GET':
        form.scheduled_time.data = interview.scheduled_date.strftime('%H:%M')
    
    if form.validate_on_submit():
        # Kết hợp ngày và giờ
        scheduled_date = form.scheduled_date.data
        scheduled_time = form.scheduled_time.data
        
        try:
            hour, minute = map(int, scheduled_time.split(':'))
            scheduled_datetime = datetime.combine(scheduled_date, datetime.min.time())
            scheduled_datetime = scheduled_datetime.replace(hour=hour, minute=minute)
        except ValueError:
            flash('Định dạng giờ không hợp lệ. Vui lòng sử dụng định dạng HH:MM', 'danger')
            return render_template('recruitment/interviews/edit.html',
                                  form=form,
                                  interview=interview,
                                  title='Chỉnh sửa lịch phỏng vấn')
        
        interview.candidate_id = form.candidate_id.data
        interview.scheduled_date = scheduled_datetime
        interview.interview_type = form.interview_type.data
        interview.interviewers = form.interviewers.data
        interview.location = form.location.data
        interview.status = form.status.data
        interview.feedback = form.feedback.data
        interview.rating = form.rating.data if form.rating.data else None
        
        # Cập nhật trạng thái ứng viên nếu hoàn thành phỏng vấn
        if form.status.data == InterviewStatus.COMPLETED.name:
            candidate = Candidate.query.get(form.candidate_id.data)
            if candidate.status == CandidateStatus.INTERVIEW_SCHEDULED.name:
                candidate.status = CandidateStatus.INTERVIEWED.name
        
        db.session.commit()
        
        flash('Lịch phỏng vấn đã được cập nhật!', 'success')
        return redirect(url_for('recruitment.interview_view', id=interview.id))
    
    return render_template('recruitment/interviews/edit.html',
                          form=form,
                          interview=interview,
                          title='Chỉnh sửa lịch phỏng vấn')


@recruitment_bp.route('/recruitment/interviews/<int:id>')
@login_required
def interview_view(id):
    interview = Interview.query.get_or_404(id)
    
    return render_template('recruitment/interviews/view.html',
                          interview=interview,
                          title=f'Chi tiết phỏng vấn: {interview.candidate.full_name}')


@recruitment_bp.route('/recruitment/interviews/<int:id>/complete', methods=['POST'])
@login_required
def interview_complete(id):
    interview = Interview.query.get_or_404(id)
    feedback = request.form.get('feedback', '')
    rating = request.form.get('rating', '')
    
    interview.status = InterviewStatus.COMPLETED.name
    interview.feedback = feedback
    interview.rating = int(rating) if rating and rating.isdigit() else None
    
    # Cập nhật trạng thái ứng viên
    candidate = interview.candidate
    if candidate.status == CandidateStatus.INTERVIEW_SCHEDULED.name:
        candidate.status = CandidateStatus.INTERVIEWED.name
    
    db.session.commit()
    
    flash('Phỏng vấn đã được hoàn thành!', 'success')
    return redirect(url_for('recruitment.interview_view', id=id))


@recruitment_bp.route('/recruitment/interviews/<int:id>/cancel', methods=['POST'])
@login_required
def interview_cancel(id):
    interview = Interview.query.get_or_404(id)
    reason = request.form.get('reason', '')
    
    interview.status = InterviewStatus.CANCELED.name
    interview.feedback = f"Đã hủy: {reason}"
    
    db.session.commit()
    
    flash('Phỏng vấn đã được hủy!', 'success')
    return redirect(url_for('recruitment.interview_view', id=id))


# API endpoints
@recruitment_bp.route('/api/recruitment/positions')
@login_required
def api_positions():
    positions = JobPosition.query.filter_by(is_active=True).all()
    
    return jsonify([{
        'id': position.id,
        'title': position.title,
        'department': position.department.name,
        'requirements': position.required_experience
    } for position in positions])


@recruitment_bp.route('/api/recruitment/candidates/<int:opening_id>')
@login_required
def api_candidates_by_opening(opening_id):
    candidates = Candidate.query.filter_by(job_opening_id=opening_id).all()
    
    return jsonify([{
        'id': candidate.id,
        'name': candidate.full_name,
        'email': candidate.email,
        'status': candidate.status,
        'application_date': candidate.application_date.strftime('%Y-%m-%d')
    } for candidate in candidates])