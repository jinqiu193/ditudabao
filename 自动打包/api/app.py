from flask import Flask

app = Flask(__name__)

# 保持原有路由和功能不变
@app.route('/tool')
def run_tool():
    # 调用现有打包工具逻辑
    return '执行完成'

@app.route('/package')
def package_map():
    # 调用原有打包工具的核心函数
    from 地图自动打包工具 import main_processor
    result = main_processor()
    return jsonify(result)

if __name__ == '__main__':
    app.run()