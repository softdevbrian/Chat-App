# Oracle Cloud: Cost Management, Usage Verification & Instance Control Guide

This guide explains why Oracle Cloud cards are occasionally pinged, how to verify that your account is 100% within the **Always Free Tier**, the exact terminal commands to inspect your server's hardware utilization, how to navigate Oracle's billing dashboard, and how to safely pause and resume your VM at will.

---

## 1. Demystifying the €0.90 EUR (~$1.00 USD) Charge

If you received a bank alert for ~€0.90 EUR or a "Payment Failure" notification from Oracle, **do not panic**. This is standard industry behavior across cloud providers.

### 💡 What Actually Happened:
* **Pre-Authorization Ping (Active Card Check):** Cloud providers (Oracle, AWS, Google Cloud, Azure) periodically test registered payment methods by placing a temporary **$1.00 USD / €0.90 EUR authorization hold** to ensure that your debit/credit card has not expired, been cancelled, or reported lost.
* **Why the Bank Alerted "Payment Failure":** Modern banks use 3D-Secure / OTP algorithms. When Oracle's automated system sends a $1 card validation ping in the background without prompting you for an SMS OTP, fraud detection algorithms at your bank often decline the automated transaction and notify you.
* **Temporary & Refunded:** When this validation hold goes through, it is **never actually settled as a bill**. It automatically drops off or is refunded within 3 to 7 business days.

---

## 2. Oracle "Always Free" Limits vs. Your Exact VM Usage

Oracle Cloud offers one of the most generous permanent Free Tiers in the cloud industry. Here is how your live VM compares to the hard limits:

| Resource | Your Server's Current Allocation | Oracle Always Free Limit | Percentage Used | Free Tier Status |
| :--- | :--- | :--- | :--- | :--- |
| **Ampere A1 OCPU** | **1 OCPU** | Up to **4 OCPUs** | **25%** | ✅ 100% Free |
| **Ampere Memory (RAM)** | **6 GB** | Up to **24 GB** | **25%** | ✅ 100% Free |
| **Block Volume (Disk)** | **46.5 GB** | Up to **200 GB** | **23.2%** | ✅ 100% Free |
| **Outbound Data Transfer** | < 1 GB | Up to **10 TB / month** | **< 0.01%** | ✅ 100% Free |
| **Architecture** | Direct Nginx (No Cloud Load Balancer) | Free | **0%** | ✅ 100% Free |

> [!NOTE]
> As long as your instance stays within these thresholds, Oracle will **never** charge you for computing or disk resources.

---

## 3. How to Connect from Windows: PowerShell Setup & Rules

Before running any verification or control commands, follow these rules so you never get stuck:

### ⚠️ Should You Run PowerShell as Administrator?
**NO. Always run PowerShell as a REGULAR USER (Standard Privileges).**

* **Why?** Your private SSH key (`oracle_vms.key`) and SSH configuration (`config`) live in your personal user directory: `C:\Users\YOBI\.ssh\`.
* In Step 3 of deployment, we locked down Windows security permissions so that **only your regular user account (`YOBI\YOBI`)** has exclusive read permissions on the key.
* If you open PowerShell "As Administrator", Windows executes with an elevated administrator token. OpenSSH may look for keys under an administrative profile or encounter permission mismatches.
* **How to open properly:** Press the **Windows Key** &rarr; Type **`PowerShell`** &rarr; Press **Enter** (click normally, **do NOT** choose "Run as Administrator"). You can also simply open the integrated terminal in VS Code (`Ctrl + ~` or **Terminal** &rarr; **New Terminal**).

---

### 💡 Two Ways to Run Commands on Your Server

#### Method A: The One-Liner (Remote Execution)
You stay in your Windows PowerShell. SSH sends the command over the internet, runs it on Linux, and prints the result directly to your Windows terminal:
```powershell
ssh yb-chatapp "<command>"
```
*Example:* `ssh yb-chatapp "uptime"`

#### Method B: The Interactive Session (Logging Inside Linux)
You open a live command line inside the Ubuntu virtual machine:
1. In PowerShell, type:
   ```powershell
   ssh yb-chatapp
   ```
2. Your prompt will change from `PS C:\...>` to:
   ```bash
   ubuntu@yb-chatapp:~$
   ```
3. You are now working directly inside your cloud server in Frankfurt! You can type Linux commands directly (`uptime`, `df -h`, `free -m`) without prefixing them with `ssh`.
4. When finished, type **`exit`** and press **Enter** to disconnect and return to Windows.

#### 🔑 Backup Command (If the `yb-chatapp` shortcut is ever unavailable):
```powershell
ssh -i "C:\Users\YOBI\.ssh\oracle_vms.key" ubuntu@130.61.9.37
```

---

## 4. Terminal Commands: How to Check VM Status & Resource Health

You can verify your VM's live resource consumption from your standard Windows PowerShell:

### 1. Check System Uptime & CPU Load
```powershell
ssh yb-chatapp "uptime"
```
**Example Output:**
```text
 17:11:25 up 3 days, 23:47,  1 user,  load average: 0.00, 0.00, 0.00
