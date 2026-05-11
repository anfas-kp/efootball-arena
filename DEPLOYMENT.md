# 🌐 Free Hosting Deployment Guide

To host your Django project completely for **free**, you will use a combination of three generous free-tier services. Here is your step-by-step guide to getting it live.

### The Free Hosting Stack
1. **GitHub**: To hold your code.
2. **Render.com**: To host the actual web application.
3. **Neon.tech**: To host the PostgreSQL database (Render's free DB expires after 90 days, Neon's is forever free).
4. **Cloudinary.com**: To permanently store uploaded team logos and screenshots.

---

### Step 1: Push your code to GitHub
Before you can host the website, the code needs to be on GitHub.
1. Go to [GitHub.com](https://github.com/) and create a free account.
2. Create a new repository (name it `efootball-arena`).
3. Open your terminal in VS Code (inside the `d:\efootball` folder) and run:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/efootball-arena.git
   git push -u origin main
   ```
*(Replace the URL with your actual GitHub repository URL).*

---

### Step 2: Get your Cloudinary Credentials (For Image Storage)
Because free hosts delete files every time the server sleeps, we need Cloudinary to store images permanently.
1. Go to [Cloudinary.com](https://cloudinary.com/) and create a free account.
2. Go to your **Dashboard**.
3. Locate your **Product Environment Credentials**. You will need to copy three separate values for Step 4:
   - **Cloud Name** (e.g., `dabcdefgh`)
   - **API Key** (e.g., `123456789012345`)
   - **API Secret** (e.g., `AbCdEfGhIjKlMnOpQrStUvWxYz`)

---

### Step 3: Get your Database URL (Neon.tech)
1. Go to [Neon.tech](https://neon.tech/) and sign up.
2. Create a new project (name it `efootball-db`).
3. Once created, you will see a **Connection string** on the dashboard. It looks like:
   `postgres://username:password@ep-cool-db.us-east-2.aws.neon.tech/neondb`
   *(Save this URL for Step 4).*

---

### Step 4: Setup Redis (For Fast Background Tasks)
1. In Render, click **New** -> **Redis**.
2. Name it `efootball-redis`.
3. Select **"Free"** and click **Create Redis**.
4. Once created, copy the **Internal Redis URL** (e.g., `redis://red-xxx:6379`).

---

### Step 5: Deploy on Render
1. Go to [Render.com](https://render.com/) and click **New** -> **Web Service**.
2. Connect your repository.
3. Fill out the details:
   - **Build Command**: `bash build.sh`
   - **Start Command**: `bash run.sh`
   - **Instance Type**: `Free`
4. Click **Advanced** -> **Add Environment Variable**:

| Key | Value |
| :--- | :--- |
| `PYTHON_VERSION` | `3.11.0` |
| `DEBUG` | `False` |
| `SECRET_KEY` | *(Any random text)* |
| `ALLOWED_HOSTS` | `*` |
| `DATABASE_URL` | *(Your Neon.tech URL)* |
| `REDIS_URL` | *(Your Internal Redis URL from Step 4)* |
| `CLOUDINARY_CLOUD_NAME` | *(Your Cloud Name)* |
| `CLOUDINARY_API_KEY` | *(Your API Key)* |
| `CLOUDINARY_API_SECRET` | *(Your API Secret)* |

5. Click **Create Web Service**.

6. Click **Create Web Service**.

---

### Step 7: Windows Development Workarounds
If you are developing on Windows, Celery may encounter `Access Denied` errors with the default pool. Use this command to run your worker:
```bash
celery -A efootball_project worker --loglevel=info -P solo
```

### 📈 Production Scaling & Stats
With the new **Computed Stats System**, your server will handle 1,000+ teams easily.
- **Standings**: Are pre-computed in the `LeagueStanding` table.
- **Auto-Sync**: When you approve a result in the dashboard, a Django Signal automatically triggers a background refresh. No manual action is needed.

### 🔐 Security & HTTPS
When `DEBUG` is set to `False` on Render:
- The site will automatically redirect all traffic to **HTTPS**.
- Session and CSRF cookies are set to `SECURE=True`.
- **HSTS** is enabled for 1 year to ensure browser-level security.

---

### Step 8: You're Live! 🚀
Render will now read your `build.sh` file, install all the packages, connect to Neon and Cloudinary, and start the server. 

**Wait 3-5 minutes**, and Render will give you a live URL at the top left (e.g., `https://efootball-arena.onrender.com`). 

#### Final Step: Create an Admin Account
Because this is a fresh database on Neon, you will need to create a new Superuser for your live site. 
1. In your Render dashboard, click on your live web service.
2. Click the **"Shell"** tab.
3. Type the following command and follow the prompts:
   ```bash
   python manage.py createsuperuser
   ```

You can now log into your live website using this admin account!
