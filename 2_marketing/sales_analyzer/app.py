from flask import Flask, render_template, request, redirect, url_for, flash
import os
import csv
from collections import defaultdict
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def analyze_sales_data(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            data.append(row)
    
    # 마케팅 채널 분석
    channel_stats = defaultdict(lambda: {'총매출': 0, '거래수': 0, '할인율합': 0})
    for row in data:
        channel = row['마케팅채널']
        amount = int(row['총금액'])
        discount = float(row['할인율'])
        
        channel_stats[channel]['총매출'] += amount
        channel_stats[channel]['거래수'] += 1
        channel_stats[channel]['할인율합'] += discount
    
    channels = []
    for channel, stats in channel_stats.items():
        avg_amount = stats['총매출'] / stats['거래수']
        avg_discount = stats['할인율합'] / stats['거래수']
        channels.append({
            '채널': channel,
            '총매출': stats['총매출'],
            '평균구매액': round(avg_amount, 0),
            '거래수': stats['거래수'],
            '평균할인율': round(avg_discount, 1)
        })
    channels.sort(key=lambda x: x['총매출'], reverse=True)
    
    # 제품 카테고리 분석
    category_stats = defaultdict(lambda: {'총매출': 0, '거래수': 0, '총수량': 0})
    for row in data:
        category = row['카테고리']
        amount = int(row['총금액'])
        quantity = int(row['수량'])
        
        category_stats[category]['총매출'] += amount
        category_stats[category]['거래수'] += 1
        category_stats[category]['총수량'] += quantity
    
    categories = []
    for category, stats in category_stats.items():
        avg_amount = stats['총매출'] / stats['거래수']
        categories.append({
            '카테고리': category,
            '총매출': stats['총매출'],
            '평균구매액': round(avg_amount, 0),
            '거래수': stats['거래수'],
            '총판매수량': stats['총수량']
        })
    categories.sort(key=lambda x: x['총매출'], reverse=True)
    
    # 고객 세그먼트 분석
    age_segments = {'20대 이하': 0, '26-35세': 0, '36-45세': 0, '46-55세': 0, '56세 이상': 0}
    gender_stats = {'남성': {'총매출': 0, '거래수': 0}, '여성': {'총매출': 0, '거래수': 0}}
    
    for row in data:
        age = int(row['고객연령'])
        gender = row['고객성별']
        amount = int(row['총금액'])
        
        if age <= 25:
            age_segments['20대 이하'] += amount
        elif age <= 35:
            age_segments['26-35세'] += amount
        elif age <= 45:
            age_segments['36-45세'] += amount
        elif age <= 55:
            age_segments['46-55세'] += amount
        else:
            age_segments['56세 이상'] += amount
        
        gender_stats[gender]['총매출'] += amount
        gender_stats[gender]['거래수'] += 1
    
    # 지역별 분석
    region_stats = defaultdict(lambda: {'총매출': 0, '거래수': 0})
    for row in data:
        region = row['고객지역']
        amount = int(row['총금액'])
        
        region_stats[region]['총매출'] += amount
        region_stats[region]['거래수'] += 1
    
    regions = []
    for region, stats in region_stats.items():
        avg_amount = stats['총매출'] / stats['거래수']
        regions.append({
            '지역': region,
            '총매출': stats['총매출'],
            '평균구매액': round(avg_amount, 0),
            '거래수': stats['거래수']
        })
    regions.sort(key=lambda x: x['총매출'], reverse=True)
    
    return {
        'channels': channels,
        'categories': categories,
        'age_segments': age_segments,
        'gender_stats': gender_stats,
        'regions': regions,
        'total_records': len(data)
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('파일이 선택되지 않았습니다.')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('파일이 선택되지 않았습니다.')
        return redirect(request.url)
    
    if file and file.filename.lower().endswith('.csv'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            analysis_result = analyze_sales_data(file_path)
            return render_template('result.html', data=analysis_result, filename=filename)
        except Exception as e:
            flash(f'파일 분석 중 오류가 발생했습니다: {str(e)}')
            return redirect(url_for('index'))
    else:
        flash('CSV 파일만 업로드 가능합니다.')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)