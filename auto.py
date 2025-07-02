import time
from playwright.sync_api import sync_playwright, TimeoutError

# --- 请在这里配置您的面板信息 / Please configure your panel information here ---
PANEL_URL = "Your_URL"  # 您的面板URL（包含安全入口） / Your panel URL (including the security entrance)
USERNAME = "Your_Username"                                 # 您的面板登录用户名 / Your panel login username
PASSWORD = "Your_Password"                            # 您的面板登录密码 / Your panel login password
# ------------------------------------

def set_pagination_to_100(page):
    """
    【已根据最新HTML修正】将网站列表的分页设置为100条/页。
    [Corrected according to the latest HTML] Sets the website list pagination to 100 items/page.
    """
    print("\n--- 正在设置分页为100条/页 / Setting pagination to 100 items/page ---")
    try:
        # 步骤 1: 点击分页大小选择器以展开下拉列表 / Step 1: Click the pagination size selector to expand the dropdown list
        pagination_trigger_selector = ".el-pagination__sizes .el-input"
        print(f"定位分页触发器 / Locating pagination trigger: {pagination_trigger_selector}")
        page.locator(pagination_trigger_selector).click()
        print("已点击分页选择器。/ Clicked the pagination selector.")

        # 步骤 2: 等待并点击“100条/页”选项 / Step 2: Wait for and click the "100条/页" (100 items/page) option
        option_locator = page.locator('li.el-select-dropdown__item:has-text("100条/页")')
        option_locator.wait_for(state="visible", timeout=5000)
        option_locator.click()
        print("已选择 '100条/页'。/ Selected '100 items/page'.")

        # 步骤 3: 等待表格刷新 / Step 3: Wait for the table to refresh
        print("等待表格因分页设置而刷新... / Waiting for the table to refresh due to pagination change...")
        time.sleep(3) # 等待3秒让列表重新加载 / Wait 3 seconds for the list to reload
        print("分页设置完成。/ Pagination setup complete.")
    except Exception as e:
        print(f"警告：修改分页失败，将使用默认分页。错误: {e} / Warning: Failed to change pagination, will use default. Error: {e}")
        pass

