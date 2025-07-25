import time
from playwright.sync_api import sync_playwright, TimeoutError

# --- 请在这里配置您的面板信息 / Please configure your panel information here ---
# 填写您的面板URL（包含安全入口）、用户名和密码
# Fill in your panel URL (including the security entrance), username, and password
PANEL_URL = "Your_Panel_URL"      # 例如 / e.g., "https://1.2.3.4:5678/abcdefg"
USERNAME = "Your_Username"        # 您的面板登录用户名 / Your panel login username
PASSWORD = "Your_Password"        # 您的面板登录密码 / Your panel login password
# ------------------------------------

def set_pagination_to_100(page):
    """
    【仅执行一次】将网站列表的分页设置为100条/页。
    [Execute Once] Sets the website list pagination to 100 items/page.
    """
    print("\n--- 正在设置分页为100条/页 / Setting pagination to 100 items/page ---")
    try:
        # 点击分页大小选择器
        page.locator(".el-pagination__sizes .el-select__wrapper").click()
        # 选择"100条/页"选项
        page.get_by_role("option", name="100条/页").click()
        # 等待网络空闲以确保表格刷新
        page.wait_for_load_state("networkidle", timeout=10000)
        print("分页设置完成。/ Pagination setup complete.")
    except Exception as e:
        print(f"警告：修改分页失败，将使用默认分页。错误: {e} / Warning: Failed to change pagination, will use default. Error: {e}")
        pass

def run(playwright):
    """
    主执行函数 / Main execution function
    """
    browser = playwright.chromium.launch(
        headless=False,      # 设置为 True 可在后台运行 / Set to True to run in the background
        slow_mo=50,
        args=['--start-maximized']
    )
    context = browser.new_context(
        ignore_https_errors=True, # 忽略HTTPS证书错误 / Ignore HTTPS certificate errors
        no_viewport=True
    )
    page = context.new_page()

    try:
        # --- 1. 登录与导航 / 1. Login and Navigation ---
        print("正在尝试登录面板... / Attempting to log into the panel...")
        page.goto(PANEL_URL, timeout=60000)
        
        page.wait_for_selector('input[name="username"]', timeout=30000)
        print("输入凭据... / Entering credentials...")
        page.fill('input[name="username"]', USERNAME)
        page.fill('input[name="password"]', PASSWORD)
        page.click('button.login-submit')
        
        print("登录成功，正在导航至网站列表... / Login successful, navigating to website list...")
        website_menu_selector = 'li.menu-item.menu-site'
        page.wait_for_selector(website_menu_selector, timeout=30000)
        page.locator(website_menu_selector).click()

        add_site_button_selector = 'button:has-text("添加站点")'
        page.wait_for_selector(add_site_button_selector, timeout=20000)
        print("已进入网站列表页面。/ Reached the website list page.")

        # --- 2. 设置分页 / 2. Set Pagination ---
        set_pagination_to_100(page)

        # --- 3. SSL证书续签循环 / 3. SSL Certificate Renewal Loop ---
        while True:
            # 等待网站列表加载完成
            page.wait_for_selector('.el-table__body-wrapper .el-table__body tr.el-table__row', timeout=15000)
            all_rows = page.locator('.el-table__body-wrapper .el-table__body tr.el-table__row').all()
            if not all_rows:
                print("未找到任何网站。/ No websites found.")
                break
            
            target_index = -1
            print(f"\n正在扫描 {len(all_rows)} 个网站，查找需要续签的证书... / Scanning {len(all_rows)} websites for certificates to renew...")
            
            # 查找第一个“已过期”或“未部署”的证书
            # Find the first 'Expired' or 'Not Deployed' certificate
            for i, row in enumerate(all_rows):
                if row.get_by_text("已过期", exact=True).count() > 0 or row.get_by_text("未部署", exact=True).count() > 0:
                    status_text = row.locator('td').nth(9).inner_text().strip()
                    print(f"发现需要处理的站点: 状态为 '{status_text}'。 / Found a site to process: status is '{status_text}'.")
                    target_index = i
                    break
            
            if target_index == -1:
                print("\n所有证书状态正常，任务完成！/ All certificate statuses are normal. Task complete!")
                break
            
            print(f"--- 开始处理第 {target_index + 1} 行的证书 ---")
            
            domain_name = all_rows[target_index].locator('td:nth-child(2) span.bt-link').first.inner_text()
            print(f"目标网站 / Target website: {domain_name.strip()}")

            print("点击 '设置' / Clicking 'Settings'...")
            # 兼容固定列和非固定列的“设置”按钮
            # Compatible with 'Settings' buttons in both fixed and non-fixed columns
            try:
                fixed_settings_button = page.locator('.el-table__fixed-right .el-table__row').nth(target_index).get_by_text('设置', exact=True)
                fixed_settings_button.click()
            except Exception:
                all_rows[target_index].get_by_text('设置', exact=True).click()

            # --- 弹窗内操作 / Operations within the dialog ---
            print("切换到SSL设置 / Switching to SSL settings...")
            page.locator('#tab-ssl').click()
            page.locator('.el-tabs__item:has-text("Let\'s Encrypt")').click()
            time.sleep(1)

            print("开始申请流程：点击'申请证书' / Starting application: Clicking 'Apply Certificate'...")
            page.locator('#pane-letsEncryptList button:has-text("申请证书")').click()

            print("在新弹窗中全选域名 / Selecting all domains in the new dialog...")
            page.locator('.el-dialog .el-checkbox:has-text("全选")').click()
            time.sleep(0.5)

            print("提交申请 / Submitting application...")
            page.locator('div.el-dialog').last.get_by_role("button", name="申请证书").click()
            
            print("等待证书部署... (最长等待180秒) / Waiting for certificate deployment... (max 180s)")
            try:
                # 等待UI上出现“已部署”的标志
                page.locator('#tab-currentCertInfo:has-text("[已部署SSL]")').wait_for(timeout=180000)
                print("证书申请并部署成功！/ Certificate applied and deployed successfully!")
            except TimeoutError:
                print(f"警告：180秒内未检测到成功状态。续签可能失败或仍在后台进行。/ Warning: Success status not detected within 180s. Renewal may have failed or is still in progress.")
            
            time.sleep(3)
            print("\n刷新页面以更新列表... / Refreshing page to update the list...")
            page.reload(wait_until="domcontentloaded")
            
            page.wait_for_selector(add_site_button_selector, timeout=30000) 
            print("页面已刷新，继续检查下一个... / Page refreshed, continuing to the next...")
            time.sleep(3)
            
    except Exception as e:
        print(f"\n脚本执行过程中发生错误: {e} / An error occurred during script execution: {e}")
        try:
            page.screenshot(path="error_screenshot.png", full_page=True)
            print("已保存错误截图到 error_screenshot.png / Error screenshot saved to error_screenshot.png")
        except Exception as ss_e:
            print(f"保存截图失败 / Failed to save screenshot: {ss_e}")
    
    finally:
        print("任务结束，关闭浏览器。/ Task finished, closing browser.")
        browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
