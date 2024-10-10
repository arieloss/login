from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

app = FastAPI()

# Pour gérer les sessions utilisateur
app.add_middleware(SessionMiddleware, secret_key="votre_secret")

templates = Jinja2Templates(directory="templates")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Remplace "*" par l'URL de ton front-end si c'est plus sécurisé
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def create_users_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        password TEXT NOT NULL
                    )''')
    conn.commit()
    conn.close()

# Appeler la fonction pour créer la table au démarrage de l'application
create_users_table()



# Initialisation de la base de données SQLite
def init_db():
    conn = sqlite3.connect('users.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     username TEXT NOT NULL,
                     password TEXT NOT NULL);''')
    conn.close()


# Route pour afficher la page de connexion
@app.get("/", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# Route pour la connexion
@app.post("/login", response_class=HTMLResponse)
async def login_user(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        request.session['username'] = username
        return RedirectResponse("/dashboard", status_code=302)
    else:
        raise HTTPException(status_code=400, detail="Invalid credentials")


# Route pour l'inscription
@app.post("/signup", response_class=HTMLResponse)
async def signup_user(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()
    return RedirectResponse("/", status_code=302)


# Route pour le tableau de bord personnalisé
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    username = request.session.get('username')
    if not username:
        return RedirectResponse("/", status_code=302)

    # Messages de bienvenue personnalisés pour chaque utilisateur
    welcome_messages = {
        "ariel": "Bienvenue, Ariel !",
        "jane": "Hello Jane !",
        "default": "Bienvenue sur votre tableau de bord !"
    }

    welcome_message = welcome_messages.get(username.lower(), welcome_messages["default"])
    return templates.TemplateResponse("dashboard.html",
                                      {"request": request, "username": username, "welcome_message": welcome_message})


if __name__ == "__main__":
    init_db()  # Initialiser la base de données au démarrage
