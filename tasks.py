from robocorp.tasks import task
from robocorp.workitems import ApplicationException
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
import time
import os
import shutil


@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """

    browser.configure(
	#browser_engine="chrome",
    #slowmo=1000,
    headless=False
    )

    receipt_path = "output/receipt"
    #clean_envirment(receipt_path)
    open_robot_order_website()
    orders = get_orders()
    for order in orders:
        close_annoying_modal()
        fill_the_form(order)
        #preview()#why I nedd this???
        clickorder()
        pdf_path = store_receipt_as_pdf(order["Order number"],receipt_path)
        screenshot_path = screenshot_robot(order["Order number"],receipt_path)
        embed_screenshot_to_receipt(screenshot_path, pdf_path,order["Order number"], receipt_path)
        Order_another_robot()
    archive_receipts(receipt_path) 
    #time.sleep(60) # Sleep for 3 seconds

def open_robot_order_website():
    browser.goto("https://robotsparebinindustries.com/#/robot-order")
    #browser.page().evaluate("document.documentElement.requestFullscreen()") #full screen
    

def get_orders():
    #http = HTTP()
    HTTP().download("https://robotsparebinindustries.com/orders.csv", overwrite=True)
    return Tables().read_table_from_csv("orders.csv")

def close_annoying_modal():
    page = browser.page()
    #page.locator("//button[text()='OK']").click() not recommended by playwrigth
    page.get_by_role("button",name="OK").click() #recommended by playwrigth

def fill_the_form(order):
    page = browser.page()
    page.select_option("//select[@id='head']", index=int(order['Head']))
    page.check(f"//input[@type='radio' and @value='{order['Body']}']")
    page.fill("//label[text()='3. Legs:']/following-sibling::input",order['Legs'])
    page.fill("//input[@id='address']",order['Address'])

def preview():
    page = browser.page()
    page.click("//button[text()='Preview']")

def clickorder():
    page = browser.page()
    count = 0
    while not page.locator("//div[@id='order-completion']").is_visible() and count < 5 and page.locator("//button[@id='order']").is_visible():
        count+= 1
        page.locator("//button[@id='order']").click()
    if (count == 0 or count >=5) and not page.locator("//div[@id='order-completion']").is_visible():
        raise ApplicationException("An unexpected error occurred while attempting to click on the order button.Count value is either 0 or exceeds 5, which may indicate an issue with the order button's state or availability.")
        
           
        
def store_receipt_as_pdf(order_number, receipt_path):
    pdf_Path = f"{receipt_path}/ordernumber {order_number}/{order_number}.pdf"
    page = browser.page()
    receipt_html = page.locator("//div[@id='receipt']").inner_html()
    pdf = PDF()
    pdf.html_to_pdf(receipt_html, pdf_Path)
    return pdf_Path


def screenshot_robot(order_number, receipt_path):
    screenshot_Path = f"{receipt_path}/ordernumber {order_number}/{order_number}.png"
    page = browser.page()
    page.locator("//div[@id='robot-preview-image']").screenshot(path=screenshot_Path)
    return screenshot_Path

def Order_another_robot():
    page = browser.page()
    page.click("//button[@id='order-another']")

def embed_screenshot_to_receipt(screenshot, pdf_file, order_number, receipt_path):
    updated_PDF_Path = f"{receipt_path}/ordernumber {order_number}/{order_number}updated.pdf"
    pdf = PDF()
    pdf.add_files_to_pdf(
        files=[pdf_file, screenshot],  # This adds the screenshot to the PDF
        target_document=updated_PDF_Path,  # The resulting PDF with the screenshot added
        append=True  # This ensures that the screenshot is added to the existing content of 'output.pdf'
    )
    os.remove(screenshot)
    os.remove(pdf_file)

def clean_envirment(receipt_path):
    if  os.path.exists(receipt_path):
        shutil.rmtree(receipt_path)

def archive_receipts(receipt_path):
    shutil.make_archive(receipt_path,'zip',receipt_path)
    shutil.rmtree(receipt_path)