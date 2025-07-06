
---

## 🔧 Extra Installation Steps for Cloud Environments

This section covers platform-specific steps for setting up and running the app in cloud environments like **Ubuntu on AWS** and **GitHub Codespaces**.

---

### 🖥️ Ubuntu Linux on AWS

#### ✅ Required Utilities

Install essential packages:

```bash
sudo apt update
sudo apt install python3.12-venv make
```

#### 🐳 Install Docker

Follow the official Docker instructions for Ubuntu:
👉 [https://docs.docker.com/engine/install/ubuntu/](https://docs.docker.com/engine/install/ubuntu/)

> Make sure to follow the post-install steps to allow your user to run Docker without `sudo`.

#### 🔓 Open Required Ports

Expose the following ports in your EC2 **Security Group** (SG) settings under **Inbound Rules**:

| Port | Protocol | Purpose           |
| ---- | -------- | ----------------- |
| 3000 | TCP      | Frontend UI       |
| 8123 | TCP      | LangGraph backend |

Set these as **Custom TCP Rules** and allow access from your desired IP range (e.g., `0.0.0.0/0` for open access during dev).

---

### 🌐 GitHub Codespaces

GitHub Codespaces automatically maps exposed ports and creates HTTPS-accessible links.

#### ✅ Frontend (Port 3000)

After you start the services. 
1. Codespaces will generate a link for port `3000` (e.g., `https://3000-username-...githubpreview.dev`).
2. Click the **globe icon** next to the port and set its visibility to **Public** so others can access it.

#### 🔁 Backend (Port 8123)

1. When the LangGraph backend starts, Codespaces will generate a link for port `8123`.
2. Again, set visibility to **Public**.
3. Copy this backend URL and paste it into the Agent Chat UI where it asks for the backend endpoint.


