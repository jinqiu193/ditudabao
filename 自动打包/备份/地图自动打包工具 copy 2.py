from flask import Flask, request, send_file, flash, redirect, url_for # 导入 flash, redirect, url_for
import os
import zipfile
import shutil
from werkzeug.utils import secure_filename
import io # 导入 io
import re
import webbrowser

app = Flask(__name__)
# 设置一个密钥用于 flash 消息
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# 配置上传文件存储路径 - 使用绝对路径
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 辅助函数：检查 zip 文件内容
def check_zip_content(file_storage, extension):
    """检查 FileStorage 对象代表的 zip 文件是否包含指定扩展名的文件"""
    try:
        # 确保文件指针在开头
        file_storage.stream.seek(0)
        # 直接从流中读取 zip 文件，避免保存到磁盘
        with zipfile.ZipFile(io.BytesIO(file_storage.read()), 'r') as zip_ref:
            for filename in zip_ref.namelist():
                if filename.lower().endswith(extension):
                    # 再次将文件指针移到开头，以便后续保存
                    file_storage.stream.seek(0)
                    return True
        # 再次将文件指针移到开头
        file_storage.stream.seek(0)
        return False
    except zipfile.BadZipFile:
        # 如果文件不是有效的 zip 文件
        file_storage.stream.seek(0)
        return False
    except Exception as e:
        # 处理其他可能的异常
        print(f"Error checking zip content: {e}")
        file_storage.stream.seek(0)
        return False

