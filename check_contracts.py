"""
Script để kiểm tra các hợp đồng sắp hết hạn và gửi thông báo
Script này có thể được chạy tự động thông qua cron
"""
import sys
import logging
from datetime import datetime
from app import app, db
from notifications import check_expiring_contracts

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """
    Hàm chính của script
    
    Sử dụng: python check_contracts.py [days_threshold]
    - days_threshold: Số ngày trước khi hết hạn (mặc định 30)
    """
    try:
        # Lấy tham số từ dòng lệnh nếu có
        days_threshold = 30
        if len(sys.argv) > 1:
            days_threshold = int(sys.argv[1])
        
        logger.info(f"Kiểm tra hợp đồng sắp hết hạn trong {days_threshold} ngày tới...")
        
        with app.app_context():
            count = check_expiring_contracts(days_threshold=days_threshold)
            
            logger.info(f"Đã kiểm tra xong, {count} thông báo đã được gửi.")
        
        return 0
    except Exception as e:
        logger.error(f"Lỗi: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())