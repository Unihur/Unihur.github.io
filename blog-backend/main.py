#重启服务器指令：uvicorn main:app --reload
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# 引入我们刚才写的数据库模块
from database import engine, Base, get_db
import models

# 1. 自动创建数据库表 (如果在硬盘里没找到 blog.db，会自动建一个)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="UniHur Blog API")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Pydantic 模型 (前端数据校验) =====
class ArticleCreate(BaseModel):
    title: str
    slug: str
    content: str
    intro: Optional[str] = None
    tags: List[str] = []
    category: Optional[str] = None
    publishTime: datetime
    isHidden: bool = False
    isPinned: bool = False
    cover: Optional[str] = None

class ArticleResponse(ArticleCreate):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True # 允许从 SQLAlchemy 模型读取数据

# ===== 路由 API =====

@app.get("/")
def read_root():
    return {"message": "欢迎来到 UniHur 博客后端 API!"}

# 【新增】发布文章 (存入数据库)
@app.post("/api/articles", response_model=dict)
def create_article(article: ArticleCreate, db: Session = Depends(get_db)):
    # 检查 slug 是否已存在，防止 URL 重复
    db_article = db.query(models.Article).filter(models.Article.slug == article.slug).first()
    if db_article:
        raise HTTPException(status_code=400, detail="Slug 已经被使用了，请换一个!")

    # 把前端传来的 Pydantic 模型转换为 SQLAlchemy 的数据库对象
    new_article = models.Article(
        title=article.title,
        slug=article.slug,
        content=article.content,
        intro=article.intro,
        tags=article.tags,
        category=article.category,
        cover=article.cover,
        is_hidden=article.isHidden, # 注意 Python 用下划线命名
        is_pinned=article.isPinned,
        publish_time=article.publishTime
    )
    
    # 存入数据库的三步曲：添加、提交、刷新
    db.add(new_article)
    db.commit()
    db.refresh(new_article)
    
    return {
        "status": "success", 
        "message": "文章已永久保存至数据库!",
        "article_id": new_article.id
    }

# 【新增】获取文章列表 (供首页调用)
@app.get("/api/articles", response_model=List[ArticleResponse])
def get_articles(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    # 从数据库里拿，跳过隐藏文章，按时间倒序
    articles = db.query(models.Article).filter(models.Article.is_hidden == False).order_by(models.Article.publish_time.desc()).offset(skip).limit(limit).all()
    
    # 因为 Pydantic 变量名和数据库驼峰名有点差异，我们需要简单转换一下再返回��前端
    result = []
    for a in articles:
        result.append({
            "id": a.id,
            "title": a.title,
            "slug": a.slug,
            "content": a.content,
            "intro": a.intro,
            "tags": a.tags,
            "category": a.category,
            "publishTime": a.publish_time,
            "isHidden": a.is_hidden,
            "isPinned": a.is_pinned,
            "cover": a.cover,
            "created_at": a.created_at
        })
    return result


    # 查找当前文章
    article = db.query(models.Article).filter(models.Article.slug == slug).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
        
    # 查找上一篇 (发布时间比当前文章早的第一篇)
    prev_article = db.query(models.Article).filter(
        models.Article.publish_time < article.publish_time, 
        models.Article.is_hidden == False
    ).order_by(models.Article.publish_time.desc()).first()
    
    # 查找下一篇 (发布时间比当前文章晚的第一篇)
    next_article = db.query(models.Article).filter(
        models.Article.publish_time > article.publish_time, 
        models.Article.is_hidden == False
    ).order_by(models.Article.publish_time.asc()).first()
    
    return {
        "article": {
            "id": article.id,
            "title": article.title,
            "slug": article.slug,
            "content": article.content,
            "tags": article.tags,
            "category": article.category,
            "publishTime": article.publish_time,
            "cover": article.cover,
            "likes": article.likes
        },
        "prev": {"title": prev_article.title, "slug": prev_article.slug} if prev_article else None,
        "next": {"title": next_article.title, "slug": next_article.slug} if next_article else None
    }

    # 【新增】点赞接口

# 【只保留这一个：获取单篇文章详情，包含上下篇和点赞数】
@app.get("/api/articles/{slug}")
def get_article(slug: str, db: Session = Depends(get_db)):
    # 查找当前文章
    article = db.query(models.Article).filter(models.Article.slug == slug).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
        
    # 查找上一篇 (发布时间比当前文章早的第一篇)
    prev_article = db.query(models.Article).filter(
        models.Article.publish_time < article.publish_time, 
        models.Article.is_hidden == False
    ).order_by(models.Article.publish_time.desc()).first()
    
    # 查找下一篇 (发布时间比当前文章晚的第一篇)
    next_article = db.query(models.Article).filter(
        models.Article.publish_time > article.publish_time, 
        models.Article.is_hidden == False
    ).order_by(models.Article.publish_time.asc()).first()
    
    return {
        "article": {
            "id": article.id,
            "title": article.title,
            "slug": article.slug,
            "content": article.content,
            "tags": article.tags,
            "category": article.category,
            "publishTime": article.publish_time,
            "cover": article.cover,  # 👈 这里的逗号加好了！
            "likes": article.likes   # 👈 现在前端能顺利拿到点赞数了
        },
        "prev": {"title": prev_article.title, "slug": prev_article.slug} if prev_article else None,
        "next": {"title": next_article.title, "slug": next_article.slug} if next_article else None
    }

@app.post("/api/articles/{slug}/like")
def like_article(slug: str, db: Session = Depends(get_db)):
    article = db.query(models.Article).filter(models.Article.slug == slug).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    # 数据库点赞数 +1
    if article.likes is None:
        article.likes = 1
    else:
        article.likes += 1
        
    db.commit()
    return {"status": "success", "likes": article.likes}