@app.route('/')
def index():
    from flask import render_template_string # 在函数内部导入

    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>地图压缩包处理工具</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; /* 更现代的字体 */
                background-color: #f4f4f4; /* 添加背景色 */
                display: flex; /* 使用 Flexbox 居中 */
                justify-content: center;
                align-items: center;
                min-height: 100vh; /* 确保内容垂直居中 */
                margin: 0;
            }
            .container { /* 新增容器 */
                background-color: #fff;
                padding: 30px 40px; /* 增加内边距 */
                border-radius: 8px; /* 添加圆角 */
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); /* 添加阴影 */
                max-width: 600px; /* 限制最大宽度 */
                width: 100%;
            }
            h1 {
                text-align: center; /* 标题居中 */
                color: #333;
                margin-bottom: 30px; /* 增加标题下边距 */
            }
            .form-group {
                margin-bottom: 20px; /* 增加表单组间距 */
            }
            label {
                display: block;
                margin-bottom: 8px; /* 增加标签下边距 */
                color: #555;
                font-weight: bold; /* 标签加粗 */
            }
            input[type="file"] {
                width: calc(100% - 20px); /* 调整宽度以适应内边距 */
                padding: 10px; /* 调整输入框内边距 */
                margin-bottom: 10px;
                border: 1px solid #ccc; /* 添加边框 */
                border-radius: 4px;
                box-sizing: border-box; /* 确保 padding 不会撑大元素 */
            }
            button {
                background-color: #007bff; /* 更改按钮颜色 */
                color: white;
                padding: 12px 25px; /* 调整按钮内边距 */
                border: none;
                border-radius: 5px; /* 调整按钮圆角 */
                cursor: pointer;
                font-size: 16px; /* 调整按钮字体大小 */
                transition: background-color 0.3s ease; /* 添加过渡效果 */
                display: block; /* 让按钮独占一行 */
                width: 100%; /* 按钮宽度占满容器 */
                margin-top: 20px; /* 增加按钮上边距 */
            }
            button:hover {
                background-color: #0056b3; /* 更改悬停颜色 */
            }
            .flash-message { /* 添加 flash 消息样式 */
                padding: 15px;
                margin-bottom: 20px;
                border: 1px solid transparent;
                border-radius: 4px;
                text-align: center;
            }
            .flash-error {
                color: #a94442;
                background-color: #f2dede;
                border-color: #ebccd1;
            }
            .flash-success { /* 可以添加成功消息样式 */
                color: #3c763d;
                background-color: #dff0d8;
                border-color: #d6e9c6;
            }
        </style>
        <style>
            /* 添加进度提示样式 */
            .progress {
                display: none;
                text-align: center;
                margin-top: 20px;
                color: #007bff;
            }
            .spinner {
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid #f3f3f3;
                border-top: 3px solid #007bff;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="container"> <!-- 使用容器包裹内容 -->
            <h1>地图压缩包处理工具</h1>
            <!-- 显示 flash 消息 -->
            {% with messages = get_flashed_messages(with_categories=true) %}
              {% if messages %}
                {% for category, message in messages %}
                  {# 为验证消息添加特定前缀或标识 #}
                  {% if message.startswith('[验证]') %}
                  <div class="flash-message flash-{{ category }}">{{ message }}</div>
                  {% elif category == 'error' or category == 'success' %}
                  {# 只显示处理流程的消息 #}
                  <div class="flash-message flash-{{ category }}">{{ message }}</div>
                  {% endif %}
                {% endfor %}
              {% endif %}
            {% endwith %}

            <h2>合并地图与主题包</h2>
            <form action="{{ url_for('upload_file') }}" method="post" enctype="multipart/form-data" id="uploadForm">
                <div class="form-group">
                    <label for="zip_files">从蜂鸟地图下载地图和主题压缩包，文件名不要带（1）之类的内容 (共2个):</label>
                    <input type="file" id="zip_files" name="zip_files" multiple required accept=".zip"> <!-- 添加 accept 属性 -->
                </div>
                <button type="submit">上传主题和地图压缩包</button>
            </form>
            <div class="progress" id="progressIndicator">
                <div class="spinner"></div>
                <p>正在处理文件，请稍候...</p>
            </div>

            <div class="separator"></div> <!-- 添加分隔线 -->

            <h2>验证压缩包结构</h2>
             <!-- 显示验证相关的 flash 消息 -->
            {% with messages = get_flashed_messages(with_categories=true) %}
              {% if messages %}
                {% for category, message in messages %}
                  {% if message.startswith('[验证]') %}
                  <div class="flash-message flash-{{ category }}">{{ message[4:] }}</div> {# 去掉前缀显示 #}
                  {% endif %}
                {% endfor %}
              {% endif %}
            {% endwith %}
            <form action="{{ url_for('verify_zip') }}" method="post" enctype="multipart/form-data" id="verifyForm">
                <div class="form-group">
                    <label for="verify_file">选择要验证的压缩包 (1个):</label>
                    <input type="file" id="verify_file" name="verify_file" required accept=".zip">
                </div>
                <button type="submit">上传并验证压缩包是否正确</button>
            </form>

        </div>
        <script>
            // Optional: Add JS to show progress for the first form if needed
            // document.getElementById('uploadForm').addEventListener('submit', function() {
            //     document.getElementById('progressIndicator').style.display = 'block';
            // });
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_template)

@app.route('/upload', methods=['POST'])
def upload_file():
    # 使用 getlist 获取所有同名 'zip_files' 的文件
    uploaded_files = request.files.getlist('zip_files')

    # 验证是否上传了两个文件
    if len(uploaded_files) != 2:
        flash('请确保一次性选择并上传两个文件 (一个地图包，一个主题包)。', 'error')
        return redirect(url_for('index'))

    file1 = uploaded_files[0]
    file2 = uploaded_files[1]

    # 确保文件名不为空
    if not file1.filename or not file2.filename:
        flash('请选择有效的文件 (文件名不能为空)。', 'error')
        return redirect(url_for('index'))

    # 识别文件类型 (这部分逻辑不变)
    file1_is_map = check_zip_content(file1, '.fmap')
    file1_is_theme = check_zip_content(file1, '.theme')
    file2_is_map = check_zip_content(file2, '.fmap')
    file2_is_theme = check_zip_content(file2, '.theme')

    map_file = None
    theme_file = None

    if file1_is_map and file2_is_theme:
        map_file = file1
        theme_file = file2
    elif file1_is_theme and file2_is_map:
        map_file = file2
        theme_file = file1
    else:
        # 处理错误情况：类型不匹配或重复 (这部分逻辑不变)
        error_msg = "无法识别文件类型或文件类型冲突。请确保一个文件包含 .fmap (地图)，另一个包含 .theme (主题)。"
        if file1_is_map and file2_is_map:
            error_msg = "两个文件都像是地图文件 (包含 .fmap)。"
        elif file1_is_theme and file2_is_theme:
             error_msg = "两个文件都像是主题文件 (包含 .theme)。"
        elif not (file1_is_map or file1_is_theme or file2_is_map or file2_is_theme):
             error_msg = "无法在任何一个文件中找到 .fmap 或 .theme 文件。"

        flash(error_msg, 'error')
        return redirect(url_for('index'))

    try:
        # --- 后续处理逻辑与之前完全相同 ---
        # 从识别出的地图压缩包文件名中提取地图包名称，并清理文件名
        # 先进行安全处理，再清理特殊符号，确保secure_filename不会重新引入下划线
        map_name = os.path.splitext(clean_filename(secure_filename(map_file.filename)))[0]
        theme_name = os.path.splitext(clean_filename(secure_filename(theme_file.filename)))[0] # 保留主题名称以备用

        # 额外验证并清理顶层文件夹名称，确保不含-和_
        map_name = map_name.replace('-', '').replace('_', '')
        theme_name = os.path.splitext(clean_filename(secure_filename(theme_file.filename)))[0] # 保留主题名称以备用

        # 确保上传目录存在
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        # 创建以地图压缩包名称命名的工作目录
        work_dir = os.path.join(app.config['UPLOAD_FOLDER'], map_name)
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)
        os.makedirs(work_dir)

        # 保存原始压缩包 (使用识别后的变量)
        map_path = os.path.join(work_dir, secure_filename(map_file.filename))
        theme_path = os.path.join(work_dir, secure_filename(theme_file.filename))

        map_file.save(map_path)
        theme_file.save(theme_path)

        # 解压文件前检查文件是否存在
        if not os.path.exists(map_path) or not os.path.exists(theme_path):
             # 注意：这里返回错误页面可能更好，而不是简单的文本
            return '文件保存失败', 500

        # 解压文件并保持原始文件夹结构
        with zipfile.ZipFile(map_path, 'r') as zip_ref:
            namelist = zip_ref.namelist()
            root_dirs = set()
            for name in namelist:
                parts = name.split('/')
                if len(parts) > 1 and parts[0]: # 确保根目录名不为空
                    root_dirs.add(parts[0])
            if not root_dirs:
                map_extract_dir = os.path.join(work_dir, map_name)
                os.makedirs(map_extract_dir, exist_ok=True) # 使用 exist_ok=True 更安全
                zip_ref.extractall(map_extract_dir)
            else:
                zip_ref.extractall(work_dir)

        with zipfile.ZipFile(theme_path, 'r') as zip_ref:
            namelist = zip_ref.namelist()
            root_dirs = set()
            for name in namelist:
                parts = name.split('/')
                if len(parts) > 1 and parts[0]: # 确保根目录名不为空
                    root_dirs.add(parts[0])
            if not root_dirs:
                theme_extract_dir = os.path.join(work_dir, theme_name)
                os.makedirs(theme_extract_dir, exist_ok=True) # 使用 exist_ok=True 更安全
                zip_ref.extractall(theme_extract_dir)
            else:
                zip_ref.extractall(work_dir)

        # 删除原始压缩包
        os.remove(map_path)
        os.remove(theme_path)

        # 创建新的压缩包
        final_zip_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{map_name}.zip')
        with zipfile.ZipFile(final_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 添加工作目录下的所有文件到压缩包
            for root, dirs, files in os.walk(work_dir):
                # 排除可能由 macOS 创建的 __MACOSX 文件夹
                dirs[:] = [d for d in dirs if d != '__MACOSX']
                for file in files:
                    # 排除 .DS_Store 文件
                    if file == '.DS_Store':
                        continue
                    file_path = os.path.join(root, file)
                    # 计算相对路径，保持目录结构
                    arcname = os.path.relpath(file_path, work_dir) # 让解压后的文件直接在 work_dir 下
                    
                    # 清理路径中的所有文件夹和文件名
                    arcname_parts = arcname.split(os.sep)
                    cleaned_parts = [clean_filename(part) for part in arcname_parts]
                    cleaned_arcname = os.path.join(*cleaned_parts)
                    
                    # 为了实现最终压缩包包含一个以 map_name 命名的文件夹，我们需要调整 arcname
                    final_arcname = os.path.join(map_name, cleaned_arcname)
                    zipf.write(file_path, final_arcname)


        # 清理工作目录
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)

        # 返回处理后的压缩包
        return send_file(
            final_zip_path,
            as_attachment=True,
            download_name=f'{map_name}.zip'
        )

    except Exception as e:
        # 改进错误处理，使用 flash 显示错误信息 (这部分逻辑不变)
        error_msg = '处理失败：'
        if isinstance(e, zipfile.BadZipFile):
            error_msg += '无效的压缩文件格式'
        elif isinstance(e, OSError):
            error_msg += '文件系统操作失败，请检查文件权限'
        else:
            error_msg += str(e)
        
        print(f'详细错误: {e}')
        print(f'上传目录：{app.config["UPLOAD_FOLDER"]}')
        print(f'当前工作目录：{os.getcwd()}')
        flash(error_msg, 'error')
        if 'work_dir' in locals() and os.path.exists(work_dir):
             try:
                 shutil.rmtree(work_dir)
             except Exception as cleanup_e:
                 print(f"清理工作目录失败: {cleanup_e}")
        return redirect(url_for('index'))


@app.route('/verify', methods=['POST'])
def verify_zip():
    if 'verify_file' not in request.files:
        flash('[验证]未找到文件部分', 'error')
        return redirect(url_for('index'))

    file = request.files['verify_file']

    if file.filename == '':
        flash('[验证]未选择文件', 'error')
        return redirect(url_for('index'))

    if file and file.filename.lower().endswith('.zip'):
        original_filename = file.filename
        # 检查文件名是否只包含数字（不含后缀）
        filename_without_ext = os.path.splitext(original_filename)[0]
        if not re.fullmatch(r'\d+', filename_without_ext):
            flash(f'[验证]文件名 "{original_filename}" 只能包含数字。', 'error')
            return redirect(url_for('index'))
        
        filename = secure_filename(file.filename)
        # 预期根目录名（不含 .zip 后缀）
        expected_root_dir_name = os.path.splitext(filename)[0]
        # 创建临时目录进行解压和检查
        # 使用更安全的临时目录创建方式
        import tempfile
        temp_dir = None # 初始化为 None
        try:
            # 创建一个唯一的临时目录
            temp_dir = tempfile.mkdtemp(prefix='zip_verify_', dir=app.config['UPLOAD_FOLDER'])

            # 检查 zip 文件是否有效并解压
            try:
                # 从内存流解压，避免保存原始 zip
                file.stream.seek(0) # 确保指针在开头
                with zipfile.ZipFile(io.BytesIO(file.read()), 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            except zipfile.BadZipFile:
                flash(f'[验证]文件 "{filename}" 不是有效的 ZIP 文件。', 'error')
                return redirect(url_for('index'))
            except Exception as e:
                flash(f'[验证]解压文件 "{filename}" 时出错: {e}', 'error')
                return redirect(url_for('index'))

            # 检查解压后的根目录结构
            extracted_items = os.listdir(temp_dir)

            # 排除 macOS 自动生成的 __MACOSX 文件夹
            extracted_items = [item for item in extracted_items if item != '__MACOSX']

            if len(extracted_items) == 1 and os.path.isdir(os.path.join(temp_dir, extracted_items[0])):
                actual_root_dir_name = extracted_items[0]
                # 检查根目录名称是否只包含数字
                if not re.fullmatch(r'\d+', actual_root_dir_name):
                    flash(f'[验证]解压后的根目录名称 "{actual_root_dir_name}" 只能包含数字。', 'error')
                    return redirect(url_for('index'))
                if actual_root_dir_name == expected_root_dir_name:
                    flash(f'[验证]文件 "{filename}" 的结构符合预期 (根目录: {actual_root_dir_name})。', 'success')
                else:
                    flash(f'[验证]文件 "{filename}" 的结构不符合预期：根目录名称应为 "{expected_root_dir_name}"，实际为 "{actual_root_dir_name}"。', 'error')
            elif len(extracted_items) == 0:
                 flash(f'[验证]文件 "{filename}" 解压后为空。', 'error')
            else:
                 # 先将列表转换为字符串
                 extracted_list_str = ', '.join(extracted_items)
                 # 然后在 f-string 中使用这个字符串变量
                 flash(f'[验证]文件 "{filename}" 的结构不符合预期：根目录应只包含一个名为 "{expected_root_dir_name}" 的文件夹，实际包含: {extracted_list_str}。', 'error')

        except Exception as e:
            flash(f'[验证]处理文件时发生意外错误: {e}', 'error')
            print(f"Verification error: {e}") # 记录详细错误到控制台
        finally:
            # 清理临时目录
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as cleanup_e:
                    print(f"Error cleaning up temp directory {temp_dir}: {cleanup_e}")

        return redirect(url_for('index'))
    else:
        flash('[验证]请上传有效的 .zip 文件。', 'error')
        return redirect(url_for('index'))


def clean_filename(filename):
    """清理文件名，去除所有-和_符号以及类似(1)、（2）等后缀"""
    # 去除文件扩展名
    name, ext = os.path.splitext(filename)
    
    # 处理中文括号和英文括号
    # 移除末尾的 (数字) 或 （数字）
    import re
    name = re.sub(r'[\(（]\d+[\)）]$', '', name)
    
    # 移除名称中的-和_符号
    name = name.replace('-', '').replace('_', '')
    
    # 返回清理后的文件名
    return name + ext

if __name__ == '__main__':
    # 自动打开浏览器
    webbrowser.open('http://localhost:5000')
    # 启动Flask应用
    app.run(debug=True)