```
* **`load average: 0.00, 0.00, 0.00`**: Shows that your CPU is virtually idle when nobody is chatting.

---

### 2. Check Disk Space Allocation
```powershell
ssh yb-chatapp "df -h"
```
**Example Output:**
```text
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        45G  4.0G   41G   9% /
```
* **`Size 45G`**: Confirms that your boot volume is well within Oracle's 200 GB free tier cap.
* **`Used 4.0G (9%)`**: Ubuntu, Daphne, Redis, and Django are only using 4 GB total!

---

### 3. Check Memory (RAM) Allocation
```powershell
ssh yb-chatapp "free -m"
```
**Example Output:**
```text
               total        used        free      shared  buff/cache   available
Mem:            5903         614        2220           5        3269        5288
```
* **`total: 5903 MB (~6 GB)`**: Confirms your instance is provisioned with 6 GB RAM (well below the 24 GB free tier ceiling).
* **`used: 614 MB`**: The chat server runs lightweight, using less than 11% of available memory.

---

### 4. Check Active Background Services
```powershell
ssh yb-chatapp "systemctl is-active chat-app redis-server nginx"
```
**Expected Output:**
```text
active
active
active
```
* Confirms Daphne ASGI, Redis Channel Layer, and Nginx reverse proxy are healthy and operational.

---

## 5. How to Inspect Billing & Set Up Budget Alerts in Oracle Console

To verify your invoices and ensure zero unwanted charges:

### Step 1: Check Current Invoices
1. Log in to [cloud.oracle.com](https://cloud.oracle.com).
2. Open the **Navigation Menu (☰)** in the top-left corner.
3. Scroll down to **Billing & Cost Management** &rarr; **Invoices**.
4. Your balance should show **€0.00 / $0.00**.

### Step 2: View Detailed Cost Analysis
1. Open **Billing & Cost Management** &rarr; **Cost Analysis**.
2. Set the Date Range to **Current Month**.
3. Set **Group by** to **Service** or **SKU**.
4. Confirm that all daily spending charts show **$0.00**.

### Step 3: Set a $1.00 Early Warning Budget Alert (Recommended)
1. In the navigation menu, go to **Billing & Cost Management** &rarr; **Budgets**.
2. Click **Create Budget**.
3. Set the target to your root compartment.
4. Set the budget amount to **$1.00**.
5. Set an alert rule: If forecast or actual spending reaches **$0.01 (1%)**, send an alert to your email.
6. If any paid feature is ever accidentally clicked in the future, Oracle will immediately email you before a significant bill can accumulate.

---

## 6. How to Pause and Resume the Project at Will

Depending on whether you want to temporarily suspend traffic or completely power down the virtual machine, choose one of the two methods below:

### Method A: Pause Only the Chat Application (Quick & Safe)
* **What it does:** Freezes Daphne so no WebSockets or HTTP traffic can enter the app. Keeps the Linux VM running with its network interface and IP intact.
* **When to use:** When you are taking a break from coding and don't want anyone connecting, but don't want to power down Linux.

**To Pause:**
```powershell
ssh yb-chatapp "sudo systemctl stop chat-app"
```

**To Resume:**
```powershell
ssh yb-chatapp "sudo systemctl start chat-app"
```

---

### Method B: Power Down the Whole Virtual Machine (Complete Shutdown)
* **What it does:** Shuts down the Linux OS completely. Consumes 0 OCPUs and 0 RAM hours.
* **When to use:** When you won't be working on the project for weeks or months.

#### Option 1: Stop from PowerShell Terminal:
```powershell
ssh yb-chatapp "sudo poweroff"
```

#### Option 2: Stop from Oracle Cloud Console:
1. Go to **Compute** &rarr; **Instances**.
2. Click your instance name (`YB-ChatApp`).
3. Click the **Stop** button and select **Stop instance** (graceful shutdown).

#### How to Start It Back Up:
1. Log into [cloud.oracle.com](https://cloud.oracle.com).
2. Go to **Compute** &rarr; **Instances** &rarr; Click your instance.
3. Click **Start**.
4. Once the status shows green (**Running**), Daphne, Redis, and Nginx will start automatically.

> [!WARNING]
> **Check Your Public IP After a Full Shutdown:**
> If your VM uses an **Ephemeral** Public IP, stopping and restarting the instance in Oracle Cloud may assign a new public IP address. If the IP address changes:
> 1. Note the new public IP from the Oracle Console.
> 2. Open your [DuckDNS dashboard](https://www.duckdns.org) and update the IP for `ybchatapp.duckdns.org`.
> 3. Update the IP in your local `~/.ssh/config` file if needed.

---

## 7. Public Repository Security Checklist

When publishing code to GitHub, ensure no sensitive secrets are committed:

| Item | Status | Action Required |
| :--- | :--- | :--- |
| **SSH Private Keys (`.key`, `.pem`)** | ✅ **Protected** | Private keys are stored locally on your PC and excluded via `.gitignore`. Never push `.key` files. |
| **DuckDNS Account Token** | ⚠️ **Redacted** | Any real token previously written in logs was replaced with `<YOUR_DUCKDNS_TOKEN>`. As a best practice, log in to [DuckDNS](https://www.duckdns.org) and click **regenerate token**. |
| **Django `SECRET_KEY`** | ✅ **Safe for Learning** | Uses fallback for development; for production apps with real user data, set `DJANGO_SECRET_KEY` via environment variables. |
| **Server Public IP (`130.61.9.37`)** | ℹ️ **Public by Design** | Your domain points to it publicly. Access is secured by SSH key-only authentication (`PasswordAuthentication no`). |
