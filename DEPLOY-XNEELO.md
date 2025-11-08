# Deploying SkyScansGames to xneelo

This guide covers deploying the FastAPI backend and React frontend to xneelo hosting.

## Prerequisites

- xneelo VPS or Cloud hosting account (Python support required)
- Domain name (can be purchased through xneelo or transferred)
- SSH access to your server
- Python 3.12+ installed on the server

## Step 0: Purchase Domain (if needed)

### Option A: Purchase Domain Through xneelo

1. **Log into xneelo Control Panel**
   - Go to https://xneelo.co.za
   - Log into your account

2. **Purchase Domain**
   - Navigate to **Domains** → **Register Domain**
   - Search for your desired domain name (e.g., `skyscansgames.co.za` or `.com`)
   - Add to cart and complete purchase
   - Domain will be automatically added to your account

3. **Domain Management**
   - Your domain will appear in **Domains** section
   - DNS management is available in the same control panel

### Option B: Use Existing Domain

If you already have a domain:
- Transfer it to xneelo, OR
- Point DNS nameservers to xneelo's nameservers

**xneelo Nameservers** (check your account for exact nameservers):
- `ns1.xneelo.co.za`
- `ns2.xneelo.co.za`

## Understanding Domain vs Hosting

**Important:** You need BOTH:
1. **Domain** (e.g., `skyscansgames.co.za`) - This is your website address
2. **Hosting/Server** (xneelo VPS or Cloud) - This is where your backend and frontend actually run

### What is "Cloud Hosting"? (Not Cloud Storage!)

**Cloud Hosting** = Virtual server in the cloud (a computer/server you rent)
- ✅ Runs your Python/FastAPI backend
- ✅ Serves your React frontend
- ✅ Has an IP address
- ✅ You can SSH into it
- ✅ Runs 24/7

**Cloud Storage** = File storage (like Dropbox, Google Drive)
- ❌ Cannot run Python applications
- ❌ Cannot host websites
- ❌ Just stores files

**For this project, you need Cloud Hosting (virtual server), NOT cloud storage!**

**How it works:**
- Your **domain** points to your **server's IP address** via DNS records
- Your **backend (FastAPI)** runs as a service on your server (port 8000)
- Your **frontend (React)** is built and served as static files via Nginx
- **Nginx** (web server) routes requests:
  - `yourdomain.com` → serves React frontend
  - `api.yourdomain.com` → proxies to backend on port 8000

**What you need to purchase:**
- ✅ Domain (can buy through xneelo)
- ✅ VPS or Cloud hosting (required for Python/FastAPI backend)

## Hosting Options

**Recommended:** xneelo VPS or Cloud hosting (not shared hosting, as you need Python/FastAPI)

### Option 1: Single Server (Backend + Frontend) - RECOMMENDED
- Deploy both backend and frontend on the same VPS/Cloud server
- Backend runs on one port (e.g., 8000) as a systemd service
- Frontend served as static files via Nginx
- Domain points to this server
- **Cost:** One VPS/Cloud hosting plan

### Option 2: Separate Services
- Backend on VPS/Cloud
- Frontend on shared hosting (static files only)
- **Cost:** VPS/Cloud + Shared hosting plan

## Simplified Single-Domain Setup (No Subdomain)

**This is the EASIEST option** - Everything runs on one domain:
- Frontend: `https://yourdomain.com`
- Backend: `https://yourdomain.com/api`

### Quick Comparison

| Feature | Subdomain Setup | Single-Domain Setup (Simplified) |
|---------|----------------|----------------------------------|
| **Frontend URL** | `https://yourdomain.com` | `https://yourdomain.com` |
| **Backend URL** | `https://api.yourdomain.com` | `https://yourdomain.com/api` |
| **DNS Records Needed** | 3 (root, www, api) | 2 (root, www) ✅ |
| **Nginx Config** | 2 server blocks | 1 server block ✅ |
| **SSL Certificates** | 3 domains | 2 domains ✅ |
| **Complexity** | Medium | Low ✅ |
| **Recommended For** | Production/Scale | Quick Setup ✅ |

**Benefits of Single-Domain Setup:**
- ✅ No subdomain DNS configuration needed
- ✅ Simpler setup
- ✅ Only need 2 DNS records (root + www)
- ✅ Works with basic hosting plans
- ✅ Easier SSL certificate management

