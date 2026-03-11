# 🦉 Duolingo Automation Scripts / 多邻国自动化脚本合集

🌍 **Choose your language / 选择语言:**
* [English Version](#english-version)
* [中文版本](#中文版本)

---

## <a id="english-version"></a> English Version

A collection of scripts for automating Duolingo tasks, including completing lessons and farming XP.

> **⚠️ Disclaimer**
> 
> This project contains scripts that use a third-party API (`api.duolingopro.net`) and send your personal account authentication (JWT token) to its server. The functionality and security of this third-party service are not related to or guaranteed by this project. **Use at your own risk.**

### 📂 File Descriptions

#### 🤖 `duolingo.py` (Auto-Lesson)
The main script for automatically completing Duolingo lessons. It uses Playwright to control a headless browser, logs in, navigates to a specific lesson, and injects a JavaScript payload to solve challenges automatically. It also extracts the user's JWT token for other scripts to use and can be configured to run for a specific number of loops.

**🔑 How to use `duolingo_state.json` (Required for Headless Server Deployment)**
If you are running this script on a headless server (e.g., Linux without a GUI), you cannot log in manually. You must use a state file to bypass the login phase:
1. **Local Extraction:** On your local machine (Windows/Mac), run a Playwright script with `headless=False` to log into Duolingo. Save the browser context state to a file named `duolingo_state.json`.
2. **Upload:** Place `duolingo_state.json` in the same directory as `duolingo.py` on your server.
3. **Auto-Injection:** When `duolingo.py` runs, it will detect this file, automatically inject the Cookies and LocalStorage, and bypass the login verification seamlessly.

#### 🚀 `duolingo-xp.py` (XP Farmer)
A Python script for farming XP points. It reads the JWT token saved by `duolingo.py` and sends a request to a third-party API (`api.duolingopro.net`) to add a specified amount of XP to the account.

#### 🌐 `api_server.py` (Local API)
A local Flask web server that provides an API to trigger the `duolingo.py` and `duolingo-xp.py` scripts. It features two endpoints: `/run-lesson` to start the lesson bot and `/run-xp` to start the XP farming script. A lock mechanism ensures that only one task can run at a time.

#### 🛠️ JavaScript Utilities
* **`duolingo-helper.js`**: A comprehensive JavaScript script designed to be injected into a Duolingo lesson page. It creates a UI panel with start/stop buttons for the auto-solving process. It extracts correct answers from the page's React components and automatically performs the necessary actions (clicking, typing) to solve the challenges. The content of this file is embedded within `duolingo.py`.![image](https://github.com/user-attachments/assets/b5e41e60-dbef-4ebc-8557-4dac8e78d282")
* **`duolingo-xp.js`**: A JavaScript script intended to be run in the browser's developer console. It extracts the JWT token from the browser's cookies and makes a POST request to the `api.duolingopro.net` service to request XP, similar to the `duolingo-xp.py` script. It serves as a manual alternative.
* **`show-answer.js`**: A bookmarklet-style JavaScript snippet. When executed on a Duolingo challenge page, it extracts the correct answer from the React component data and displays it prominently in an overlay on the screen. It is a tool for manually revealing the answer to a single question.

<br>

---

## <a id="中文版本"></a> 中文版本

一组用于多邻国（Duolingo）的自动化脚本，主要功能包括自动完成课程和刷经验值（XP）。

> **⚠️ 免责声明**
> 
> 本项目包含调用第三方 API (`api.duolingopro.net`) 的脚本，这会将您的个人账户鉴权信息（JWT 令牌）发送到其服务器。该第三方服务的功能和安全性与本项目无关，本项目不提供任何保证。**请自行承担使用风险。**

### 📂 文件说明

#### 🤖 `duolingo.py` (自动刷课)
这是核心的自动刷课脚本。它通过 Playwright 库控制一个无头浏览器，自动登录多邻国、进入指定课程，并注入JS代码以全自动答题。该脚本还会提取并保存账户的JWT凭证，供其他脚本使用。可以配置循环运行的次数。

**🔑 如何使用 `duolingo_state.json` (无头服务器部署必备)**
如果您在无头服务器（如无图形界面的 Linux）上运行此脚本，由于无法手动登录，您必须通过凭证文件注入登录状态：
1. **本地提取:** 在本地电脑上，以有界面的方式运行 Playwright 登录多邻国，并将浏览器上下文状态导出为 `duolingo_state.json`。
2. **上传至服务器:** 将生成的 `duolingo_state.json` 文件上传至服务器，与 `duolingo.py` 放在同一目录下。
3. **自动注入:** 脚本运行时会自动检测该文件，将 Cookie 和 LocalStorage 注入持久化目录中，完美绕过登录验证。

#### 🚀 `duolingo-xp.py` (自动刷分)
一个用于刷经验值（XP）的Python脚本。它会读取由 `duolingo.py` 保存的JWT凭证，然后调用一个第三方API (`api.duolingopro.net`) 来为账户增加指定数量的XP。

#### 🌐 `api_server.py` (本地服务中心)
一个本地 Flask Web 服务器。它提供API接口来触发 `duolingo.py`（刷课）和 `duolingo-xp.py`（刷分）脚本。它包含两个接口：`/run-lesson` 用于开始刷课，`/run-xp` 用于开始刷XP。通过锁机制确保同一时间只有一个任务在执行，保护服务器资源。

#### 🛠️ 浏览器脚本工具
* **`duolingo-helper.js`**: 一个功能全面的JS脚本，设计用于注入到多邻国的答题页面。它会创建一个包含“开始/停止”按钮的控制面板。它通过从页面的React组件中提取正确答案，自动完成点击、输入等操作来解题。此文件的内容被直接嵌入在 `duolingo.py` 脚本中。![image](https://github.com/user-attachments/assets/b5e41e60-dbef-4ebc-8557-4dac8e78d282")
* **`duolingo-xp.js`**: 一个用于在浏览器开发者控制台手动执行的JS脚本。它从浏览器的Cookie中提取JWT凭证，然后向 `api.duolingopro.net` 服务发送请求来增加XP，功能与 `duolingo-xp.py` 脚本类似。可作为手动刷分的备用方案。
* **`show-answer.js`**: 一个书签脚本（bookmarklet）。在多邻国的答题页面运行时，它会从React组件中提取当前题目的正确答案，并将其显示在一个屏幕中央的浮层上。这是一个用于手动显示单题答案的工具。
