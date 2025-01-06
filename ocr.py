from flask import Flask, request, jsonify
import fitz  # PyMuPDF
import os
import tempfile
import re

app = Flask(__name__)

def extract_info(text, filename):
    # 根据文件名选择不同的提取模式
    if "交易结算费和账户维护费" in filename:
        patterns = {
            "托管账号": r"托管账号[:：]?\s*(\S+)",
            "现券": r"现券\s*\d+\s*([\d,]+\.\d+)",
            "回售": r"回售\s*\d+\s*([\d,]+\.\d+)",
            "质押式回购(多券)": r"质押式回购\(多券\)\s*\d+\s*([\d,]+\.\d+)"
        }
    elif "上海清算所" in filename:
        patterns = {
            "持有人账号": r"持有人账号[:：]?\s*(\S+)",
            "全额结算过户费-现券买卖": r"全额结算过户费-现券买卖\s*\d+\.\d+\s*\d+\.\d+\s*\d+\.\d+\s*([\d,]+\.\d+)",
            "全额结算过户费-质押式回购": r"全额结算过户费-质押式回购\s*\d+\.\d+\s*\d+\.\d+\s*\d+\.\d+\s*([\d,]+\.\d+)",
            "账户维护费": r"账户维护费\s*\d+\.\d+\s*\d+\.\d+\s*\d+\.\d+\s*([\d,]+\.\d+)",
            "查询服务费": r"查询服务费\s*\d+\.\d+\s*\d+\.\d+\s*\d+\.\d+\s*([\d,]+\.\d+)"
        }
    else:
        return {}

    extracted_info = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            extracted_info[key] = match.group(1)

    return extracted_info

@app.route('/ocr', methods=['POST'])
def ocr():
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400

    results = {}

    # 获取所有文件
    files = request.files.getlist('file')

    for file in files:
        filename = file.filename

        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            file.save(temp_file.name)
            temp_filename = temp_file.name

        text = ''
        try:
            if filename.lower().endswith('.pdf'):
                # 使用 PyMuPDF 提取 PDF 文本
                doc = fitz.open(temp_filename)
                for page in doc:
                    text += page.get_text()
                doc.close()
            else:
                results[filename] = {'error': '不支持的文件格式'}
                continue
        except Exception as e:
            results[filename] = {'error': str(e)}
            continue
        finally:
            # 删除临时文件
            os.remove(temp_filename)

        # 提取特定信息
        extracted_info = extract_info(text, filename)
        results[filename] = extracted_info

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
