"""
Module xử lý gửi thông báo qua email và Telegram
"""
import os
import logging
from datetime import datetime, date, timedelta
import json
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import telegram
from telegram.error import TelegramError
from app import db
from models import Contract, Employee, ContractStatus


logger = logging.getLogger(__name__)

# Kiểm tra xem các API key có tồn tại không
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')


def send_email_notification(to_email, subject, text_content=None, html_content=None):
    """
    Gửi thông báo qua email sử dụng SendGrid
    
    Args:
        to_email (str): Địa chỉ email người nhận
        subject (str): Tiêu đề email
        text_content (str, optional): Nội dung email dạng text
        html_content (str, optional): Nội dung email dạng HTML
    
    Returns:
        bool: True nếu gửi thành công, False nếu có lỗi
    """
    if not SENDGRID_API_KEY:
        logger.warning("Không thể gửi email: SENDGRID_API_KEY không tồn tại.")
        return False
    
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        
        # Email người gửi
        from_email = Email("noreply@hrmanager.vn")
        
        message = Mail(
            from_email=from_email,
            to_emails=To(to_email),
            subject=subject
        )
        
        if html_content:
            message.content = Content("text/html", html_content)
        elif text_content:
            message.content = Content("text/plain", text_content)
        
        response = sg.send(message)
        logger.info(f"Đã gửi email đến {to_email}: {subject} (Status: {response.status_code})")
        return True
    except Exception as e:
        logger.error(f"Lỗi khi gửi email: {e}")
        return False


