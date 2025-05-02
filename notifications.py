"""
Module quản lý thông báo: email và Telegram
"""
import os
import sys
import logging
from datetime import datetime, date, timedelta
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from telegram import Bot
from telegram.error import TelegramError
from models import Contract, ContractStatus, Employee, Department, User
from app import app, db

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Đọc API keys từ môi trường
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Email mặc định của người gửi
DEFAULT_FROM_EMAIL = "no-reply@admin.com"

async def send_telegram_message(message):
    """
    Gửi tin nhắn qua Telegram
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Các biến môi trường TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID không được cấu hình")
        return False
    
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='HTML')
        logger.info(f"Đã gửi tin nhắn Telegram thành công")
        return True
    except TelegramError as e:
        logger.error(f"Lỗi khi gửi tin nhắn Telegram: {e}")
        return False

def send_email(to_email, subject, html_content=None, text_content=None):
    """
    Gửi email qua SendGrid
    """
    if not SENDGRID_API_KEY:
        logger.warning("Biến môi trường SENDGRID_API_KEY không được cấu hình")
        return False
    
    if not html_content and not text_content:
        logger.error("Cần cung cấp nội dung email (HTML hoặc text)")
        return False
    
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        
        message = Mail(
            from_email=Email(DEFAULT_FROM_EMAIL),
            to_emails=To(to_email),
            subject=subject
        )
        
        if html_content:
            message.content = Content("text/html", html_content)
        elif text_content:
            message.content = Content("text/plain", text_content)
        
        response = sg.send(message)
        logger.info(f"Đã gửi email thành công đến {to_email}, mã trạng thái: {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"Lỗi khi gửi email: {e}")
        return False

def check_expiring_contracts(days_threshold=30):
    """
    Kiểm tra và thông báo các hợp đồng sắp hết hạn trong ngưỡng ngày được chỉ định
    """
    today = date.today()
    expiry_date = today + timedelta(days=days_threshold)
    
    # Lấy danh sách hợp đồng sắp hết hạn
    expiring_contracts = Contract.query.filter(
        Contract.status == ContractStatus.ACTIVE.name,
        Contract.end_date.isnot(None),  # Chỉ kiểm tra hợp đồng có ngày kết thúc
        Contract.end_date <= expiry_date,  # Sắp hết hạn trong ngưỡng ngày
        Contract.end_date > today  # Chưa hết hạn
    ).all()
    
    if not expiring_contracts:
        logger.info(f"Không có hợp đồng nào sắp hết hạn trong {days_threshold} ngày tới")
        return
    
    # Tạo thông báo cho từng hợp đồng
    for contract in expiring_contracts:
        days_remaining = (contract.end_date - today).days
        
        # Lấy thông tin nhân viên
        employee = contract.employee
        if not employee:
            logger.warning(f"Không tìm thấy nhân viên cho hợp đồng {contract.contract_number}")
            continue
        
        # Lấy thông tin người quản lý
        managers = User.query.filter_by(role="admin").all()
        manager_emails = [manager.email for manager in managers]
        
        # Tạo nội dung email
        subject = f"CẢNH BÁO: Hợp đồng của {employee.full_name} sắp hết hạn"
        html_content = f"""
        <h2>Thông báo hợp đồng sắp hết hạn</h2>
        <p>Kính gửi Ban Quản lý,</p>
        <p>Hệ thống phát hiện một hợp đồng sắp hết hạn trong <strong>{days_remaining}</strong> ngày tới.</p>
        <h3>Chi tiết hợp đồng:</h3>
        <ul>
            <li><strong>Mã hợp đồng:</strong> {contract.contract_number}</li>
            <li><strong>Nhân viên:</strong> {employee.full_name} (Mã: {employee.employee_code})</li>
            <li><strong>Phòng ban:</strong> {employee.department.name if employee.department else 'N/A'}</li>
            <li><strong>Vị trí:</strong> {contract.job_title}</li>
            <li><strong>Ngày bắt đầu:</strong> {contract.start_date.strftime('%d/%m/%Y')}</li>
            <li><strong>Ngày kết thúc:</strong> {contract.end_date.strftime('%d/%m/%Y')}</li>
        </ul>
        <p>Vui lòng xem xét gia hạn hoặc chấm dứt hợp đồng trước ngày hết hạn.</p>
        <p>Trân trọng,<br>Hệ thống Quản lý Nhân sự</p>
        """
        
        # Tạo nội dung telegram
        telegram_message = f"""
<b>⚠️ CẢNH BÁO: Hợp đồng sắp hết hạn</b>

Hợp đồng của <b>{employee.full_name}</b> sẽ hết hạn trong <b>{days_remaining}</b> ngày.

