from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import requests
import json
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# ===== 환경 변수에서 설정 읽기 (Render에서 설정) =====
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID_HERE')
# ================================================

# 접수 데이터를 저장할 리스트 (메모리에 저장)
# 주의: 서버 재시작 시 데이터가 사라집니다
# 실제 운영 시에는 데이터베이스 사용 권장
consultations = []

def send_telegram_message(consultation_data):
    """텔레그램으로 알림 메시지 전송"""
    if TELEGRAM_BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE' or TELEGRAM_CHAT_ID == 'YOUR_CHAT_ID_HERE':
        print("⚠️ 텔레그램 설정이 완료되지 않았습니다.")
        return False
    
    # 메시지 내용
    message = f"""🏢 새로운 부동산 상담 접수!

👤 고객명: {consultation_data['name']}
📞 연락처: {consultation_data['phone']}
📋 상담종류: {consultation_data['consultType']}
💬 내용: {consultation_data['message'] if consultation_data['message'] else '(없음)'}
⏰ 접수시간: {consultation_data['timestamp']}

빠른 연락 부탁드립니다! 🙏"""
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ 텔레그램 메시지 전송 성공!")
            return True
        else:
            print(f"❌ 텔레그램 메시지 전송 실패: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return False

# HTML 템플릿
INDEX_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>시원 부동산 서버</title>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 {
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 15px;
        }
        .status {
            padding: 15px;
            margin: 20px 0;
            border-radius: 8px;
            font-weight: 600;
        }
        .success {
            background: #d4edda;
            color: #155724;
        }
        .info {
            background: #e7f3ff;
            padding: 15px;
            border-left: 4px solid #2196F3;
            margin: 20px 0;
        }
        .count {
            font-size: 48px;
            color: #667eea;
            text-align: center;
            margin: 20px 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: #667eea;
            color: white;
        }
        tr:hover {
            background: #f5f5f5;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏢 시원 부동산 접수 시스템</h1>
        
        <div class="status success">
            ✅ 서버가 정상 작동 중입니다!
        </div>
        
        <div class="info">
            <h3>📊 접수 통계</h3>
            <div class="count">{{ consultation_count }}</div>
            <p style="text-align: center;">총 접수 건수</p>
        </div>
        
        <div class="info">
            <h3>📌 시스템 정보</h3>
            <p><strong>서버 상태:</strong> 온라인 ✅</p>
            <p><strong>텔레그램 알림:</strong> {{ telegram_status }}</p>
            <p><strong>마지막 접수:</strong> {{ last_consultation }}</p>
        </div>
        
        {% if consultations %}
        <div class="info">
            <h3>📋 최근 접수 내역 (최근 10건)</h3>
            <table>
                <thead>
                    <tr>
                        <th>시간</th>
                        <th>이름</th>
                        <th>연락처</th>
                        <th>종류</th>
                    </tr>
                </thead>
                <tbody>
                    {% for c in consultations[:10] %}
                    <tr>
                        <td>{{ c.timestamp }}</td>
                        <td>{{ c.name }}</td>
                        <td>{{ c.phone }}</td>
                        <td>{{ c.consultType }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """메인 페이지"""
    telegram_status = "활성화 ✅" if TELEGRAM_BOT_TOKEN != 'YOUR_BOT_TOKEN_HERE' else "미설정 ⚠️"
    last_consultation = consultations[-1]['timestamp'] if consultations else "아직 없음"
    
    return render_template_string(
        INDEX_HTML,
        consultation_count=len(consultations),
        telegram_status=telegram_status,
        last_consultation=last_consultation,
        consultations=list(reversed(consultations))
    )

@app.route('/api/consultation', methods=['POST'])
def receive_consultation():
    """상담 접수 API"""
    try:
        data = request.json
        
        # 타임스탬프 추가
        data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data['received_at'] = datetime.now().isoformat()
        
        # 데이터 저장
        consultations.append(data)
        print(f"\n✅ 새로운 접수: {data['name']} ({data['consultType']})")
        
        # 텔레그램 알림 전송
        send_telegram_message(data)
        
        return jsonify({
            'status': 'success',
            'message': '접수가 완료되었습니다.'
        }), 200
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/consultations', methods=['GET'])
def get_consultations():
    """접수 내역 조회 API"""
    return jsonify(consultations), 200

@app.route('/api/test-telegram', methods=['GET'])
def test_telegram():
    """텔레그램 테스트 API"""
    test_data = {
        'name': '테스트',
        'phone': '010-0000-0000',
        'consultType': '테스트',
        'message': '텔레그램 알림 테스트입니다.',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    result = send_telegram_message(test_data)
    
    if result:
        return jsonify({'status': 'success', 'message': '테스트 메시지가 전송되었습니다!'}), 200
    else:
        return jsonify({'status': 'error', 'message': '텔레그램 설정을 확인해주세요.'}), 500

@app.route('/health')
def health():
    """헬스체크 엔드포인트"""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 60)
    print("🏢 시원 부동산 접수 시스템 서버 시작!")
    print("=" * 60)
    print(f"📍 포트: {port}")
    print("⏰ 24시간 대기 중...")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=False)
