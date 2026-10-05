# Complete Beginner's Guide: Managing Your Oracle Cloud VM from Windows

This guide explains from absolute scratch how you can open your terminal on Windows, connect directly to your Ubuntu virtual machine in Frankfurt, navigate the filesystem, view logs, and manage your services.

---

## 1. What Is Happening Under the Hood?

Your virtual machine (`YB-ChatApp`) is a complete, independent Linux computer running inside Oracle's datacenter in Frankfurt, Germany. 

When you connect to it using **SSH (Secure Shell)**:
* Your Windows terminal becomes the display screen and keyboard for that remote Linux computer.
* Any command you type runs directly on that machine's CPU and RAM.
* The `.key` file in your `Downloads` folder is your digital passport that proves you are the owner.

---

## 2. How to Open Your Terminal and Connect

### Step 1: Open PowerShell
1. On your Windows keyboard, press the **Windows Key**.
2. Type **`PowerShell`** or **`Terminal`**.
3. Press **Enter**. (A blue or black terminal window opens).

---

### Step 2: The Magic 1-Word Shortcut
Because we configured your `~/.ssh/config` file, you now only need to type **one short command** and press **Enter**:

```powershell
ssh yb-chatapp
```

*(No IP addresses, no file paths, and no usernames to remember! Your computer automatically reads your saved config and logs you in.)*

#### The Full Command (If ever needed as a backup):
```powershell
ssh -i "~/.ssh/oracle_vms.key" ubuntu@130.61.9.37
```

Once connected, your command prompt will change from `PS C:\Users\YOBI>` to:
```bash
ubuntu@yb-chatapp:~$
```
**You are now officially inside your Linux VM in Frankfurt, Germany!**

---

## 3. Essential Linux Navigation & Commands

Once you are logged into the VM, here are the everyday commands you will use:

### Where am I and what is here?
* **`pwd`** (Print Working Directory): Shows which folder you are currently inside.
* **`ls`** (List): Shows all files and folders in the current directory.
* **`ls -la`**: Shows all files, including hidden files (starting with `.`) and file permissions.

### Moving around folders:
* **`cd chat_server`**: Moves inside the `chat_server` folder.
* **`cd ..`**: Moves back up one folder level.
* **`cd ~`**: Jumps straight back to your home directory (`/home/ubuntu`).

---

## 4. How to View and Edit Files

### Viewing file contents (Read-Only):
* **`cat filename.py`**: Prints the entire file to your screen.
* **`less filename.py`**: Lets you scroll through a long file with arrow keys. Press **`q`** to exit.
* **`tail -n 20 filename.py`**: Shows only the last 20 lines of a file.

### Editing a file (The Nano Editor):
Ubuntu comes with a simple built-in text editor called **nano**:
```bash
nano /home/ubuntu/chat_server/chat_project/settings.py
```
* **Arrow keys:** Move your cursor around.
* **Type:** Add or modify code directly.
* **Save changes:** Press **`Ctrl + O`**, then hit **Enter**.
* **Exit nano:** Press **`Ctrl + X`**.

---

## 5. How to Check Application Logs & Health

If something isn't working or you want to see who is chatting in real time:

### View Live Daphne Chat App Logs:
```bash
sudo journalctl -u chat-app -f
```
* The `-f` flag means **"follow"**—it streams live logs as users connect and send messages!
* To stop watching logs and return to the prompt: Press **`Ctrl + C`**.

### View Redis Logs:
```bash
sudo tail -n 50 /var/log/redis/redis-server.log
```

### View Nginx Web Server Access Logs:
```bash
sudo tail -f /var/log/nginx/access.log
```

---

## 6. How to Restart Services

Whenever you modify server files or settings, you restart the relevant service:

| What you want to do | Command |
| :--- | :--- |
| **Restart the Chat App (Daphne)** | `sudo systemctl restart chat-app` |
| **Check if Chat App is Running** | `sudo systemctl status chat-app` |
| **Restart the Nginx Web Server** | `sudo systemctl restart nginx` |
| **Restart Redis** | `sudo systemctl restart redis-server` |

---

## 7. How to Update Code from GitHub

When you commit new changes locally on your Windows PC and push them to GitHub, here is how you update the server in 3 quick commands:

```bash
# 1. Move to the project folder
cd /home/ubuntu/chat_server

# 2. Pull the latest code from GitHub
git pull origin main

# 3. Restart Daphne to apply the new code
sudo systemctl restart chat-app
```

---

## 8. How to Exit the VM

When you are done working on the server and want to return to your normal Windows prompt:
```bash
exit
```
Your terminal will say `Connection to 130.61.9.37 closed.` and return you to Windows PowerShell.
