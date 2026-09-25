import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routers import auth, cash, customers, products, quotes, sales, stats, stock, suppliers, users

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="La Cave du Coin — Caisse & Stock", version="1.0.0")

# Le schéma de la base est géré par Alembic (voir migrations/) : exécuter
# `alembic upgrade head` avant de démarrer l'application, plutôt que de
# recréer les tables automatiquement ici.

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Cache-busting : change à chaque redémarrage du serveur (donc à chaque
# déploiement), pour que le navigateur recharge automatiquement le CSS/JS
# mis à jour au lieu de garder une version en cache jusqu'à un hard refresh
# manuel. Disponible dans tous les templates via {{ static_version }}.
templates.env.globals["static_version"] = str(int(time.time()))

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(stock.router)
app.include_router(suppliers.router)
app.include_router(cash.router)
app.include_router(sales.router)
app.include_router(quotes.router)
app.include_router(customers.router)
app.include_router(stats.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root(request: Request):
    return templates.TemplateResponse(request, "login.html", {})


@app.get("/pos")
def pos_page(request: Request):
    return templates.TemplateResponse(request, "pos.html", {})


@app.get("/stock")
def stock_page(request: Request):
    return templates.TemplateResponse(request, "stock.html", {})


@app.get("/cash")
def cash_page(request: Request):
    return templates.TemplateResponse(request, "cash.html", {})


@app.get("/dashboard")
def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html", {})


@app.get("/users")
def users_page(request: Request):
    return templates.TemplateResponse(request, "users.html", {})


@app.get("/account")
def account_page(request: Request):
    return templates.TemplateResponse(request, "account.html", {})


@app.get("/debts")
def debts_page(request: Request):
    return templates.TemplateResponse(request, "debts.html", {})
