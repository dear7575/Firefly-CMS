
<img src="./docs/images/1131.png" width = "405" height = "511" alt="Firefly CMS" align=right />

<div align="center">

# Firefly CMS
> A Dynamic Blog Content Management System Based on Firefly Theme
>
> ![Node.js >= 20](https://img.shields.io/badge/node.js-%3E%3D20-brightgreen)
![pnpm >= 9](https://img.shields.io/badge/pnpm-%3E%3D9-blue)
![Astro](https://img.shields.io/badge/Astro-5.x-orange)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)
>
> [![Stars](https://img.shields.io/github/stars/dear7575/Firefly-CMS?style=social)](https://github.com/dear7575/Firefly-CMS/stargazers)
[![Forks](https://img.shields.io/github/forks/dear7575/Firefly-CMS?style=social)](https://github.com/dear7575/Firefly-CMS/network/members)
[![Issues](https://img.shields.io/github/issues/dear7575/Firefly-CMS)](https://github.com/dear7575/Firefly-CMS/issues)
>
> ![GitHub License](https://img.shields.io/github/license/dear7575/Firefly-CMS)
>
</div>

---

**Firefly CMS** is a secondary development project based on [CuteLeaf/Firefly](https://github.com/CuteLeaf/Firefly) theme. While preserving the beautiful frontend, it adds a complete admin management system, upgrading from a static blog to a dynamic content management system.

📖 README: **[简体中文](README.md)** | **[English](README.en.md)**

## 🆕 New Features in This Fork

### Admin Management System
- **FastAPI Backend** - High-performance async API service based on Python
- **MySQL Database** - Persistent data storage with UUID primary keys
- **JWT Authentication** - Secure user authentication mechanism
- **RESTful API** - Standardized interface design

### Management Features
- **Post Management** - Online editor (Vditor), draft/publish, pinning, password protection
- **Category Management** - CRUD operations, color tags, enable/disable
- **Tag Management** - CRUD operations, color tags, enable/disable
- **Friend Links** - Link management, sorting weight, avatar/description
- **Announcement Management** - CRUD operations, show/hide, type selection (info/warning/success)
- **System Settings** - Dynamic management of site info, profile, theme config
- **Social Links** - Social media link management
- **Access Logs** - Login records, API access statistics, log cleanup

### Dynamic Configuration
- **Site Info** - Title, subtitle, description, keywords
- **Profile** - Avatar, nickname, bio
- **Brand Settings** - Logo, navbar title
- **Banner Settings** - Homepage banner text
- **Theme Settings** - Theme color, default mode
- **Footer Settings** - ICP filing, copyright info
- **Announcement Config** - Dynamic announcement content with multiple types
- **About Page** - Dynamic about page content management

---

## ✨ Original Features

> The following features are inherited from [CuteLeaf/Firefly](https://github.com/CuteLeaf/Firefly)

### Core Features
- [x] **Astro + Tailwind CSS** - Ultra-fast static site generation based on modern tech stack
- [x] **Smooth Animations** - Swup page transitions for silky browsing experience
- [x] **Responsive Design** - Perfect adaptation for desktop, tablet, and mobile
- [x] **Multi-language Support** - i18n internationalization, supports Chinese, English, Japanese, Russian
- [x] **Full-text Search** - Pagefind client-side search, supports MeiliSearch

### Personalization
- [x] **Sidebar** - Single or dual sidebar configuration
- [x] **Post Layout** - List, grid, waterfall layouts
- [x] **Wallpaper Mode** - Banner wallpaper, fullscreen wallpaper, solid background
- [x] **Theme Color** - 360° hue adjustment, light/dark/system modes

### Page Components
- [x] **Guestbook** - Integrated comment system
- [x] **Announcement** - Top announcement banner
- [x] **Live2D** - Spine and Live2D animations
- [x] **Site Statistics** - Posts, categories, tags count, total words, uptime
- [x] **Site Calendar** - Monthly calendar with published posts
- [x] **Share Poster** - Article share poster generation
- [x] **Friend Links** - Beautiful friend link cards
- [x] **Bangumi** - Bangumi API anime tracking
- [x] **Comment System** - Twikoo, Waline, Giscus, Disqus, Artalk
- [x] **Music Player** - APlayer + Meting API

### Content Enhancement
- [x] **Image Lightbox** - Fancybox image preview
- [x] **Table of Contents** - Dynamic TOC with anchor navigation
- [x] **Code Highlighting** - Expressive Code
- [x] **Math Formulas** - KaTeX rendering
- [x] **Random Covers** - API random cover images

---

## 🚀 Quick Start

### Deployment Options

#### 🐳 Recommended: Docker Deployment (Production Ready)

The easiest way to get started with just a few commands:

```bash
# Linux/Mac users
chmod +x docker-start.sh
./docker-start.sh

# Windows users
docker-start.bat
```

Or manually:

```bash
docker-compose up -d
```

Access URLs:
- 🌐 Homepage: `http://localhost`
- 📊 Admin Panel: `http://localhost/admin`
- 📚 API Docs: `http://localhost/api/docs`

See [Docker Deployment Guide](./docs/DOCKER_DEPLOYMENT.md) for details.

---

#### 💻 Development: Manual Deployment

### Requirements

**Frontend:**
- Node.js >= 20
- pnpm >= 9

**Backend:**
- Python >= 3.10
- MySQL >= 5.7

### 1. Clone Repository

```bash
git clone https://github.com/dear7575/Firefly-CMS.git
cd Firefly-CMS
```

### 2. Backend Deployment

```bash
# Enter backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure database (edit connection info in database.py)
# DATABASE_URL = "mysql+pymysql://username:password@host:port/database"

# Initialize database (required for first deployment)
python setup.py                  # Basic init (tables + admin + default settings)
# or
python setup.py --demo           # Basic init + demo data (categories, tags, sample posts)
# or
python setup.py --full           # Full init (basic + demo data + frontend config import)
# or
python setup.py --import-posts   # Import static Markdown posts to database
# or
python setup.py --reset          # Reset database (DANGER: deletes all data and reinitializes)

# Start backend service
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend API docs: `http://localhost:8000/docs`

### 3. Frontend Deployment

```bash
# Return to project root
cd ..

# Install dependencies
pnpm install

# Configure API URL (optional, defaults to http://localhost:8000)
# Edit .env file: PUBLIC_API_URL=http://your-api-url

# Start development server
pnpm dev
```

Frontend: `http://localhost:4321`
Admin Panel: `http://localhost:4321/admin/`

### 4. Default Admin Account

The backend automatically creates a default admin on first start:
- Username: `admin`
- Password: `admin123`

**Please change the password immediately after login!**

---

## 📁 Project Structure

```
Firefly-CMS/
├── backend/                 # Backend service
│   ├── main.py             # FastAPI entry
│   ├── setup.py            # Database initialization script
│   ├── models.py           # Database models
│   ├── database.py         # Database config
│   ├── auth.py             # Authentication module
│   ├── routes/             # API routes
│   │   ├── posts.py        # Posts API
│   │   ├── categories.py   # Categories API
│   │   ├── tags.py         # Tags API
│   │   ├── friends.py      # Friend links API
│   │   ├── settings.py     # Settings API
│   │   ├── social_links.py # Social links API
│   │   ├── logs.py         # Logs API
│   │   └── auth.py         # Auth API
│   └── requirements.txt    # Python dependencies
├── src/
│   ├── pages/
│   │   └── admin/          # Admin pages
│   ├── services/           # Frontend services
│   │   ├── api.ts          # API calls
│   │   └── siteSettings.ts # Dynamic config
│   └── ...                 # Other frontend files
└── ...
```

---

## 🔧 Configuration

### Backend Configuration

Edit `backend/database.py`:

```python
DATABASE_URL = "mysql+pymysql://username:password@host:port/database?charset=utf8mb4"
```

### Frontend Configuration

Create `.env` file:

```env
PUBLIC_API_URL=http://localhost:8000
```

### Production Deployment

1. **Backend**: Deploy with Gunicorn + Uvicorn
   ```bash
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
   ```

2. **Frontend**: Build static files or use SSR mode
   ```bash
   pnpm build
   ```

---

## 🙏 Acknowledgments

### Original Projects
- **[CuteLeaf/Firefly](https://github.com/CuteLeaf/Firefly)** - This project is based on this theme, thanks to [CuteLeaf](https://github.com/CuteLeaf) for the open source contribution
- **[saicaca/fuwari](https://github.com/saicaca/fuwari)** - Upstream project of Firefly, thanks to [saicaca](https://github.com/saicaca) for the original design

### Tech Stack
- [Astro](https://astro.build) - Frontend framework
- [Tailwind CSS](https://tailwindcss.com) - CSS framework
- [FastAPI](https://fastapi.tiangolo.com) - Backend framework
- [SQLAlchemy](https://www.sqlalchemy.org) - ORM
- [Vditor](https://github.com/Vanessa219/vditor) - Markdown editor

---

## 📝 License

This project is licensed under the [MIT License](./LICENSE).

**Copyright Notice:**
- Copyright (c) 2024 [saicaca](https://github.com/saicaca) - Original Fuwari project
- Copyright (c) 2025 [CuteLeaf](https://github.com/CuteLeaf) - Firefly theme
- Copyright (c) 2025 [dear7575](https://github.com/dear7575) - Firefly CMS fork

Under the MIT License, you are free to use, modify, and distribute this project, but you must retain the above copyright notices.

---

## 🤝 Contributing

Welcome to submit [Issues](https://github.com/dear7575/Firefly-CMS/issues) or [Pull Requests](https://github.com/dear7575/Firefly-CMS/pulls)!

