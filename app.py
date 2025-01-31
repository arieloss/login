from fastapi import FastAPI, HTTPException, Form, Depends, Request, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Boolean, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from datetime import datetime
from enum import Enum
# Gestionnaire de WebSocket
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set

import os
import uuid

# Configuration de la base de données
DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modèle Utilisateur
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    email = Column(String, unique=True, nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    profile_image = Column(String, nullable=True)  # Chemin vers l'image de profil

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    image_url = Column(String, nullable=True)
    document_url = Column(String, nullable=True)
    author_id = Column(Integer)
    created_at = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String)
    content = Column(String)
    created_at = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))



# Ajout de nouveaux modèles dans le fichier Python
class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    created_by = Column(Integer)
    created_at = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

class GroupMember(Base):
    __tablename__ = "group_members"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer)
    user_id = Column(Integer)
    role = Column(String, default="member")  # admin, member, etc.

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    STICKER = "sticker"
    EMOJI = "emoji"
    FILE = "file"
    AUDIO = "audio"

class DirectMessage(Base):
    __tablename__ = "direct_messages"
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer)
    receiver_id = Column(Integer)
    content = Column(String)
    message_type = Column(String, default=MessageType.TEXT)
    file_path = Column(String, nullable=True)
    created_at = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        print(f"Connexion WebSocket ajoutée pour l'utilisateur {user_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if len(self.active_connections[user_id]) == 0:
                del self.active_connections[user_id]
            print(f"WebSocket déconnecté pour l'utilisateur {user_id}")
    
    async def send_personal_message(self, user_id: int, message: dict):
        print(f"Tentative d'envoi de message à l'utilisateur {user_id}")
        print(f"Connexions actives : {self.active_connections}")
        
        if user_id in self.active_connections:
            print(f"Nombre de connexions pour {user_id}: {len(self.active_connections[user_id])}")
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_json(message)
                    print(f"Message envoyé à l'utilisateur {user_id}")
                except Exception as e:
                    print(f"Erreur lors de l'envoi du message : {e}")
        else:
            print(f"Aucune connexion active pour l'utilisateur {user_id}")

# Initialisation du gestionnaire WebSocket
websocket_manager = WebSocketManager()

# Créer les tables
Base.metadata.create_all(bind=engine)

# Configuration de l'application
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

# Gestion des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Dépendance pour obtenir la session de base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Création de l'admin par défaut si non existant
def create_default_admin(db: Session):
    admin_username = "admin"
    admin_password = "admin123"
    admin_email = "admin@example.com"
    
    existing_admin = db.query(User).filter(User.username == admin_username).first()
    if not existing_admin:
        hashed_password = pwd_context.hash(admin_password)
        admin_user = User(
            username=admin_username, 
            password=hashed_password, 
            email=admin_email, 
            is_admin=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        

# Middleware pour gérer la session
@app.middleware("http")
async def add_session_to_request(request: Request, call_next):
    # Vous devriez implémenter un système de gestion de session plus sécurisé
    session = request.cookies.get("session")
    request.state.username = session
    response = await call_next(request)
    return response

# Vérification de la connexion
def get_current_user(request: Request = None, db: Session = Depends(get_db)):
    # Adaptez la logique pour gérer les cas où request pourrait être None
    username = request.state.username if request else None
    
    if not username:
        raise HTTPException(status_code=401, detail="Vous devez être connecté")
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
    
    return user

# Page d'accueil (Connexion)
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Route de connexion
@app.post("/login")
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    
    if user and pwd_context.verify(password, user.password):
        # Créer une réponse avec cookie de session
        response = RedirectResponse(
            url="/admin-dashboard" if user.is_admin else "/user-dashboard", 
            status_code=303
        )
        response.set_cookie(key="session", value=username, httponly=True)
        return response
    
    return templates.TemplateResponse("login.html", {
        "request": Request, 
        "error": "Nom d'utilisateur ou mot de passe incorrect"
    })
    
    
@app.get("/logout")
def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("session")
    return response

# Tableau de bord administrateur
@app.get("/admin-dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).all()
    posts = db.query(Post).all()
    messages = db.query(Message).all()
    total_users = len(users)
    total_posts = len(posts)
    recent_posts = len(posts[-5:])  # Affiche les 5 derniers posts
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request, 
        "users": users, 
        "posts": posts,
        "messages": messages,
        "total_users": total_users,
        "total_posts": total_posts,
        "recent_posts": recent_posts
    })

# Route pour publier du contenu (texte, image, document)
@app.post("/publish")
async def publish_content(
    text: str = Form(None), 
    image: UploadFile = File(None), 
    document: UploadFile = File(None), 
    db: Session = Depends(get_db)
):
    os.makedirs("uploads/images", exist_ok=True)
    os.makedirs("uploads/documents", exist_ok=True)

    image_url = None
    document_url = None

    # Gérer l'image
    if image:
        image_filename = f"uploads/images/{image.filename}"
        with open(image_filename, "wb") as image_file:
            image_file.write(await image.read())
        image_url = image_filename

    # Gérer le document
    if document:
        document_filename = f"uploads/documents/{document.filename}"
        with open(document_filename, "wb") as document_file:
            document_file.write(await document.read())
        document_url = document_filename

    # Ajouter la publication
    new_post = Post(
        title="Nouvelle publication", 
        content=text, 
        image_url=image_url, 
        document_url=document_url, 
        author_id=1
    )
    db.add(new_post)
    db.commit()

    return {"message": "Publication effectuée avec succès"}

def get_websocket_manager() -> WebSocketManager:
    return websocket_manager


# Route pour envoyer un message
@app.post("/send-dm")
async def send_direct_message(
    receiver_id: int = Form(...),
    message: str = Form(None),
    message_type: MessageType = Form(MessageType.TEXT),
    file: UploadFile = File(None),
    emoji: str = Form(None),
    sticker: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    websocket_manager: WebSocketManager = Depends(get_websocket_manager)
):
    # Vérifier si le destinataire existe
    receiver = db.query(User).filter(User.id == receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Gestion du fichier
    file_path = None
    if file:
        os.makedirs("uploads/dm_files", exist_ok=True)
        filename = f"uploads/dm_files/{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
        
        with open(filename, "wb") as buffer:
            buffer.write(await file.read())
        
        file_path = filename
        
        # Déterminer le type de message en fonction du type de fichier
        if file.content_type.startswith("image"):
            message_type = MessageType.IMAGE
        elif file.content_type.startswith("video"):
            message_type = MessageType.VIDEO
    
    # Gestion des emojis
    if emoji:
        message_type = MessageType.EMOJI
        message = emoji
    
    # Gestion des stickers
    if sticker:
        message_type = MessageType.STICKER
        message = sticker
    
    # Créer le message
    new_message = DirectMessage(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=message or "",
        message_type=message_type,
        file_path=file_path
    )
    
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    
    # Préparer les données du message pour l'envoi
    message_data = {
        "id": new_message.id,
        "sender_id": new_message.sender_id,
        "content": new_message.content,
        "message_type": new_message.message_type,
        "file_path": new_message.file_path or "",
        "created_at": new_message.created_at
    }
    
    # Envoyer le message via WebSocket
    await websocket_manager.send_personal_message(receiver_id, message_data)
    
    return {"message": "Message envoyé avec succès", "message_data": message_data}


# Route pour ajouter un utilisateur (admin only)
@app.post("/add-user")
def add_user(
    username: str = Form(...), 
    password: str = Form(...), 
    email: str = Form(...), 
    is_admin: bool = Form(False), 
    db: Session = Depends(get_db)
):
    # Vérifier si l'utilisateur existe déjà
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        return {"error": "Nom d'utilisateur ou email déjà existant"}
    
    # Hacher le mot de passe
    hashed_password = pwd_context.hash(password)
    
    # Créer un nouvel utilisateur
    new_user = User(
        username=username, 
        password=hashed_password, 
        email=email, 
        is_admin=is_admin
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return RedirectResponse(url="/admin-dashboard", status_code=303)

# Tableau de bord utilisateur
@app.get("/user-dashboard", response_class=HTMLResponse)
def user_dashboard(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("user_dashboard.html", {
        "request": request, 
        "user": current_user
    })
    
@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("profile.html", {
        "request": request, 
        "user": current_user
    })
    
    
    
@app.post("/change-password")
def change_password(
    old_password: str = Form(...), 
    new_password: str = Form(...), 
    confirm_password: str = Form(...),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Vérifier l'ancien mot de passe
    if not pwd_context.verify(old_password, current_user.password):
        return templates.TemplateResponse("profile.html", {
            "request": request, 
            "user": current_user,
            "password_error": "L'ancien mot de passe est incorrect"
        })
    
    # Vérifier que les nouveaux mots de passe correspondent
    if new_password != confirm_password:
        return templates.TemplateResponse("profile.html", {
            "request": request, 
            "user": current_user,
            "password_error": "Les nouveaux mots de passe ne correspondent pas"
        })
    
    # Mettre à jour le mot de passe
    current_user.password = pwd_context.hash(new_password)
    db.commit()
    
    return templates.TemplateResponse("profile.html", {
        "request": request, 
        "user": current_user,
        "password_success": "Mot de passe modifié avec succès"
    })

@app.post("/upload-profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Créer le dossier uploads s'il n'existe pas
    os.makedirs("uploads", exist_ok=True)
    
    # Générer un nom de fichier unique
    filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
    file_path = os.path.join("uploads", filename)
    
    # Sauvegarder le fichier
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    # Mettre à jour le chemin de l'image de profil
    current_user.profile_image = filename
    db.commit()
    
    return RedirectResponse(url="/profile", status_code=303)




# Route pour afficher tous les messages
@app.get("/messages", response_class=HTMLResponse)
def view_messages(request: Request, db: Session = Depends(get_db)):
    messages = db.query(Message).order_by(Message.created_at.desc()).all()
    return templates.TemplateResponse("messages.html", {
        "request": request, 
        "messages": messages
    })

# Route pour afficher toutes les publications
@app.get("/publications", response_class=HTMLResponse)
def view_publications(request: Request, db: Session = Depends(get_db)):
    posts = db.query(Post).order_by(Post.created_at.desc()).all()
    return templates.TemplateResponse("publications.html", {
        "request": request, 
        "posts": posts
    })


# Route pour créer un groupe
@app.post("/create-group")
def create_group(
    name: str = Form(...), 
    description: str = Form(None), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Vérifier si le groupe existe déjà
    existing_group = db.query(Group).filter(Group.name == name).first()
    if existing_group:
        raise HTTPException(status_code=400, detail="Un groupe avec ce nom existe déjà")
    
    new_group = Group(
        name=name, 
        description=description,
        created_by=current_user.id
    )
    
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    
    # Ajouter l'utilisateur comme membre admin du groupe
    group_member = GroupMember(
        group_id=new_group.id,
        user_id=current_user.id,
        role="admin"
    )
    
    db.add(group_member)
    db.commit()
    
    return RedirectResponse(url="/groups", status_code=303)

@app.get("/search-users")
def search_users(
    query: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Rechercher des utilisateurs qui ne sont pas l'utilisateur connecté
    users = db.query(User).filter(
        (User.username.contains(query)) | (User.email.contains(query)),
        User.id != current_user.id  # Exclure l'utilisateur connecté
    ).all()
    
    # Transformer les utilisateurs en dictionnaires pour la sérialisation JSON
    user_list = [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "profile_image": user.profile_image or "/static/default-avatar.png"
        } for user in users
    ]
    
    return {"users": user_list}

# Route pour envoyer un message privé
@app.post("/send-dm")
async def send_direct_message(
    receiver_id: int = Form(...),
    message: str = Form(None),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Vérifier si le destinataire existe
    receiver = db.query(User).filter(User.id == receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Gestion du fichier (si image ou vidéo)
    file_path = None
    message_type = "text"
    
    if file:
        os.makedirs("uploads/dm_files", exist_ok=True)
        filename = f"uploads/dm_files/{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
        
        with open(filename, "wb") as buffer:
            buffer.write(await file.read())
        
        file_path = filename
        message_type = "image" if file.content_type.startswith("image") else "video"
    
    # Créer le message
    new_message = DirectMessage(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=message,
        message_type=message_type,
        file_path=file_path
    )
    
    db.add(new_message)
    db.commit()
    
    return {"message": "Message envoyé avec succès"}

# Route pour supprimer un message
@app.delete("/delete-message/{message_id}")
def delete_message(
    message_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Rechercher le message
    message = db.query(Message).filter(Message.id == message_id).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message non trouvé")
    
    # Vérifier les permissions de suppression
    if current_user.is_admin or message.sender == current_user.username:
        db.delete(message)
        db.commit()
        return {"message": "Message supprimé avec succès"}
    
    raise HTTPException(status_code=403, detail="Vous n'avez pas la permission de supprimer ce message")

@app.get("/direct-messages", response_class=HTMLResponse)
def direct_messages(
    request: Request, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Récupérer la liste des contacts (utilisateurs avec lesquels l'utilisateur a déjà communiqué)
    contacts = db.query(User).join(
        DirectMessage, 
        ((DirectMessage.sender_id == User.id) | (DirectMessage.receiver_id == User.id))
    ).filter(
        (DirectMessage.sender_id == current_user.id) | (DirectMessage.receiver_id == current_user.id)
    ).distinct().all()
    
    return templates.TemplateResponse("direct_messages.html", {
        "request": request, 
        "current_user": current_user,
        "contacts": contacts,
        "recipient": None,
        "messages": []
    })

@app.get("/dm/{user_id}", response_class=HTMLResponse)
def direct_message_with_user(
    request: Request, 
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Récupérer les informations de l'utilisateur destinataire
    recipient = db.query(User).filter(User.id == user_id).first()
    
    if not recipient:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Récupérer l'historique des messages entre les deux utilisateurs
    messages = db.query(DirectMessage).filter(
        ((DirectMessage.sender_id == current_user.id) & (DirectMessage.receiver_id == user_id)) |
        ((DirectMessage.sender_id == user_id) & (DirectMessage.receiver_id == current_user.id))
    ).order_by(DirectMessage.created_at).all()
    
    # Récupérer la liste des contacts
    contacts = db.query(User).join(
        DirectMessage, 
        ((DirectMessage.sender_id == User.id) | (DirectMessage.receiver_id == User.id))
    ).filter(
        (DirectMessage.sender_id == current_user.id) | (DirectMessage.receiver_id == current_user.id)
    ).distinct().all()
    
    return templates.TemplateResponse("direct_messages.html", {
        "request": request, 
        "current_user": current_user,
        "recipient": recipient,
        "messages": messages,
        "contacts": contacts
    })


# Route WebSocket
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: int,
    db: Session = Depends(get_db)
):
    try:
        # Authentification
        session_token = websocket.cookies.get("session")
        if not session_token:
            await websocket.close(code=1008, reason="Unauthorized")
            return
        
        # Vérifier que l'utilisateur existe
        user = db.query(User).filter(User.username == session_token).first()
        if not user or user.id != user_id:
            await websocket.close(code=1008, reason="Unauthorized")
            return
        
        # Connexion du WebSocket
        await websocket_manager.connect(websocket, user_id)
        
        print(f"WebSocket connecté pour l'utilisateur {user_id}")
        
        while True:
            # Maintenir la connexion ouverte
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        print(f"WebSocket déconnecté pour l'utilisateur {user_id}")
        websocket_manager.disconnect(websocket, user_id)
    except Exception as e:
        print(f"Erreur WebSocket: {e}")
        await websocket.close(code=1011)

# Initialisation de l'admin
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    create_default_admin(db)
    db.close()

