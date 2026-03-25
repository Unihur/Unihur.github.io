from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. 数据库 URL (使用本地 SQLite 文件 blog.db)
SQLALCHEMY_DATABASE_URL = "sqlite:///./blog.db"

# 2. 创建数据库引擎 (connect_args 是为了解决 SQLite 线程报错的小细节)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. 创建数据库会话 (Session)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. 创建基础模型类 (我们之后的表结构都要继承它)
Base = declarative_base()

# 5. 依赖注入函数：每次请求时获取一个数据库连接，用完自动关掉
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()