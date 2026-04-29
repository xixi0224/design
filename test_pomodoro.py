"""
测试番茄钟自动记录功能
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_pomodoro_complete():
    """测试番茄钟完成记录"""
    print("=" * 50)
    print("测试番茄钟自动记录功能")
    print("=" * 50)
    
    # 测试数据：完成一个25分钟的番茄钟
    test_data = {
        "duration": 25,
        "user_id": 1
    }
    
    print(f"\n发送请求: POST {BASE_URL}/api/tools/pomodoro/complete")
    print(f"请求数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/tools/pomodoro/complete",
            json=test_data
        )
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应数据: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("\n✅ 测试成功！")
                print(f"   - 记录时长: {data['duration']} 分钟")
                print(f"   - 今日累计: {data['total_today']} 分钟")
                print(f"   - 消息: {data['message']}")
            else:
                print("\n❌ 测试失败：API返回success=False")
        else:
            print(f"\n❌ 测试失败：HTTP {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败：请确保后端服务正在运行")
        print(f"   运行命令: cd ZhiNote2.0hou && uvicorn app.main:app --reload --port 8000")
    except Exception as e:
        print(f"\n❌ 测试出错: {str(e)}")

def test_multiple_pomodoros():
    """测试多次完成番茄钟"""
    print("\n" + "=" * 50)
    print("测试多次完成番茄钟（累加功能）")
    print("=" * 50)
    
    durations = [25, 30, 15]  # 模拟3次番茄钟
    
    for i, duration in enumerate(durations, 1):
        print(f"\n第 {i} 次完成番茄钟: {duration} 分钟")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/tools/pomodoro/complete",
                json={"duration": duration, "user_id": 1}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 成功 - 今日累计: {data['total_today']} 分钟")
            else:
                print(f"   ❌ 失败 - HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 错误: {str(e)}")
            break

if __name__ == "__main__":
    print("\n🍅 番茄钟自动记录功能测试\n")
    
    # 单次测试
    test_pomodoro_complete()
    
    # 多次测试（累加）
    test_multiple_pomodoros()
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("=" * 50)
