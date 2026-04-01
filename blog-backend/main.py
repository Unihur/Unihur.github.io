#本地重启服务器指令：uvicorn main:app --reload

# =========================================================================
# 【服务器后端重启完整指令】
# 如果代码 push 到 GitHub 同步后，后端逻辑未生效，请在服务器终端依次执行：
#
# 1. 进入后端目录：
#    cd /root/blog-backend  (根据你服务器的实际路径修改)
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

from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import shutil
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from models import User
from sqlalchemy import or_

# 引入我们刚才写的数据库模块
from database import engine, Base, get_db
import models
import jwt

# 确保有文件夹存头像
os.makedirs("uploads/avatars", exist_ok=True)
os.makedirs("uploads/images", exist_ok=True)

# 1. 自动创建数据库表 (如果在硬盘里没找到 blog.db，会自动建一个)
models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="UniHur Blog API")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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
    views: int = 0

    class Config:
        orm_mode = True # 允许从 SQLAlchemy 模型读取数据

# 在 Pydantic 模型区下面，新增登录模型
class LoginData(BaseModel):
    username: str
    password: str

# 设定你的管理员账号、密码和用于加密的密钥
# 如果找不到环境变量，就使用后面的默认值（或者你可以让它直接报错，为了安全起见）
ADMIN_USER = os.getenv("ADMIN_USER", "unihur")  # 用户名一般无所谓，可以放明文
ADMIN_PASS = os.getenv("ADMIN_PASS", "default_password_please_change") 
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key_change_me")

