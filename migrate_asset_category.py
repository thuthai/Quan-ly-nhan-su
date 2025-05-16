"""
Script để cập nhật bảng assets, thêm cột category_id tham chiếu đến bảng asset_categories
"""
from app import db
from models import Asset, AssetCategoryModel
from sqlalchemy import text


def alter_table():
    """Thêm cột category_id vào bảng assets"""
    with db.engine.connect() as conn:
        # Kiểm tra xem cột đã tồn tại chưa
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='assets' AND column_name='category_id'
        """))
        
        # Nếu cột chưa tồn tại, thêm vào
        if result.rowcount == 0:
            conn.execute(text("""
                ALTER TABLE assets 
                ADD COLUMN category_id INTEGER,
                ADD CONSTRAINT fk_asset_category 
                FOREIGN KEY (category_id) REFERENCES asset_categories(id)
            """))
            conn.commit()
            print("Đã thêm cột category_id vào bảng assets")
        else:
            print("Cột category_id đã tồn tại")


def migrate_data():
    """Chuyển đổi dữ liệu từ category (enum) sang category_id (FK)"""
    # Lấy tất cả tài sản chưa có category_id
    assets = Asset.query.filter_by(category_id=None).all()
    
    if not assets:
        print("Không có tài sản cần cập nhật")
        return
    
    # Lấy danh sách các danh mục trong database
    categories = AssetCategoryModel.query.all()
    category_map = {cat.name: cat.id for cat in categories}
    
    # Tạo các danh mục cần thiết nếu chưa có
    enum_map = {
        'COMPUTER': 'Máy tính',
        'LAPTOP': 'Laptop',
        'PHONE': 'Điện thoại',
        'FURNITURE': 'Nội thất',
        'OFFICE': 'Thiết bị văn phòng',
        'VEHICLE': 'Phương tiện',
        'OTHER': 'Khác'
    }
    
    for enum_name, display_name in enum_map.items():
        if display_name not in category_map:
            # Tạo danh mục mới
            new_category = AssetCategoryModel(
                name=display_name,
                description=f"Danh mục {display_name}",
                is_active=True
            )
            db.session.add(new_category)
            db.session.commit()
            category_map[display_name] = new_category.id
            print(f"Đã tạo danh mục {display_name}")
    
    # Cập nhật category_id cho tất cả tài sản
    for asset in assets:
        if asset.category and asset.category.name in enum_map:
            category_name = enum_map[asset.category.name]
            if category_name in category_map:
                asset.category_id = category_map[category_name]
                print(f"Cập nhật tài sản {asset.asset_code} sang danh mục {category_name}")
    
    db.session.commit()
    print(f"Đã cập nhật {len(assets)} tài sản")


if __name__ == "__main__":
    from app import app
    with app.app_context():
        alter_table()
        migrate_data()
        print("Hoàn thành migration")