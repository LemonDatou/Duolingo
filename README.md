# 🦉 Duolingo Automation Scripts / 多邻国自动化脚本合集

🌍 **Choose your language / 选择语言:**
* [中文版本](#中文版本)
* [English Version](#english-version)

---

## <a id="中文版本"></a> 中文版本

一组用于多邻国（Duolingo）的自动化脚本，主要功能包括自动完成课程和刷经验值（XP）。

### 🚀 快速使用
* **自动答题**：如果需要全自动完成当前单元，请使用 `duolingo-helper.js`。
* **辅助答题**：如果只需要在答题时显示当前问题的答案，请使用 `show-answer.js`。
* **即时 XP**：如果需要立刻获得大量 XP，请使用 `duolingo-xp.js`。
* **远程部署**：如果需要部署到服务器运行，请使用 `server` 目录中的 Python 脚本。

> **⚠️ 免责声明**
> 
> 请注意，**刷 XP 脚本（`duolingo-xp.py` 和 `duolingo-xp.js`）**调用了第三方 API (`api.duolingopro.net`)，这会将您的个人账户鉴权信息（JWT 令牌）发送到其服务器。该第三方服务的安全性与本项目无关，请自行承担风险。**其他脚本均运行在本地环境中，不会向任何第三方发送数据。**

---

### 🛠️ 浏览器脚本工具 (JS Utilities)
这些脚本可以直接在浏览器中使用，无需安装 Python 环境。

#### **如何使用：**
1. **控制台法**：在多邻国答题页面按下 `F12` 或 `Ctrl+Shift+I` 打开开发者工具，切换到 `Console` 选项卡，粘贴代码并回车。
2. **书签法 (仅限 `show-answer.js`)**：新建浏览器书签，在 URL 处粘贴以 `javascript:` 开头的脚本代码。点击书签即可运行。

* **`duolingo-helper.js`**: 全功能自动解题脚本。注入后会创建一个包含“开始/停止”按钮的控制面板。它能从 React 组件中提取正确答案，自动完成点击、输入等操作。
<img src="https://github.com/user-attachments/assets/b5e41e60-dbef-4ebc-8557-4dac8e78d282" alt="helper-ui" width="600">

* **`show-answer.js`**: 辅助答题脚本。运行时会显示当前题目的正确答案，并将其显示在屏幕中央的浮层上，适合辅助手动答题。

* **`duolingo-xp.js`**: 一键获取 XP 脚本。它从 Cookie 中提取 JWT 凭证并发送至第三方服务，立刻获得大量 XP（默认1000），风险自行承担。

---

### 🤖 服务端 Python 脚本 (Server Scripts)
适用于需要自动化循环运行或部署在 Linux 服务器上的场景。

#### 🤖 `duolingo.py` (自动刷课)
通过 Playwright 控制无头浏览器，全自动登录并刷课。脚本会提取并保存账户的 JWT 凭证供刷分脚本使用。

**🔑 如何使用 `duolingo_state.json` (无头服务器必备)**
1. **本地提取**: 在有界面的本地电脑运行 Playwright 登录，保存上下文状态为 `duolingo_state.json`。
2. **上传**: 将该文件上传至服务器与 `duolingo.py` 同级目录。
3. **自动注入**: 脚本将自动检测并注入 Cookie 和 LocalStorage，绕过登录验证。

#### 🚀 `duolingo-xp.py` (自动刷 XP)
读取 `duolingo.py` 保存的 JWT，调用第三方 API 批量增加 XP。

#### 🌐 `api_server.py` (本地服务中心)
Flask Web 服务器，提供 `/run-lesson` 和 `/run-xp` 接口。通过锁机制确保同一时间只有一个任务执行，防止服务器资源过载。

<br>

---

## <a id="english-version"></a> English Version

A collection of scripts for automating Duolingo tasks, including completing lessons and farming XP.

### 🚀 Quick Start
* **Auto-Solve**: To fully automate the current unit, use `duolingo-helper.js`.
* **Answer Helper**: To display answers while manually solving, use `show-answer.js`.
* **Instant XP**: To gain XP immediately, use `duolingo-xp.js`.
* **Server Deployment**: To run 24/7 on a remote server, use the Python scripts in the `server` directory.
* **Stand-alone**: All scripts in this project can be run independently.

> **⚠️ Disclaimer**
> 
> Please note that the **XP farming scripts (`duolingo-xp.py` and `duolingo-xp.js`)** utilize a third-party API (`api.duolingopro.net`) and will send your personal account authentication (JWT token) to their server. The security of this third-party service is not related to this project; use it at your own risk. **All other scripts run entirely locally on your machine and do not send data to any third party.**

---

### 🛠️ JavaScript Utilities
These scripts can be used directly in your browser without a Python environment.

#### **How to Use:**
1. **Console Method**: Press `F12` or `Ctrl+Shift+I` on the Duolingo lesson page, go to the `Console` tab, paste the code, and press Enter.
2. **Bookmarklet Method (For `show-answer.js`)**: Create a new bookmark and paste the script (starting with `javascript:`) into the URL field. Click the bookmark to run.

* **`duolingo-helper.js`**: A comprehensive auto-solver. It creates a UI panel with start/stop buttons. It extracts answers from React components and performs clicking/typing actions automatically.
<img src="https://github.com/user-attachments/assets/b5e41e60-dbef-4ebc-8557-4dac8e78d282" alt="helper-ui" width="600">

* **`show-answer.js`**: A bookmarklet-style script that extracts the correct answer and displays it in a central overlay. Perfect for manual assistance.

* **`duolingo-xp.js`**: A browser alternative to `duolingo-xp.py` that extracts JWT from cookies and requests XP via the API.

---

### 🤖 Server Python Scripts
Best for automated loops or deployment on Linux servers.

#### 🤖 `duolingo.py` (Auto-Lesson)
Uses Playwright to control a headless browser for auto-solving lessons. It extracts and saves the JWT token for the XP script.

**🔑 How to use `duolingo_state.json` (Required for Headless Servers)**
1. **Local Extraction**: Run Playwright on a local PC with a GUI to log in, then save the state as `duolingo_state.json`.
2. **Upload**: Place this file in the same directory as `duolingo.py` on your server.
3. **Auto-Injection**: The script will automatically detect the file and inject Cookies/LocalStorage to bypass login.

#### 🚀 `duolingo-xp.py` (XP Farmer)
Reads the saved JWT and requests XP through a third-party API.

#### 🌐 `api_server.py` (Local API)
A Flask server providing `/run-lesson` and `/run-xp` endpoints. Features a lock mechanism to prevent resource overload by ensuring only one task runs at a time.