# =========== 新增：登录接口 ===========
@app.post("/api/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    if not data.username or not data.password:
        raise HTTPException(status_code=400, detail="账号和密码不能为空")
        
    user = db.query(User).filter(User.username == data.username).first()
    
    if not user:
        # 自动注册：如果是站长直接免审，其他访客设为 False 待审
        is_admin = (data.username == "unihur")
        new_user = User(username=data.username, password=data.password, is_approved=is_admin)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        if not is_admin:
            raise HTTPException(status_code=403, detail="注册成功！请等待管理员审核。")
        user = new_user
    else:
        # 如果已经存在，检查是否审核通过
        if not user.is_approved and user.username != "unihur":
            raise HTTPException(status_code=403, detail="账号正在审核中，请耐心等待。")
        if user.password != data.password:
            raise HTTPException(status_code=401, detail="密码错误")

    token = jwt.encode({"username": user.username, "id": user.id}, SECRET_KEY, algorithm="HS256")
    return {
        "token": token, 
        "username": user.username,
        "avatar": user.avatar,
        "config": {
            "theme_style": user.theme_style,
            "banner_mode": user.banner_mode,
            "is_dark": user.is_dark
        }
    }
    if not data.username or not data.password:
        raise HTTPException(status_code=400, detail="账号和密码不能为空")
        
    user = db.query(User).filter(User.username == data.username).first()
    
    # 【核心逻辑】如果没有该账号，直接创建（即自动注册）
    if not user:
        new_user = User(username=data.username, password=data.password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user = new_user
    else:
        # 如果有该账号，验证密码
        if user.password != data.password:
            raise HTTPException(status_code=401, detail="密码错误")

    # 签发 Token 并返回用户绑定的配置
    token = jwt.encode({"username": user.username, "id": user.id}, SECRET_KEY, algorithm="HS256")
    return {
        "token": token, 
        "username": user.username,
        "avatar": user.avatar,
        "config": {
            "theme_style": user.theme_style,
            "banner_mode": user.banner_mode,
            "is_dark": user.is_dark
        }
    }

# 更新用户设置接口
class UpdateConfigData(BaseModel):
    theme_style: Optional[str] = None
    banner_mode: Optional[str] = None
    new_username: Optional[str] = None
    is_dark: Optional[bool] = None

# ============ 新增：检测账号审核状态接口 ============
@app.get("/api/user/status")
def check_user_approval_status(username: str, db: Session = Depends(get_db)):
    if not username:
        raise HTTPException(status_code=400, detail="账号不能为空")
    
    # 因为管理员 unihur 是特权免审的，直接返回通过
    if username == "unihur":
        return {"status": "approved", "message": "超级管理员账号"}
        
    user = db.query(models.User).filter(models.User.username == username).first()
    
    if not user:
        return {"status": "not_found", "message": "该账号尚未注册，登录将自动提交申请"}
    
    if user.is_approved:
        return {"status": "approved", "message": "账号已通过审核"}
    else:
        return {"status": "pending", "message": "账号正在审核中，请耐心等待"}

@app.post("/api/user/update")
def update_user_info(data: UpdateConfigData, token: str = Header(...), db: Session = Depends(get_db)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    user = db.query(User).filter(User.username == payload["username"]).first()
    
    if data.theme_style: user.theme_style = data.theme_style
    if data.banner_mode: user.banner_mode = data.banner_mode
    if data.is_dark is not None: user.is_dark = data.is_dark
    if data.new_username: 
        # 修改用户名需检查是否冲突
        if db.query(User).filter(User.username == data.new_username).first():
            raise HTTPException(status_code=400, detail="用户名已存在")
        user.username = data.new_username
        
    db.commit()
    return {"message": "更新成功", "new_username": user.username}

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

# ============ 图片上传与图库接口 ============
@app.post("/api/upload/image")
def upload_image(file: UploadFile = File(...), _user: str = Depends(verify_token)): # 👈 这里改了
    file_ext = file.filename.split('.')[-1]
    # 生成一个唯一的文件名（用时间戳防重复）
    file_name = f"{int(datetime.now().timestamp())}_{file.filename}"
    file_path = f"uploads/images/{file_name}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 返回正确的 HTTPS / 域名相对路径
    return {"status": "success", "url": f"/uploads/images/{file_name}"}

@app.get("/api/images")
def get_images(_user: str = Depends(verify_token)): # 👈 这里也改了
    image_dir = "uploads/images"
    if not os.path.exists(image_dir):
        return []
    
    images = []
    # 遍历文件夹下所有的图片
    for filename in os.listdir(image_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            images.append(f"/uploads/images/{filename}")
            
    # 按照文件的修改时间倒序排列（最新的在最前面）
    images.sort(key=lambda x: os.path.getmtime(f"uploads/images/{x.split('/')[-1]}"), reverse=True)
    return images

class SettingUpdate(BaseModel):
    banner_mode: str
    is_dark: bool

class CommentCreate(BaseModel):
    article_slug: str
    content: str
    author: str = "游客"
    reply_to: Optional[str] = None
    parent_id: Optional[int] = None

class CommentAction(BaseModel):
    like_inc: int = 0
    dislike_inc: int = 0

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
            "shares": a.shares,
            "views": a.views
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
            "shares": article.shares,
            "views": article.views 
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

    # 👇 新增：每次有人查看详情，浏览数自动 +1
    if article.views is None:
        article.views = 1
    else:
        article.views += 1
    db.commit() # 保存浏览量

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
            "shares": article.shares,
            "views": article.views  
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
def create_comment(comment: CommentCreate, token: Optional[str] = Header(None), db: Session = Depends(get_db)):
    author_id = None
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            author_id = payload.get("id")
        except: pass 
            
    new_comment = models.Comment(
        article_slug=comment.article_slug,
        content=comment.content,
        author=comment.author,
        author_id=author_id,
        parent_id=comment.parent_id # 新增存入父ID
    )
    db.add(new_comment)
    db.commit()
    return {"status": "success"}

@app.get("/api/comments/{article_slug}")
def get_comments(article_slug: str, token: Optional[str] = Header(None), db: Session = Depends(get_db)):
    # 尝试解析当前请求的用户名，用来判断他是否点赞过
    current_username = None
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_username = payload.get("username")
        except: pass

    comments = db.query(models.Comment).filter(models.Comment.article_slug == article_slug).all()
    
    # 查出当前用户所有的点赞记录
    user_likes = {}
    if current_username:
        likes_records = db.query(models.CommentLike).filter(models.CommentLike.username == current_username).all()
        for r in likes_records:
            user_likes[r.comment_id] = r.action # "like" or "dislike"

    res = []
    for c in comments:
        author_name = c.author
        avatar = ""
        if c.author_id:
            user = db.query(models.User).filter(models.User.id == c.author_id).first()
            if user:
                author_name = user.username
                avatar = user.avatar
                
        res.append({
            "id": c.id, 
            "parent_id": c.parent_id,
            "likes": c.likes or 0,
            "dislikes": c.dislikes or 0,
            "is_pinned": getattr(c, 'is_pinned', False), # 防止旧库没有这列报错
            "author": author_name, 
            "avatar": avatar,
            "content": c.content, 
            "time": c.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            # 返回当前用户对该条评论的状态
            "userAction": user_likes.get(c.id, None) 
        })
    return res


class CommentActionReq(BaseModel):
    action: str # "like" 或 "dislike"

# 👇 新增：评论点赞/点踩接口
@app.post("/api/comments/{comment_id}/action")
def action_comment(comment_id: int, req: CommentActionReq, token: str = Header(...), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("username")
    except:
        raise HTTPException(status_code=401, detail="请先登录")

    c = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="评论不存在")

    # 查当前用户对这条评论的记录
    record = db.query(models.CommentLike).filter(
        models.CommentLike.comment_id == comment_id,
        models.CommentLike.username == username
    ).first()

    action = req.action

    if record:
        if record.action == action:
            # 取消点赞或取消踩
            if action == "like": c.likes -= 1
            else: c.dislikes -= 1
            db.delete(record)
            action_result = None # 代表最终无状态
        else:
            # 切换状态 (比如从踩变赞)
            if action == "like":
                c.dislikes -= 1
                c.likes += 1
            else:
                c.likes -= 1
                c.dislikes += 1
            record.action = action
            action_result = action
    else:
        # 新增
        if action == "like": c.likes += 1
        else: c.dislikes += 1
        new_record = models.CommentLike(comment_id=comment_id, username=username, action=action)
        db.add(new_record)
        action_result = action

    db.commit()
    return {"status": "success", "likes": c.likes, "dislikes": c.dislikes, "userAction": action_result}

@app.post("/api/comments/{comment_id}/pin")
def pin_comment(comment_id: int, token: str = Header(...), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("username") != "unihur":
            raise HTTPException(status_code=403, detail="无权限操作")
    except:
        raise HTTPException(status_code=401, detail="无效令牌")
        
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if comment:
        comment.is_pinned = not comment.is_pinned
        db.commit()
    return {"status": "success", "is_pinned": comment.is_pinned}

# ============ 评论管理（新增删除功能）============
@app.delete("/api/comments/{comment_id}")
def delete_comment(comment_id: int, token: str = Header(...), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        current_user = payload.get("username")
    except:
        raise HTTPException(status_code=401, detail="登录已过期或无效")
        
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
        
    # 核心：允许管理员(unihur) 或者是 评论的发布者删除
    if current_user != "unihur" and current_user != comment.author:
        raise HTTPException(status_code=403, detail="无权限删除此评论")
        
    db.delete(comment)
    
    # 级联删除：如果删的是根评论，把它下面的子回复也一并删掉
    db.query(models.Comment).filter(models.Comment.parent_id == comment_id).delete()
    
    db.commit()
    return {"status": "success", "message": "评论已删除"}

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

# =========== 分类管理 API ===========
class CategoryCreate(BaseModel):
    name: str

@app.get("/api/categories")
def get_categories(db: Session = Depends(get_db)):
    cats = db.query(models.Category).all()
    result = []
    for c in cats:
        # 统计该分类下有几篇文章
        count = db.query(models.Article).filter(models.Article.category == c.name).count()
        result.append({"name": c.name, "count": count})
    return result

@app.post("/api/categories")
def add_category(cat: CategoryCreate, db: Session = Depends(get_db), _token: str = Depends(verify_token)):
    if db.query(models.Category).filter(models.Category.name == cat.name).first():
        raise HTTPException(status_code=400, detail="分类已存在")
    new_cat = models.Category(name=cat.name)
    db.add(new_cat)
    db.commit()
    return {"status": "success"}

@app.put("/api/categories/{old_name}")
def rename_category(old_name: str, cat: CategoryCreate, db: Session = Depends(get_db), _token: str = Depends(verify_token)):
    db_cat = db.query(models.Category).filter(models.Category.name == old_name).first()
    if not db_cat:
        raise HTTPException(404, detail="分类不存在")
    db_cat.name = cat.name
    # 把之前所有属于旧分类的文章，全部更新为新分类名
    db.query(models.Article).filter(models.Article.category == old_name).update({"category": cat.name})
    db.commit()
    return {"status": "success"}

@app.delete("/api/categories/{name}")
def delete_category(name: str, db: Session = Depends(get_db), _token: str = Depends(verify_token)):
    db_cat = db.query(models.Category).filter(models.Category.name == name).first()
    if db_cat:
        db.delete(db_cat)
        # 将被删除分类下的文章，分类置空
        db.query(models.Article).filter(models.Article.category == name).update({"category": None})
        db.commit()
    return {"status": "success"}

# ============ 3. 新增上传头像接口 ============
@app.post("/api/user/avatar")
def upload_avatar(file: UploadFile = File(...), token: str = Header(...), db: Session = Depends(get_db)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    user = db.query(models.User).filter(models.User.username == payload["username"]).first()
    
    file_ext = file.filename.split('.')[-1]
    file_name = f"{user.id}_{int(datetime.now().timestamp())}.{file_ext}"
    file_path = f"uploads/avatars/{file_name}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    user.avatar = f"https://unihur.xyz/{file_path}"
    db.commit()
    return {"status": "success", "avatar": user.avatar}

# ============ 4. 新增访客(用户)管理接口 ============
@app.get("/api/admin/visitors")
def get_visitors(token: str = Header(...), db: Session = Depends(get_db)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    if payload["username"] != "unihur":
        raise HTTPException(status_code=403, detail="无权限")
        
    users = db.query(models.User).filter(models.User.username != "unihur").all()
    # 返回列表中带上 is_approved 状态
    return [{"id": u.id, "username": u.username, "avatar": u.avatar, "is_approved": u.is_approved} for u in users]

@app.put("/api/admin/visitors/{user_id}/approve")
def approve_visitor(user_id: int, token: str = Header(...), db: Session = Depends(get_db)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    if payload["username"] != "unihur":
        raise HTTPException(status_code=403, detail="无权限")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.is_approved = True
        db.commit()
    return {"status": "success"}

@app.delete("/api/admin/visitors/{user_id}")
def delete_visitor(user_id: int, token: str = Header(...), db: Session = Depends(get_db)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    if payload["username"] != "unihur":
        raise HTTPException(status_code=403, detail="无权限")
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        # 👇 新增：删除物理磁盘上的头像文件
        if user.avatar:
            try:
                # 将 "https://unihur.xyz/uploads/avatars/xxx.jpg" 截取为本地相对路径
                file_path = user.avatar.split("unihur.xyz/")[-1]
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print("删除头像文件失败:", e)

        db.delete(user)
        db.commit()
    return {"status": "success"}

# ============ 新增：全局访客统计接口 ============
@app.get("/api/site/visitor-count")
def get_visitor_count(db: Session = Depends(get_db)):
    stat = db.query(models.SiteStat).first()
    # 如果还没有记录，初始化为 0
    if not stat:
        stat = models.SiteStat(visitor_count=0)
        db.add(stat)
        db.commit()
        db.refresh(stat)
    return {"visitor_count": stat.visitor_count}

@app.post("/api/site/visitor-count/increment")
def increment_visitor_count(db: Session = Depends(get_db)):
    stat = db.query(models.SiteStat).first()
    if not stat:
        stat = models.SiteStat(visitor_count=0)
        db.add(stat)
        db.commit()
        db.refresh(stat)
    
    # 访客数 + 1
    stat.visitor_count += 1
    db.commit()
    return {"visitor_count": stat.visitor_count}

# ============ 新增：校验账号存活状态 ============
@app.get("/api/user/me")
def check_user_status(token: str = Header(...), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = db.query(models.User).filter(models.User.id == payload.get("id")).first()
        if not user:
            raise HTTPException(status_code=401, detail="账号已被注销")
        
        # 👇 修改返回数据，把 config 带上
        return {
            "status": "ok", 
            "config": {
                "theme_style": user.theme_style,
                "banner_mode": user.banner_mode,
                "is_dark": user.is_dark
            }
        }
    except:
        raise HTTPException(status_code=401, detail="登录失效")