def send_telegram_notification(message):
    """
    Gửi thông báo qua Telegram
    
    Args:
        message (str): Nội dung tin nhắn
    
    Returns:
        bool: True nếu gửi thành công, False nếu có lỗi
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Không thể gửi Telegram: TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID không tồn tại.")
        return False
    
    try:
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="HTML")
        logger.info(f"Đã gửi thông báo Telegram: {message[:50]}...")
        return True
    except TelegramError as e:
        logger.error(f"Lỗi khi gửi Telegram: {e}")
        return False


def send_contract_notification(contract_id, event_type):
    """
    Gửi thông báo liên quan đến hợp đồng
    
    Args:
        contract_id (int): ID của hợp đồng
        event_type (str): Loại sự kiện ('new', 'updated', 'terminated', 'expiring')
    
    Returns:
        bool: True nếu gửi thành công, False nếu có lỗi
    """
    try:
        contract = Contract.query.get(contract_id)
        if not contract:
            logger.error(f"Không tìm thấy hợp đồng với ID {contract_id}")
            return False
        
        employee = Employee.query.get(contract.employee_id)
        if not employee:
            logger.error(f"Không tìm thấy nhân viên cho hợp đồng {contract_id}")
            return False
        
        # Thông tin chung
        contract_info = {
            "id": contract.id,
            "contract_number": contract.contract_number,
            "employee_name": employee.full_name if employee else "Unknown",
            "employee_id": employee.employee_id if employee else "N/A",
            "contract_type": contract.contract_type, 
            "start_date": contract.start_date.strftime("%d/%m/%Y") if contract.start_date else "N/A",
            "end_date": contract.end_date.strftime("%d/%m/%Y") if contract.end_date else "Không xác định",
            "job_title": contract.job_title or "N/A",
            "base_salary": f"{contract.base_salary:,.0f} VND" if contract.base_salary else "N/A",
            "status": contract.status
        }
        
        # Email và thông báo Telegram dựa trên loại sự kiện
        if event_type == 'new':
            subject = f"Hợp đồng mới: {contract.contract_number} - {employee.full_name}"
            html_content = f"""
            <h2>Hợp đồng mới đã được tạo</h2>
            <p><strong>Số hợp đồng:</strong> {contract_info['contract_number']}</p>
            <p><strong>Nhân viên:</strong> {contract_info['employee_name']} ({contract_info['employee_id']})</p>
            <p><strong>Loại hợp đồng:</strong> {contract_info['contract_type']}</p>
            <p><strong>Ngày bắt đầu:</strong> {contract_info['start_date']}</p>
            <p><strong>Ngày kết thúc:</strong> {contract_info['end_date']}</p>
            <p><strong>Vị trí:</strong> {contract_info['job_title']}</p>
            <p><strong>Lương cơ bản:</strong> {contract_info['base_salary']}</p>
            <p>Vui lòng kiểm tra thông tin và xác nhận trong hệ thống.</p>
            """
            
            telegram_message = f"""
            🔔 <b>Hợp đồng mới đã được tạo</b>
            
            📄 Số hợp đồng: {contract_info['contract_number']}
            👤 Nhân viên: {contract_info['employee_name']} ({contract_info['employee_id']})
            📋 Loại hợp đồng: {contract_info['contract_type']}
            📅 Thời hạn: {contract_info['start_date']} - {contract_info['end_date']}
            💼 Vị trí: {contract_info['job_title']}
            💰 Lương: {contract_info['base_salary']}
            """
        
        elif event_type == 'updated':
            subject = f"Cập nhật hợp đồng: {contract.contract_number} - {employee.full_name}"
            html_content = f"""
            <h2>Hợp đồng đã được cập nhật</h2>
            <p><strong>Số hợp đồng:</strong> {contract_info['contract_number']}</p>
            <p><strong>Nhân viên:</strong> {contract_info['employee_name']} ({contract_info['employee_id']})</p>
            <p><strong>Loại hợp đồng:</strong> {contract_info['contract_type']}</p>
            <p><strong>Ngày bắt đầu:</strong> {contract_info['start_date']}</p>
            <p><strong>Ngày kết thúc:</strong> {contract_info['end_date']}</p>
            <p><strong>Vị trí:</strong> {contract_info['job_title']}</p>
            <p><strong>Lương cơ bản:</strong> {contract_info['base_salary']}</p>
            <p><strong>Trạng thái:</strong> {contract_info['status']}</p>
            <p>Vui lòng kiểm tra thông tin cập nhật trong hệ thống.</p>
            """
            
            telegram_message = f"""
            🔄 <b>Hợp đồng đã được cập nhật</b>
            
            📄 Số hợp đồng: {contract_info['contract_number']}
            👤 Nhân viên: {contract_info['employee_name']} ({contract_info['employee_id']})
            📋 Loại hợp đồng: {contract_info['contract_type']}
            📅 Thời hạn: {contract_info['start_date']} - {contract_info['end_date']}
            💼 Vị trí: {contract_info['job_title']}
            💰 Lương: {contract_info['base_salary']}
            ⚙️ Trạng thái: {contract_info['status']}
            """
        
        elif event_type == 'terminated':
            subject = f"Chấm dứt hợp đồng: {contract.contract_number} - {employee.full_name}"
            html_content = f"""
            <h2>Hợp đồng đã bị chấm dứt</h2>
            <p><strong>Số hợp đồng:</strong> {contract_info['contract_number']}</p>
            <p><strong>Nhân viên:</strong> {contract_info['employee_name']} ({contract_info['employee_id']})</p>
            <p><strong>Loại hợp đồng:</strong> {contract_info['contract_type']}</p>
            <p><strong>Ngày bắt đầu:</strong> {contract_info['start_date']}</p>
            <p><strong>Ngày kết thúc ban đầu:</strong> {contract_info['end_date']}</p>
            <p><strong>Ngày chấm dứt thực tế:</strong> {contract.terminated_date.strftime("%d/%m/%Y") if contract.terminated_date else "N/A"}</p>
            <p><strong>Lý do chấm dứt:</strong> {contract.termination_reason or "Không có thông tin"}</p>
            <p>Vui lòng kiểm tra thông tin và cập nhật trong hệ thống.</p>
            """
            
            telegram_message = f"""
            ❌ <b>Hợp đồng đã bị chấm dứt</b>
            
            📄 Số hợp đồng: {contract_info['contract_number']}
            👤 Nhân viên: {contract_info['employee_name']} ({contract_info['employee_id']})
            📋 Loại hợp đồng: {contract_info['contract_type']}
            📅 Bắt đầu: {contract_info['start_date']}
            🛑 Ngày chấm dứt: {contract.terminated_date.strftime("%d/%m/%Y") if contract.terminated_date else "N/A"}
            📝 Lý do: {contract.termination_reason or "Không có thông tin"}
            """
        
        elif event_type == 'expiring':
            # Tính số ngày còn lại
            days_remaining = (contract.end_date - date.today()).days
            
            subject = f"Cảnh báo hợp đồng sắp hết hạn: {contract.contract_number} - {employee.full_name}"
            html_content = f"""
            <h2>Cảnh báo: Hợp đồng sắp hết hạn</h2>
            <p><strong>Số hợp đồng:</strong> {contract_info['contract_number']}</p>
            <p><strong>Nhân viên:</strong> {contract_info['employee_name']} ({contract_info['employee_id']})</p>
            <p><strong>Loại hợp đồng:</strong> {contract_info['contract_type']}</p>
            <p><strong>Ngày bắt đầu:</strong> {contract_info['start_date']}</p>
            <p><strong>Ngày kết thúc:</strong> {contract_info['end_date']}</p>
            <p><strong>Số ngày còn lại:</strong> {days_remaining} ngày</p>
            <p><strong>Vị trí:</strong> {contract_info['job_title']}</p>
            <p>Vui lòng xem xét gia hạn hoặc tạo hợp đồng mới.</p>
            """
            
            telegram_message = f"""
            ⚠️ <b>Cảnh báo: Hợp đồng sắp hết hạn</b>
            
            📄 Số hợp đồng: {contract_info['contract_number']}
            👤 Nhân viên: {contract_info['employee_name']} ({contract_info['employee_id']})
            📋 Loại hợp đồng: {contract_info['contract_type']}
            📅 Hết hạn: {contract_info['end_date']}
            ⏱️ Còn lại: {days_remaining} ngày
            💼 Vị trí: {contract_info['job_title']}
            
            Vui lòng xem xét gia hạn hoặc tạo hợp đồng mới.
            """
        
        else:
            logger.error(f"Loại sự kiện không hợp lệ: {event_type}")
            return False
        
        # Gửi email đến admin HR
        email_sent = False
        if SENDGRID_API_KEY:
            # Trong một hệ thống thực tế, bạn sẽ lấy email của HR manager từ db
            email_sent = send_email_notification(
                to_email="hr@example.com",  # Thay bằng email thực tế của HR manager
                subject=subject,
                html_content=html_content
            )
        
        # Gửi thông báo Telegram
        telegram_sent = False
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            telegram_sent = send_telegram_notification(telegram_message)
        
        return email_sent or telegram_sent
    
    except Exception as e:
        logger.error(f"Lỗi khi gửi thông báo hợp đồng: {e}")
        return False


def check_expiring_contracts(days_threshold=30):
    """
    Kiểm tra các hợp đồng sắp hết hạn và gửi thông báo
    
    Args:
        days_threshold (int): Ngưỡng ngày (số ngày trước khi hết hạn)
    
    Returns:
        int: Số hợp đồng sắp hết hạn được thông báo
    """
    try:
        today = date.today()
        expiry_date = today + timedelta(days=days_threshold)
        
        # Tìm các hợp đồng sắp hết hạn
        expiring_contracts = Contract.query.filter(
            Contract.end_date.isnot(None),  # Không bao gồm hợp đồng không xác định thời hạn
            Contract.end_date <= expiry_date,
            Contract.end_date > today,
            Contract.status == ContractStatus.ACTIVE.name
        ).all()
        
        notification_count = 0
        for contract in expiring_contracts:
            # Gửi thông báo cho mỗi hợp đồng
            if send_contract_notification(contract.id, 'expiring'):
                notification_count += 1
                logger.info(f"Đã gửi thông báo hợp đồng sắp hết hạn: {contract.contract_number}")
        
        return notification_count
    
    except Exception as e:
        logger.error(f"Lỗi khi kiểm tra hợp đồng sắp hết hạn: {e}")
        return 0