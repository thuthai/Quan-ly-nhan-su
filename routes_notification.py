from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
import logging
from app import db
from notifications import check_expiring_contracts, send_contract_notification
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