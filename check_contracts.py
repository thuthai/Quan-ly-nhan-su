"""
Script để kiểm tra các hợp đồng sắp hết hạn và gửi thông báo
Script này có thể được chạy tự động thông qua cron
"""
import os
import sys
import logging
from datetime import datetime
from app import app, db
from notifications import check_expiring_contracts

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        logger.info("Bắt đầu kiểm tra hợp đồng sắp hết hạn...")
        
        # Nhận ngưỡng ngày từ đối số dòng lệnh hoặc mặc định là 30 ngày
        days_threshold = 30
        if len(sys.argv) > 1:
            try:
                days_threshold = int(sys.argv[1])
            except ValueError:
                logger.warning(f"Đối số không hợp lệ: {sys.argv[1]}. Sử dụng giá trị mặc định 30 ngày.")
        
        with app.app_context():
            # Kiểm tra và gửi thông báo
            check_expiring_contracts(days_threshold)
            
        logger.info(f"Hoàn thành kiểm tra hợp đồng sắp hết hạn trong {days_threshold} ngày.")
    except Exception as e:
        logger.error(f"Lỗi khi chạy script kiểm tra hợp đồng: {e}")
        sys.exit(1)