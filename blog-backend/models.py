from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from datetime import datetime
from database import Base

class Article(Base):
    __tablename__ = "articles" # 这是数据库里实际的表名

    # 每一列的定义：名字、类型、是否主键/索引
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True, nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    content = Column(Text, nullable=False)
    intro = Column(String(500), nullable=True)
    
    # 标签和分类暂时存为 JSON 字符串和普通字符串（后期如果需要复杂查询，可以拆分成单独的表）
    tags = Column(JSON, default=[]) 
    category = Column(String(100), nullable=True)
    
    cover = Column(String(500), nullable=True)
    is_hidden = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    
    # 记录时间
    publish_time = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 👇 新增这一行：记录点赞数，默认值为 0
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)

class SiteSetting(Base):
    __tablename__ = "site_settings"
    id = Column(Integer, primary_key=True, index=True)
    banner_mode = Column(String(50), default="banner")
    is_dark = Column(Boolean, default=False)

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    article_slug = Column(String(255), index=True) # 关联文章
    author = Column(String(50), default="游客")
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)