**Jump to:** [Single-Domain Nginx Config](#5a-single-domain-nginx-config-simplified---no-subdomain)

---

## Deployment Steps

### 0. Create Cloud Instance in xneelo

**Yes, you need to create a cloud instance (VPS) to host your project!**

Since you've already created your xneelo cloud account and added bank details, follow these steps:

1. **Log into xneelo Control Panel**
   - Go to https://xneelo.co.za
   - Log into your account

2. **Navigate to Cloud/VPS Services**
   - Look for **"Cloud"**, **"VPS"**, or **"Virtual Servers"** in the menu
   - Or go to **"Services"** → **"Cloud Hosting"** or **"VPS Hosting"**

3. **Create New Instance**
   - Click **"Create Instance"**, **"New Server"**, or **"Add VPS"**
   - Select your preferred plan (minimum recommended):
     - **CPU**: 1-2 cores
     - **RAM**: 2GB minimum (4GB recommended)
     - **Storage**: 20GB minimum (SSD preferred)
     - **OS**: Ubuntu 22.04 LTS or Ubuntu 24.04 LTS (recommended)

4. **Configure Instance**
   - **Hostname**: `skyscansgames` (or your preferred name)
   - **Location**: Choose closest to your users
   - **SSH Key**: Add your SSH public key (or xneelo will provide root password)
   - **Firewall**: Allow SSH (port 22), HTTP (port 80), HTTPS (port 443)

5. **Complete Purchase/Activation**
   - Review and confirm
   - Instance will be created (usually takes 5-15 minutes)

6. **Get Your Server Details**
   - **Server IP Address**: Note this down (you'll need it for DNS)
   - **SSH Username**: Usually `root` or `ubuntu`
   - **SSH Password**: (if provided, or use SSH key)
   - **SSH Port**: Usually `22`

**Important:** Save these details! You'll need:
- Server IP address (for DNS configuration)
- SSH username and password/key (to connect)

### 1. Server Setup

#### Connect via SSH

Once your instance is created, connect to it:

**Option A: Using Password**
```bash
ssh root@your-server-ip
# or
ssh ubuntu@your-server-ip
```
Enter the password when prompted.

**Option B: Using SSH Key**
```bash
ssh -i ~/.ssh/your-key.pem root@your-server-ip
# or
ssh -i ~/.ssh/your-key.pem ubuntu@your-server-ip
```

**Replace `your-server-ip` with the actual IP address from step 6 above!**

#### Install Dependencies
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python 3.12+ and pip
sudo apt-get install -y python3.12 python3.12-venv python3-pip nginx

# Install Node.js 18+ (for building frontend)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 2. Clone Repository

```bash
cd /var/www  # or your preferred directory
sudo git clone https://github.com/Tsebo200/SkyScansGames.git
sudo chown -R $USER:$USER SkyScansGames
cd SkyScansGames
```

### 3. Backend Setup

#### Create Virtual Environment
```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt gunicorn
```

#### Create Environment File
```bash
nano .env
```

Add:
```env
RAWG_API_KEY=your_rawg_api_key
# For subdomain setup:
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com,https://api.yourdomain.com
# For single-domain setup (simplified):
# ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
DATABASE_URL=/var/www/SkyScansGames/skyscans_games.db
OPENAI_API_KEY=your_openai_key  # Optional
PORT=8000
PYTHONUNBUFFERED=1
```

#### Test Backend
```bash
source venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Visit `http://your-server-ip:8000/docs` to verify.

### 4. Frontend Setup

#### Build React App
```bash
cd /var/www/SkyScansGames/frontend
npm install

# Create production .env
# For subdomain setup:
echo "REACT_APP_API_BASE=https://api.yourdomain.com" > .env.production
# For single-domain setup (simplified):
# echo "REACT_APP_API_BASE=https://yourdomain.com/api" > .env.production

# Build
npm run build
```

This creates a `build/` folder with static files.

### 5. Configure Nginx

#### Create Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/skyscansgames
```

Add:
```nginx
# Backend API (FastAPI)
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Frontend (React)
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    root /var/www/SkyScansGames/frontend/build;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/skyscansgames /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

---

### 5a. Single-Domain Nginx Config (Simplified - No Subdomain)

**Use this if you want everything on one domain** (e.g., `yourdomain.com` and `yourdomain.com/api`)

#### Create Simplified Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/skyscansgames
```

Replace with this simpler config:
```nginx
# Single domain - Frontend + Backend
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Frontend (React) - serve static files
    root /var/www/SkyScansGames/frontend/build;
    index index.html;

    # Backend API - proxy to FastAPI
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Handle /api without trailing slash
    location = /api {
        return 301 /api/;
    }

    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**Important:** For this setup, you also need to update the frontend build:

```bash
cd /var/www/SkyScansGames/frontend
# Use /api path instead of subdomain
echo "REACT_APP_API_BASE=https://yourdomain.com/api" > .env.production
npm run build
```

**DNS Configuration (Simplified):**
- Only need 2 A records in xneelo DNS:
  - `@` → Your server IP
  - `www` → Your server IP
- No subdomain needed!

#### Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/skyscansgames /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

### 6. Create Systemd Service (Backend)

#### Create Service File
```bash
sudo nano /etc/systemd/system/skyscansgames-backend.service
```

Add:
```ini
[Unit]
Description=SkyScansGames FastAPI Backend
After=network.target

[Service]
User=your-username
Group=your-username
WorkingDirectory=/var/www/SkyScansGames/backend
Environment="PATH=/var/www/SkyScansGames/backend/venv/bin"
ExecStart=/var/www/SkyScansGames/backend/venv/bin/gunicorn -k uvicorn.workers.UvicornWorker -w 2 -b 127.0.0.1:8000 main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable skyscansgames-backend
sudo systemctl start skyscansgames-backend
sudo systemctl status skyscansgames-backend
```

### 7. SSL Certificate (Let's Encrypt)

**For subdomain setup:**
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com
```

**For single-domain setup (simplified):**
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

This automatically updates Nginx config for HTTPS.

### 8. Domain Configuration in xneelo

Since you purchased/registered the domain through xneelo, DNS management is in the same control panel:

1. **Log into xneelo Control Panel**
   - Go to https://xneelo.co.za and log in

2. **Navigate to DNS Management**
   - Go to **Domains** → Select your domain → **DNS Management** or **DNS Settings**

3. **Add DNS Records**
   
   **Option A: Subdomain Setup** (requires 3 A records):
   - **A Record**: 
     - **Name/Host**: `@` (or leave blank for root domain)
     - **Value/IP**: Your server IP address
     - **TTL**: 3600 (default)
   
   - **A Record**: 
     - **Name/Host**: `www`
     - **Value/IP**: Your server IP address
     - **TTL**: 3600
   
   - **A Record** (for API subdomain):
     - **Name/Host**: `api`
     - **Value/IP**: Your server IP address
     - **TTL**: 3600
   
   **Option B: Single-Domain Setup (Simplified)** (only 2 A records needed):
   - **A Record**: 
     - **Name/Host**: `@` (or leave blank for root domain)
     - **Value/IP**: Your server IP address
     - **TTL**: 3600
   
   - **A Record**: 
     - **Name/Host**: `www`
     - **Value/IP**: Your server IP address
     - **TTL**: 3600
   
   ✅ **Recommended:** Use Option B (single-domain) for simpler setup!

4. **Save Changes**
   - DNS changes may take 15 minutes to 48 hours to propagate
   - You can check propagation at https://www.whatsmydns.net

**Note:** If you're using xneelo's VPS/Cloud hosting, your server IP should be provided in your hosting account details.

### 9. Firewall Configuration

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 10. Update Frontend Environment

After SSL is set up, rebuild frontend with HTTPS API URL:

**For subdomain setup:**
```bash
cd /var/www/SkyScansGames/frontend
echo "REACT_APP_API_BASE=https://api.yourdomain.com" > .env.production
npm run build
sudo systemctl reload nginx
```

**For single-domain setup (simplified):**
```bash
cd /var/www/SkyScansGames/frontend
echo "REACT_APP_API_BASE=https://yourdomain.com/api" > .env.production
npm run build
sudo systemctl reload nginx
```

## Maintenance

### View Backend Logs
```bash
sudo journalctl -u skyscansgames-backend -f
```

### Restart Backend
```bash
sudo systemctl restart skyscansgames-backend
```

### Update Application
```bash
cd /var/www/SkyScansGames
git pull origin master
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart skyscansgames-backend

cd ../frontend
npm install
npm run build
sudo systemctl reload nginx
```

## Troubleshooting

### Backend Not Starting
- Check logs: `sudo journalctl -u skyscansgames-backend -n 50`
- Verify environment variables in `.env`
- Test manually: `cd backend && source venv/bin/activate && python -m uvicorn main:app`

### Frontend Not Loading
- Check Nginx logs: `sudo tail -f /var/log/nginx/error.log`
- Verify `build/` folder exists and has files
- Check file permissions: `sudo chown -R www-data:www-data /var/www/SkyScansGames/frontend/build`

### Database Issues
- Ensure database file has write permissions: `chmod 664 /var/www/SkyScansGames/skyscans_games.db`
- Check database path in `.env` matches actual location

## Alternative: Docker Deployment

If xneelo supports Docker, you can use the existing Dockerfile:

```bash
cd backend
docker build -t skyscansgames-backend .
docker run -d -p 8000:10000 \
  -e RAWG_API_KEY=your_key \
  -e ALLOWED_ORIGINS=https://yourdomain.com \
  -v /data:/data \
  skyscansgames-backend
```

## Support

For xneelo-specific issues, contact xneelo support or check their documentation:
- https://xneelo.co.za/support/

