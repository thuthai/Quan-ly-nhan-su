from app import app, db
from models import User, UserRole
from flask import Flask

# Tạo context ứng dụng
with app.app_context():
    # Kiểm tra xem có user admin nào chưa
    admin_exists = User.query.filter_by(role=UserRole.ADMIN).first()
    
    if not admin_exists:
        # Tạo người dùng admin
        admin = User(
            username='admin',
            email='admin@example.com',
            role=UserRole.ADMIN
        )
        admin.set_password('admin123')
        
        # Thêm vào database
        db.session.add(admin)
        db.session.commit()
        
        print('Đã tạo tài khoản admin:')
        print('Username: admin')
        print('Password: admin123')
    else:
        print('Đã tồn tại tài khoản admin trong hệ thống')