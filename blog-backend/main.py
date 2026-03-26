#本地重启服务器指令：uvicorn main:app --reload

# =========================================================================
# 【服务器后端重启完整指令】
# 如果代码 push 到 GitHub 同步后，后端逻辑未生效，请在服务器终端依次执行：
#
# 1. 进入后端目录：
#    cd ~/blog-backend  (根据你服务器的实际路径修改)
#
# 2. 杀掉旧的 Python 进程：
#    pkill -f uvicorn
#
# 3. 激活虚拟环境 (名字为 .venv)：
#    source .venv/bin/activate
#
# 4. (可选) 如果修改了数据库字段且不想报错，最简单就是删掉旧数据库重建：
#    rm blog.db  (注意：此操作会清空之前的测试数据！)
#
# 5. 在后台重新启动 FastAPI：
#    nohup uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
#
# 6. 验证是否启动成功 (看有没有 running 提示)：
#    cat backend.log
# =========================================================================

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# 引入我们刚才写的数据库模块
from database import engine, Base, get_db
import models
import jwt

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
    likes: int = 0
    shares: int = 0

    class Config:
        orm_mode = True # 允许从 SQLAlchemy 模型读取数据

# 在 Pydantic 模型区下面，新增登录模型
class LoginData(BaseModel):
    username: str
    password: str

# 设定你的管理员账号、密码和用于加密的密钥
ADMIN_USER = "unihur"
ADMIN_PASS = "Zyh176626149" # 换成你想要的复杂密码
SECRET_KEY = "unihur_super_admin_key" # 随便写一串复杂的英文字符

# =========== 新增：登录接口 ===========
@app.post("/api/login")
def login(data: LoginData):
    if data.username == ADMIN_USER and data.password == ADMIN_PASS:
        # 签发令牌，这就像给前端发了一张“门禁卡”
        token = jwt.encode({"user": data.username}, SECRET_KEY, algorithm="HS256")
        return {"status": "success", "token": token}
    else:
        raise HTTPException(status_code=401, detail="账号或密码错误")

# =========== 新增：检查令牌的依赖函数 ===========
def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录或令牌缺失")
    token = authorization.split(" ")[1]
    try:
        jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="令牌已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的令牌")

# ===== 路由 API =====

class SettingUpdate(BaseModel):
    banner_mode: str
    is_dark: bool

class CommentCreate(BaseModel):
    article_slug: str
    content: str
    author: str = "游客"

@app.get("/api/settings")
def get_settings(db: Session = Depends(get_db)):
    setting = db.query(models.SiteSetting).first()
    if not setting:
        setting = models.SiteSetting(banner_mode="banner", is_dark=False)
        db.add(setting)
        db.commit()
    return {"banner_mode": setting.banner_mode, "is_dark": setting.is_dark}

@app.post("/api/settings")
def update_settings(setting_data: SettingUpdate, db: Session = Depends(get_db)):
    setting = db.query(models.SiteSetting).first()
    if not setting:
        setting = models.SiteSetting()
        db.add(setting)
    setting.banner_mode = setting_data.banner_mode
    setting.is_dark = setting_data.is_dark
    db.commit()
    return {"status": "success"}

@app.get("/")
def read_root():
    return {"message": "欢迎来到 UniHur 博客后端 API!"}

# 【新增】发布文章 (存入数据库)
@app.post("/api/articles", response_model=dict)
def create_article(article: ArticleCreate, db: Session = Depends(get_db), _token: str = Depends(verify_token)):
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

# 【新增】更新已有文章
@app.put("/api/articles/{slug}", response_model=dict)
def update_article(slug: str, article: ArticleCreate, db: Session = Depends(get_db), _token: str = Depends(verify_token)):
    db_article = db.query(models.Article).filter(models.Article.slug == slug).first()
    if not db_article:
        raise HTTPException(status_code=404, detail="文章不存在，无法更新！")

    # 如果改了 URL 别名，且新别名被别的文章占用了，要报错
    if article.slug != slug:
        conflict = db.query(models.Article).filter(models.Article.slug == article.slug).first()
        if conflict:
            raise HTTPException(status_code=400, detail="新 Slug 已经被使用了，请换一个!")

    # 把传过来的新数据覆盖到数据库旧对象上
    db_article.title = article.title
    db_article.slug = article.slug
    db_article.content = article.content
    db_article.intro = article.intro
    db_article.tags = article.tags
    db_article.category = article.category
    db_article.cover = article.cover
    db_article.is_hidden = article.isHidden
    db_article.is_pinned = article.isPinned
    db_article.publish_time = article.publishTime

    db.commit()
    return {
        "status": "success", 
        "message": "文章已成功更新！"
    }

# 【新增】获取文章列表 (供首页调用)
@app.get("/api/articles", response_model=List[ArticleResponse])
def get_articles(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    # 👇 1. 修复排序逻辑：优先按照置顶(is_pinned)降序排列，然后再按时间倒序
    articles = db.query(models.Article).filter(models.Article.is_hidden == False).order_by(models.Article.is_pinned.desc(), models.Article.publish_time.desc()).offset(skip).limit(limit).all()
    
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
            "created_at": a.created_at,
            "likes": a.likes,
            "shares": a.shares  
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
            "likes": article.likes,
            "shares": article.shares
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
            "intro": article.intro,            # <-- 新增：返回简介
            "isHidden": article.is_hidden,     # <-- 新增：返回隐藏状态
            "isPinned": article.is_pinned,     # <-- 新增：返回置顶状态
            "tags": article.tags,
            "category": article.category,
            "publishTime": article.publish_time,
            "cover": article.cover,  
            "likes": article.likes,   
            "shares": article.shares  
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

@app.post("/api/articles/{slug}/share")
def share_article(slug: str, db: Session = Depends(get_db)):
    article = db.query(models.Article).filter(models.Article.slug == slug).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    if article.shares is None:
        article.shares = 1
    else:
        article.shares += 1
        
    db.commit()
    return {"status": "success", "shares": article.shares}

@app.post("/api/comments")
def create_comment(comment: CommentCreate, db: Session = Depends(get_db)):
    new_comment = models.Comment(
        article_slug=comment.article_slug,
        content=comment.content,
        author=comment.author
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return {"status": "success"}

@app.get("/api/comments/{article_slug}")
def get_comments(article_slug: str, db: Session = Depends(get_db)):
    comments = db.query(models.Comment).filter(models.Comment.article_slug == article_slug).order_by(models.Comment.created_at.desc()).all()
    return [{"id": c.id, "author": c.author, "content": c.content, "time": c.created_at.strftime("%Y-%m-%d %H:%M:%S")} for c in comments]

# 【新增】删除已有文章
@app.delete("/api/articles/{slug}", response_model=dict)
def delete_article(slug: str, db: Session = Depends(get_db), _token: str = Depends(verify_token)):
    # 1. 在数据库里找这篇文章
    db_article = db.query(models.Article).filter(models.Article.slug == slug).first()
    
    # 2. 如果没找到，报错
    if not db_article:
        raise HTTPException(status_code=404, detail="文章不存在，无法删除！")
    
    # 3. 找到的话就删除它，并保存更改
    db.delete(db_article)
    db.commit()
    
    return {"status": "success", "message": "文章已成功删除"}