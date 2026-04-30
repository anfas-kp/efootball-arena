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

### Step 2: Get your Cloudinary URL (For Image Storage)
Because free hosts delete files every time the server sleeps, we need Cloudinary to store images permanently.
1. Go to [Cloudinary.com](https://cloudinary.com/) and create a free account.
2. Go to your **Dashboard**.
3. Under "Product Environment Credentials", copy your **API Environment variable**. It will look something like this:
   `CLOUDINARY_URL=cloudinary://123456789:abcdefg@yourcloudname`
   *(Save this URL for Step 4).*

---

### Step 3: Get your Database URL (Neon.tech)
1. Go to [Neon.tech](https://neon.tech/) and sign up.
2. Create a new project (name it `efootball-db`).
3. Once created, you will see a **Connection string** on the dashboard. It looks like:
   `postgres://username:password@ep-cool-db.us-east-2.aws.neon.tech/neondb`
   *(Save this URL for Step 4).*

---

### Step 4: Deploy on Render
1. Go to [Render.com](https://render.com/) and sign up using your GitHub account.
2. Click **New** -> **Web Service**.
3. Select **"Build and deploy from a Git repository"** and connect the `efootball-arena` repository you made in Step 1.
4. Fill out the deployment details:
   - **Name**: `efootball-arena`
   - **Language**: `Python 3`
   - **Branch**: `main`
   - **Build Command**: `bash build.sh`
   - **Start Command**: `gunicorn efootball_project.wsgi:application`
   - **Instance Type**: `Free`
5. Scroll down and click **Advanced** -> **Add Environment Variable**. Add the following exactly:

| Key | Value |
| :--- | :--- |
| `PYTHON_VERSION` | `3.11.0` |
| `DEBUG` | `False` |
| `SECRET_KEY` | *(Type any random long password here)* |
| `ALLOWED_HOSTS` | `*` |
| `DATABASE_URL` | *(Paste your Neon.tech URL from Step 3 here)* |
| `CLOUDINARY_URL` | *(Paste your Cloudinary URL from Step 2 here)* |

6. Click **Create Web Service**.

---

### Step 5: You're Live! 🚀
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
