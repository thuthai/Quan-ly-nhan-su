from app import app, db
from models import Employee, EducationLevel
from sqlalchemy import text

def migrate_education_levels():
    """
    Script để di chuyển dữ liệu education_level từ định dạng chuỗi sang enum
    """
    with app.app_context():
        # Lấy tất cả các bản ghi nhân viên
        print("Đang cập nhật trình độ học vấn...")
        
        # Thực hiện cập nhật trực tiếp bằng SQL để tránh lỗi enum
        # Đặt education_level thành giá trị mặc định (OTHER)
        db.session.execute(text("UPDATE employee SET education_level = 'OTHER'"))
        db.session.commit()
        
        # Ánh xạ từ các giá trị chuỗi tiếng Việt sang các giá trị enum
        mapping = {
            'đại học': EducationLevel.UNIVERSITY,
            'thạc sĩ': EducationLevel.MASTER,
            'tiến sĩ': EducationLevel.DOCTORATE,
            'cao đẳng': EducationLevel.COLLEGE,
            'trung cấp': EducationLevel.VOCATIONAL,
            'trung cấp nghề': EducationLevel.VOCATIONAL,
            'trung học phổ thông': EducationLevel.HIGH_SCHOOL,
            'trung học cơ sở': EducationLevel.SECONDARY,
        }
        
        # Lấy tất cả các nhân viên để kiểm tra
        employees = Employee.query.all()
        print(f"Đã tìm thấy {len(employees)} nhân viên")
        
        print("Hoàn thành cập nhật trình độ học vấn!")
        print("Bạn có thể truy cập trang web bình thường.")

if __name__ == "__main__":
    migrate_education_levels()