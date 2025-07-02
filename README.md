# BaoTa-SSL-Renewer (宝塔SSL续签器)

**A Playwright-driven automation tool for intelligently managing and renewing Let's Encrypt SSL certificates specifically on the BT-Panel (宝塔面板).**

_一个由 Playwright 驱动的、专门为宝塔面板量身打造的 Let's Encrypt SSL 证书智能管理与续订自动化工具。_

[![Target Panel](https://img.shields.io/badge/Panel-BT%20Panel-green.svg)](https://www.bt.cn/)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 概览 (Overview)

**BaoTa-SSL-Renewer** 旨在解决宝塔面板用户在管理大量站点时，手动续订 Let's Encrypt 证书的痛点。尽管宝塔面板内置了自动续签任务，但在某些情况下（如DNS验证失败、配置更改等），证书仍可能过期或部署失败。本项目通过模拟用户在浏览器中的真实操作，自动登录您的宝塔面板，扫描所有网站，精准识别出“已过期”或“未部署”的SSL证书，并自动执行申请和部署流程。它为您提供了一道额外的、可靠的自动化防线，确保您的所有站点始终处于 HTTPS 的安全保护之下。

**BaoTa-SSL-Renewer** is designed to address the pain points of manual Let's Encrypt certificate renewal for BT-Panel users managing multiple websites. Although BT-Panel has a built-in auto-renewal task, certificates can still expire or fail to deploy under certain circumstances (e.g., DNS verification failures, configuration changes). This project emulates real user actions in a browser to automatically log into your BT-Panel, scan all websites, pinpoint "Expired" or "Not Deployed" SSL certificates, and execute the application and deployment process. It provides an additional, reliable layer of automation to ensure all your sites remain securely under HTTPS protection.

## 核心特性 (Core Features)

- **专为宝塔设计 (Tailored for BT-Panel):** 所有的选择器和操作流程均根据宝塔面板的前端界面进行优化，确保高兼容性。
- **智能状态检测 (Intelligent Status Detection):** 自动扫描网站列表，精准识别宝塔面板中特有的“已过期”或“未部署”证书状态。
- **端到端自动化 (End-to-End Automation):** 从登录面板到申请证书，全程无需人工干预。
- **无头环境执行 (Headless Environment Execution):** 完美结合 `xvfb-run`，使其可以在没有图形界面的 Linux 服务器上通过 Cron 周期性静默运行。
- **详尽日志与截图 (Robust Logging & Screenshots):** 记录关键执行步骤，并在发生错误时自动截取当前屏幕，极大地方便了远程调试和问题定位。
- **简易配置 (Simple Configuration):** 只需修改脚本 `auto.py` 顶部的几个变量，即可快速部署到您自己的宝塔面板环境。

## 在 Linux 服务器上部署 (Deployment on Linux Server)

请遵循以下步骤在您的宝塔服务器上部署并运行本项目。

### 先决条件 (Prerequisites)

- 一台已安装**宝塔面板**的 Linux 服务器 (推荐 Ubuntu 20.04+ 或 CentOS 7+)。
- 已安装 Git。
- Python 3.8 或更高版本。
- `pip` 包管理器。
- `xvfb` (用于在无图形界面的服务器上创建虚拟显示环境)。

### 部署步骤 (Deployment Steps)

#### 步骤 1: 克隆仓库 (Clone the Repository)
通过宝塔面板的终端或SSH登录服务器，执行以下命令：
```bash
git clone https://github.com/your-username/BaoTa-SSL-Renewer.git
cd BaoTa-SSL-Renewer
```
> **提示:** 请将 `your-username` 替换为你的 GitHub 用户名。

#### 步骤 2: 安装系统依赖 (Install System Dependencies)
`xvfb` 对于在服务器上运行 Playwright 至关重要。
```bash
# 对于 Ubuntu/Debian 系统
# For Ubuntu/Debian systems
sudo apt-get update
sudo apt-get install -y python3-pip xvfb

# 对于 CentOS/RHEL 系统
# For CentOS/RHEL systems
sudo yum install -y python3-pip xorg-x11-server-Xvfb
```

#### 步骤 3: 设置 Python 环境 (Set Up Python Environment)
强烈建议使用虚拟环境来隔离项目依赖。
```bash
# 创建虚拟环境
# Create a virtual environment
python3 -m venv venv

# 激活虚拟环境
# Activate the virtual environment
source venv/bin/activate

# 安装所需的Python包
# Install required Python packages
pip install -r requirements.txt

# 安装Playwright所需的浏览器核心
# Install browser cores required by Playwright
playwright install chromium
```
> **注意:** 如果您想退出虚拟环境，可以运行 `deactivate` 命令。
> **Note:** To exit the virtual environment, run the `deactivate` command.

#### 步骤 4: 配置脚本 (Configure the Script)
使用您喜欢的文本编辑器 (如 `nano` 或 `vim`) 打开 `auto.py` 文件，并修改顶部的配置信息，填入您的宝塔面板信息：
```bash
# 编辑 auto.py 文件
# Edit the auto.py file
nano auto.py
```
修改以下部分：
```python
# --- 请在这里配置您的面板信息 / Please configure your panel information here ---
PANEL_URL = "https://your-panel-ip:port/security_entrance"  # 您的宝塔面板URL（必须包含安全入口）/ Your BT-Panel URL (must include security entrance)
USERNAME = "your_bt_username"                           # 您的面板登录用户名 / Your panel login username
PASSWORD = "your_bt_password"                           # 您的面板登录密码 / Your panel login password
# ------------------------------------
```
请确保 `PANEL_URL` 是完整的、可从服务器内部访问的地址。

#### 步骤 5: 手动测试运行 (Manual Test Run)
在正式部署为定时任务前，先手动执行一次以确保一切正常。
```bash
xvfb-run python3 auto.py
```
观察终端输出的日志。如果一切顺利，它会扫描并处理证书。如果出现错误，请根据日志和项目目录中生成的 `error_screenshot.png` 进行排查。

#### 步骤 6: 使用 Cron 设置定时任务 (Automate with Cron)
这是实现“无人值守”的最后一步。
1.  打开 `crontab` 编辑器：
    ```bash
    crontab -e
    ```
    (如果是首次使用，选择一个编辑器，如 `nano`)

2.  在文件末尾添加以下一行，以实现每3小时执行一次：
    ```crontab
    # 每3小时执行一次 BaoTa-SSL-Renewer 脚本，检查并续订宝塔面板的SSL证书
    # Run the BaoTa-SSL-Renewer script every 3 hours to check and renew SSL certificates on BT-Panel
    0 */3 * * * /usr/bin/xvfb-run /path/to/your/project/BaoTa-SSL-Renewer/venv/bin/python3 /path/to/your/project/BaoTa-SSL-Renewer/auto.py >> /path/to/your/project/BaoTa-SSL-Renewer/cron.log 2>&1
    ```
    **重要提示 (IMPORTANT):**
    - 请将 `/path/to/your/project/BaoTa-SSL-Renewer/` 替换为您项目的**绝对路径**。您可以通过在项目目录中运行 `pwd` 命令来获取。
      _Please replace `/path/to/your/project/BaoTa-SSL-Renewer/` with the **absolute path** to your project. You can get it by running the `pwd` command in the project directory._
    - 我们使用了虚拟环境中的 Python 解释器 (`venv/bin/python3`)，这是隔离依赖的最佳实践。
      _We use the Python interpreter from the virtual environment (`venv/bin/python3`), which is the best practice for dependency isolation._

3.  保存并退出编辑器。定时任务将自动生效。

## 贡献 (Contributing)
宝塔面板的前端可能会更新，导致选择器失效。如果您发现了这类问题并修复了它，或者有任何功能改进的想法，欢迎提交 Pull Request 或创建 Issue。

Contributions are welcome! If you find that BT-Panel's frontend has been updated, causing selectors to fail, or if you have any ideas for improvements, feel free to submit a Pull Request or create an Issue.

## 致谢 (Acknowledgements)

特别感谢**北京市第三十五中学**在其 **STEAM 活动周**期间提供的宝贵时间和机会，使得本项目的开发成为可能。这段时间的专注研究与实践，是 `BaoTa-SSL-Renewer` 诞生的基石。

Special thanks to **Beijing No. 35 High School** for providing the invaluable time and opportunity during its **STEAM Week**. This period of focused research and practice was the cornerstone for the creation of `BaoTa-SSL-Renewer`.

## 许可证 (License)
本项目采用 [MIT License](https://opensource.org/licenses/MIT) 授权。
This project is licensed under the MIT License.
