import sys
import traceback
import requests
from http.server import SimpleHTTPRequestHandler, HTTPServer
from threading import Thread
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QHBoxLayout, QTabWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
import io
from contextlib import redirect_stdout
import os

# Định nghĩa máy chủ HTTP
class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    current_html = ""

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes(self.get_html_code(), 'utf-8'))
        elif self.path == '/favicon.ico':
            self.send_error(404)  # Xử lý yêu cầu favicon.ico để tránh lỗi 404
        else:
            super().do_GET()  # Dùng phương thức mặc định để xử lý các tài nguyên khác

    def get_html_code(self):
        self.current_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Python Code Executor</title>
        </head>
        <body>
            <h1>Output:</h1>
            <h2>Python Code Execution:</h2>
            <div id="output">
                <pre>
<python>
x = 10
y = 20
result = x + y
print("Result:", result)
hellol = 3 + 1
print("Hello:", hellol)
</python>
                </pre>
            </div>
        </body>
        </html>
        """
        # Trả về kết quả thực thi Python thay vì chỉ trả về HTML nguyên bản
        return check_and_execute_python(self.current_html)


# Hàm kiểm tra và thực thi mã Python trong thẻ <python>
def check_and_execute_python(html_content):
    code_start = html_content.find('<python>') + len('<python>')
    code_end = html_content.find('</python>', code_start)

    if code_start == -1 or code_end == -1:
        return html_content  # Không có thẻ <python>, trả về nguyên bản HTML

    python_code = html_content[code_start:code_end].strip()

    result_output = ""
    try:
        # Thực thi mã Python và lưu kết quả đầu ra
        f = io.StringIO()
        with redirect_stdout(f):
            exec(python_code)  # Thực thi mã Python

        result_output = f.getvalue()  # Kết quả thực thi mã Python
        print(f"Python Output: {result_output}")  # In ra kết quả thực thi Python

    except Exception as e:
        result_output = traceback.format_exc()

    # Thay thế phần mã Python trong HTML bằng kết quả thực thi
    html_content = html_content.replace('<python>', '').replace('</python>', '').replace(python_code, result_output)

    return html_content

# Hàm chạy máy chủ HTTP
def run_http_server():
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, CustomHTTPRequestHandler)
    print("Serving on http://localhost:8000")
    httpd.serve_forever()


# Định nghĩa lớp Browser
class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bobby Browser")
        self.setGeometry(100, 100, 800, 600)

        # Tạo layout chính cho cửa sổ
        main_layout = QVBoxLayout()

        # Tạo layout cho ô nhập URL và nút
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL and press Enter")
        self.url_bar.setFixedHeight(30)  # Đặt chiều cao cố định cho ô nhập URL

        # Nút Back
        self.back_button = QPushButton("Back")
        self.back_button.setFixedHeight(30)
        self.back_button.clicked.connect(self.go_back)

        # Nút Up
        self.up_button = QPushButton("Up")
        self.up_button.setFixedHeight(30)
        self.up_button.clicked.connect(self.go_up)

        # Nút Go
        self.go_button = QPushButton("Go")
        self.go_button.setFixedHeight(30)  # Đặt chiều cao cố định cho nút Go
        self.go_button.clicked.connect(self.navigate_to_url)

        # Nút Clear Cache
        self.clear_cache_button = QPushButton("Clear Cache")
        self.clear_cache_button.setFixedHeight(30)  # Đặt chiều cao cố định cho nút Xóa Cache
        self.clear_cache_button.clicked.connect(self.clear_cache)

        # Nút Thêm Tab
        self.add_tab_button = QPushButton("+")
        self.add_tab_button.setFixedHeight(30)  # Đặt chiều cao cố định cho nút thêm tab
        self.add_tab_button.clicked.connect(self.add_new_tab)

        # Tạo layout cho ô nhập URL và các nút
        url_layout = QHBoxLayout()
        url_layout.addWidget(self.back_button)
        url_layout.addWidget(self.up_button)
        url_layout.addWidget(self.url_bar)
        url_layout.addWidget(self.go_button)
        url_layout.addWidget(self.clear_cache_button)
        url_layout.addWidget(self.add_tab_button)

        # Thêm layout ô nhập vào đầu cửa sổ
        layout_widget = QWidget()
        layout_widget.setLayout(url_layout)

        # Tạo QTabWidget để quản lý các tab
        self.tabs = QTabWidget()

        # Thêm layout chính vào widget trung tâm
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Thêm widget ô nhập URL vào layout chính
        main_layout.addWidget(layout_widget)  # Thêm ô nhập URL
        main_layout.addWidget(self.tabs)  # Thêm QTabWidget

        # Thêm tab đầu tiên
        self.add_new_tab()

        # Kết nối nút đóng tab
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)

    def add_new_tab(self):
        # Tạo một QWebEngineView mới
        browser_view = QWebEngineView()
        browser_view.setUrl(QUrl("http://localhost:8000"))  # Điều hướng đến URL nội bộ

        # Thêm tab mới vào QTabWidget
        tab_index = self.tabs.addTab(browser_view, f"Tab {self.tabs.count() + 1}")
        self.tabs.setCurrentIndex(tab_index)  # Chọn tab vừa thêm

    def close_tab(self, index):
        if 0 <= index < self.tabs.count():  # Kiểm tra chỉ số hợp lệ
            self.tabs.removeTab(index)  # Xóa tab

    def navigate_to_url(self):
        url = self.url_bar.text().strip()

        # Kiểm tra nếu URL không có http:// hoặc https://, thêm vào
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url  # Thêm http:// nếu không có

        print(f"Navigating to: {url}")

        try:
            # Sử dụng requests để lấy HTML từ URL
            response = requests.get(url)
            if response.status_code == 200:
                html = response.text  # Lấy HTML từ URL

                # Kiểm tra và thực thi mã Python trong thẻ <python> của mã HTML
                html_with_python_executed = self.check_and_execute_python(html)

                # Hiển thị mã HTML đã thay đổi trong QWebEngineView
                current_browser = self.tabs.currentWidget()  # Lấy tab hiện tại
                if isinstance(current_browser, QWebEngineView):
                    current_browser.setHtml(html_with_python_executed)  # Cập nhật trang với mã đã thực thi
            else:
                print("Error: Unable to fetch the page")
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")

    def check_and_execute_python(self, html):
        # Lấy HTML từ URL và thực thi mã Python
        html_with_python_executed = check_and_execute_python(html)
        return html_with_python_executed

    def clear_cache(self):
        current_browser = self.tabs.currentWidget()  # Lấy tab hiện tại
        if isinstance(current_browser, QWebEngineView):
            current_browser.page().profile().clearHttpCache()  # Xóa cache
            print("Cache cleared.")  # Thông báo xóa cache

    def go_back(self):
        current_browser = self.tabs.currentWidget()  # Lấy tab hiện tại
        if isinstance(current_browser, QWebEngineView):
            if current_browser.history().canGoBack():
                current_browser.back()  # Quay lại trang trước đó

    def go_up(self):
        current_browser = self.tabs.currentWidget()  # Lấy tab hiện tại
        if isinstance(current_browser, QWebEngineView):
            current_url = current_browser.url().toString()
            # Điều hướng lên trang cha (nếu có)
            if "://" in current_url:
                base_url = "/".join(current_url.split("/")[:-1])
                parent_url = base_url + "/"  # Lấy URL của trang cha
                current_browser.setUrl(QUrl(parent_url))  # Điều hướng lên trang cha
                print(f"Going up to: {parent_url}")


if __name__ == "__main__":
    # Chạy máy chủ HTTP trong một luồng riêng
    http_server_thread = Thread(target=run_http_server)
    http_server_thread.start()

    # Khởi tạo ứng dụng PyQt và khởi chạy browser
    app = QApplication(sys.argv)
    browser = Browser()
    browser.show()
    sys.exit(app.exec_())