def run(playwright):
    """
    主执行函数 / Main execution function
    """
    browser = playwright.chromium.launch(
        headless=False,
        slow_mo=50,
        args=['--start-maximized']
    )
    context = browser.new_context(
        ignore_https_errors=True,
        no_viewport=True
    )
    page = context.new_page()

    try:
        # --- 1. 登录与导航流程 / 1. Login and Navigation Flow ---
        print("正在尝试登录面板... / Attempting to log into the panel...")
        page.goto(PANEL_URL, timeout=30000)
        
        print("等待登录页面加载... / Waiting for the login page to load...")
        page.wait_for_selector('input[name="username"]', timeout=20000)
        print("已到达登录页面，正在输入凭据... / Reached login page, entering credentials...")
        page.fill('input[name="username"]', USERNAME)
        page.fill('input[name="password"]', PASSWORD)
        
        login_button_selector = 'button.login-submit'
        page.click(login_button_selector)
        
        website_menu_selector = 'a[href="/site"]:has-text("网站")'
        print("等待登录成功并进入面板首页... / Waiting for successful login and panel homepage...")
        page.wait_for_selector(website_menu_selector, timeout=30000)
        print("已确认进入面板首页。/ Confirmed entry to the panel homepage.")

        print("正在点击左侧'网站'菜单... / Clicking the '网站' (Website) menu on the left...")
        page.locator(website_menu_selector).click()

        add_site_button_selector = 'button:has-text("添加站点")'
        print("等待网站列表页面加载... / Waiting for the website list page to load...")
        page.wait_for_selector(add_site_button_selector, timeout=20000)
        print("已成功进入网站列表页面。/ Successfully entered the website list page.")

        # --- 2. 【仅执行一次】设置分页为100条/页 / 2. [Execute Once] Set pagination to 100 items/page ---
        set_pagination_to_100(page)

        # --- 3. SSL证书续签循环流程 / 3. SSL Certificate Renewal Loop ---
        while True:
            main_rows = page.locator('.el-table__body-wrapper .el-table__row').all()
            
            target_index = -1
            print("\n正在扫描网站列表，查找'已过期'或'未部署'的证书... / Scanning website list for '已过期' (Expired) or '未部署' (Not Deployed) certificates...")
            for i, row in enumerate(main_rows):
                expired_selector = 'span.text-danger:has-text("已过期")'
                undeployed_selector = 'span[class*="text-[#f0ad4e]"]:has-text("未部署")'
                
                combined_selector = f"{expired_selector}, {undeployed_selector}"
                target_locator = row.locator(combined_selector)
                
                if target_locator.count() > 0:
                    status_text = target_locator.inner_text()
                    print(f"在第 {i + 1} 行发现状态为 '{status_text.strip()}' 的站点。/ Found a site with status '{status_text.strip()}' on row {i + 1}.")
                    target_index = i
                    break
            
            if target_index == -1:
                print("\n页面上已无'已过期'或'未部署'的SSL证书。任务完成！/ No more 'Expired' or 'Not Deployed' SSL certificates on the page. Task complete!")
                break
            
            expired_index = target_index

            print(f"\n--- 发现第 {expired_index + 1} 行证书需要续签，开始处理 / Found certificate on row {expired_index + 1} needs renewal, starting process ---")
            
            domain_name = main_rows[expired_index].locator('td:nth-child(2)').inner_text()
            print(f"目标网站 / Target website: {domain_name.strip()}")

            fixed_rows = page.locator('.el-table__fixed-right .el-table__row').all()
            
            if expired_index < len(fixed_rows):
                target_row_for_click = fixed_rows[expired_index]
                print("点击 '设置'... / Clicking '设置' (Settings)...")
                target_row_for_click.locator('span[title="设置"]').click()
            else:
                print(f"错误：主表格和固定列的行数不匹配，无法点击第 {expired_index + 1} 行的设置按钮。/ Error: Mismatch between main table and fixed columns row count, cannot click settings button on row {expired_index + 1}.")
                break

            # --- 弹窗内操作 / Operations within the dialog box ---
            ssl_tab_selector = '#tab-ssl'
            page.wait_for_selector(ssl_tab_selector, timeout=10000)
            page.locator(ssl_tab_selector).click()
            
            le_tab_selector = 'div:has-text("Let\'s Encrypt")'
            page.wait_for_selector(le_tab_selector, timeout=10000)
            page.locator(le_tab_selector).last.click()
            time.sleep(5)
            
            select_all_label_selector = 'label:has-text("全选")'
            page.wait_for_selector(select_all_label_selector, timeout=10000)
            page.locator(select_all_label_selector).click()
            
            apply_button = page.locator('form[data-v-9b09eae2]').locator('button:has-text("申请证书")')
            print("点击 '申请证书' 并等待验证完成... / Clicking '申请证书' (Apply for Certificate) and waiting for verification...")
            apply_button.click()
            
            try:
                success_text_locator = page.locator('.el-dialog').get_by_text('正在发送CSR')
                success_text_locator.wait_for(timeout=180000)
                print("证书验证成功! / Certificate verification successful!")
            except TimeoutError:
                print(f"警告: 等待'验证成功!'消息超时。可能续签失败或网络缓慢。/ Warning: Timed out waiting for 'verification successful!' message. Renewal may have failed or the network is slow.")
            
            print("等待10秒后关闭设置弹窗... / Waiting 10 seconds before closing the settings dialog...")
            time.sleep(10)
            
            main_dialog = page.locator('.el-dialog.bt-popup')
            main_dialog.locator('.close-popup-btn').click()
            print("设置弹窗已关闭。/ Settings dialog closed.")
            
            # --- 刷新页面以获取最新列表状态 / Refresh the page to get the latest list status ---
            print("\n正在刷新页面以确保状态更新... / Refreshing page to ensure status is updated...")
            page.reload(wait_until="domcontentloaded")
            
            print("等待页面元素加载... / Waiting for page elements to load...")
            page.wait_for_selector(add_site_button_selector, timeout=20000) 
            print("页面已刷新。继续检查下一个证书... / Page refreshed. Continuing to check the next certificate...")
            time.sleep(10)
    except Exception as e:
        print(f"\n脚本执行过程中发生错误: {e} / An error occurred during script execution: {e}")
        page.screenshot(path="error_screenshot.png")
        print("已保存错误截图到 error_screenshot.png / Error screenshot saved to error_screenshot.png")
    
    finally:
        print("任务结束，关闭浏览器。/ Task finished, closing browser.")
        browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)