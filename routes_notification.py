from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
import logging
from app import db
from models import NotificationEmail
from notifications import check_expiring_contracts, send_contract_notification, send_email_notification
from forms_notification import NotificationEmailForm, NotificationEmailEditForm, SendTestEmailForm
from functools import wraps

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Bạn không có quyền truy cập trang này.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return login_required(decorated_function)

notification_bp = Blueprint('notification', __name__, url_prefix='/notifications')


@notification_bp.route('/help')
@login_required
def help():
    """Hiển thị trang hướng dẫn sử dụng tính năng thông báo"""
    return render_template('notifications_help.html', title="Hướng dẫn thông báo")


@notification_bp.route('/check_expiring')
@admin_required
def check_expiring_manual():
    """Chạy kiểm tra thủ công các hợp đồng sắp hết hạn"""
    try:
        days = request.args.get('days', default=30, type=int)
        count = check_expiring_contracts(days_threshold=days)
        flash(f'Đã kiểm tra thành công! {count} hợp đồng sắp hết hạn trong {days} ngày tới.', 'success')
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra hợp đồng sắp hết hạn: {e}")
        flash(f'Có lỗi xảy ra khi kiểm tra hợp đồng: {str(e)}', 'danger')
    
    return redirect(url_for('notification.help'))


@notification_bp.route('/emails')
@admin_required
def email_list():
    """Hiển thị danh sách email nhận thông báo"""
    emails = NotificationEmail.query.order_by(NotificationEmail.created_at.desc()).all()
    form = NotificationEmailForm()
    test_form = SendTestEmailForm()
    
    return render_template('notifications/emails.html',
                          emails=emails,
                          form=form,
                          test_form=test_form,
                          title='Quản lý email nhận thông báo')


@notification_bp.route('/emails/create', methods=['POST'])
@admin_required
def create_email():
    """Thêm email mới nhận thông báo"""
    form = NotificationEmailForm()
    
    if form.validate_on_submit():
        # Kiểm tra email đã tồn tại chưa
        existing = NotificationEmail.query.filter_by(email=form.email.data).first()
        if existing:
            flash(f'Email {form.email.data} đã tồn tại trong hệ thống!', 'danger')
            return redirect(url_for('notification.email_list'))
        
        email = NotificationEmail(
            email=form.email.data,
            name=form.name.data,
            is_active=form.is_active.data,
            notification_types=form.notification_types.data,
            created_by_id=current_user.id
        )
        
        db.session.add(email)
        db.session.commit()
        
        flash(f'Đã thêm email {form.email.data} vào danh sách nhận thông báo!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Lỗi ở trường {getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('notification.email_list'))


@notification_bp.route('/emails/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_email(id):
    """Chỉnh sửa email nhận thông báo"""
    email = NotificationEmail.query.get_or_404(id)
    form = NotificationEmailEditForm(obj=email)
    
    if request.method == 'GET':
        form.email_id.data = email.id
        return render_template('notifications/edit_email.html',
                             form=form,
                             email=email,
                             title=f'Chỉnh sửa email: {email.email}')
    
    if form.validate_on_submit():
        # Kiểm tra email đã tồn tại chưa (nếu thay đổi)
        if email.email != form.email.data:
            existing = NotificationEmail.query.filter_by(email=form.email.data).first()
            if existing:
                flash(f'Email {form.email.data} đã tồn tại trong hệ thống!', 'danger')
                return redirect(url_for('notification.edit_email', id=id))
        
        email.email = form.email.data
        email.name = form.name.data
        email.is_active = form.is_active.data
        email.notification_types = form.notification_types.data
        
        db.session.commit()
        
        flash(f'Đã cập nhật thông tin email {email.email} thành công!', 'success')
        return redirect(url_for('notification.email_list'))
    
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'Lỗi ở trường {getattr(form, field).label.text}: {error}', 'danger')
    
    return render_template('notifications/edit_email.html',
                         form=form,
                         email=email,
                         title=f'Chỉnh sửa email: {email.email}')


@notification_bp.route('/emails/<int:id>/delete', methods=['POST'])
@admin_required
def delete_email(id):
    """Xóa email khỏi danh sách nhận thông báo"""
    email = NotificationEmail.query.get_or_404(id)
    
    db.session.delete(email)
    db.session.commit()
    
    flash(f'Đã xóa email {email.email} khỏi danh sách nhận thông báo!', 'success')
    return redirect(url_for('notification.email_list'))


@notification_bp.route('/emails/send_test', methods=['POST'])
@admin_required
def send_test_email():
    """Gửi email thử nghiệm"""
    form = SendTestEmailForm()
    
    if form.validate_on_submit():
        try:
            result = send_email_notification(
                to_email=form.email.data,
                subject=form.subject.data,
                html_content=f"<p>{form.message.data}</p>"
            )
            
            if result:
                flash(f'Đã gửi email thử nghiệm đến {form.email.data} thành công!', 'success')
            else:
                flash(f'Không thể gửi email đến {form.email.data}. Vui lòng kiểm tra cài đặt SENDGRID_API_KEY.', 'danger')
        except Exception as e:
            logging.error(f"Lỗi khi gửi email thử nghiệm: {e}")
            flash(f'Có lỗi xảy ra khi gửi email: {str(e)}', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Lỗi ở trường {getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('notification.email_list'))