<b>Chi tiết:</b>
• Mã hợp đồng: {contract.contract_number}
• Nhân viên: {employee.full_name} (Mã: {employee.employee_code})
• Phòng ban: {employee.department.name if employee.department else 'N/A'} 
• Vị trí: {contract.job_title}
• Ngày kết thúc: {contract.end_date.strftime('%d/%m/%Y')}

Vui lòng xem xét gia hạn hoặc chấm dứt hợp đồng.
        """
        
        # Gửi email đến tất cả quản lý
        for email in manager_emails:
            send_email(email, subject, html_content=html_content)
        
        # Gửi thông báo Telegram
        import asyncio
        asyncio.run(send_telegram_message(telegram_message))

def send_contract_notification(contract_id, notification_type):
    """
    Gửi thông báo khi có sự kiện xảy ra với hợp đồng
    
    notification_type có thể là:
    - 'new': Hợp đồng mới được tạo
    - 'updated': Hợp đồng được cập nhật
    - 'terminated': Hợp đồng bị chấm dứt
    """
    contract = Contract.query.get(contract_id)
    if not contract:
        logger.error(f"Không tìm thấy hợp đồng với ID {contract_id}")
        return False
    
    employee = contract.employee
    if not employee:
        logger.warning(f"Không tìm thấy nhân viên cho hợp đồng {contract.contract_number}")
        return False
    
    # Lấy thông tin người quản lý
    managers = User.query.filter_by(role="admin").all()
    manager_emails = [manager.email for manager in managers]
    
    # Xác định thông tin thông báo dựa trên loại
    if notification_type == 'new':
        subject = f"Hợp đồng mới đã được tạo: {contract.contract_number}"
        action = "tạo mới"
        icon = "🆕"
    elif notification_type == 'updated':
        subject = f"Hợp đồng đã được cập nhật: {contract.contract_number}"
        action = "cập nhật"
        icon = "🔄"
    elif notification_type == 'terminated':
        subject = f"Hợp đồng đã bị chấm dứt: {contract.contract_number}"
        action = "chấm dứt"
        icon = "❌"
    else:
        logger.error(f"Loại thông báo không hợp lệ: {notification_type}")
        return False
    
    # Tạo nội dung email
    html_content = f"""
    <h2>Thông báo hợp đồng</h2>
    <p>Kính gửi Ban Quản lý,</p>
    <p>Hợp đồng sau đây đã được {action}:</p>
    <h3>Chi tiết hợp đồng:</h3>
    <ul>
        <li><strong>Mã hợp đồng:</strong> {contract.contract_number}</li>
        <li><strong>Nhân viên:</strong> {employee.full_name} (Mã: {employee.employee_code})</li>
        <li><strong>Phòng ban:</strong> {employee.department.name if employee.department else 'N/A'}</li>
        <li><strong>Vị trí:</strong> {contract.job_title}</li>
        <li><strong>Ngày bắt đầu:</strong> {contract.start_date.strftime('%d/%m/%Y')}</li>
        <li><strong>Ngày kết thúc:</strong> {contract.end_date.strftime('%d/%m/%Y') if contract.end_date else 'Không xác định'}</li>
        <li><strong>Trạng thái:</strong> {contract.status}</li>
    </ul>
    <p>Trân trọng,<br>Hệ thống Quản lý Nhân sự</p>
    """
    
    # Tạo nội dung telegram
    telegram_message = f"""
<b>{icon} Thông báo: Hợp đồng đã được {action}</b>

<b>Chi tiết:</b>
• Mã hợp đồng: {contract.contract_number}
• Nhân viên: {employee.full_name} (Mã: {employee.employee_code})
• Phòng ban: {employee.department.name if employee.department else 'N/A'}
• Vị trí: {contract.job_title}
• Ngày bắt đầu: {contract.start_date.strftime('%d/%m/%Y')}
• Ngày kết thúc: {contract.end_date.strftime('%d/%m/%Y') if contract.end_date else 'Không xác định'}
• Trạng thái: {contract.status}
    """
    
    # Gửi email đến tất cả quản lý
    for email in manager_emails:
        send_email(email, subject, html_content=html_content)
    
    # Gửi thông báo Telegram
    import asyncio
    asyncio.run(send_telegram_message(telegram_message))
    
    return True

# Hàm kiểm tra hợp đồng sắp hết hạn có thể được gọi từ lịch trình cron hoặc thủ công
if __name__ == "__main__":
    with app.app_context():
        # Nếu được chạy từ dòng lệnh, kiểm tra các hợp đồng sắp hết hạn
        check_expiring_contracts()