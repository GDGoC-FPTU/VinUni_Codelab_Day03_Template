import sys
import os
import pytest

SOLUTION_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "starter-code"))
if SOLUTION_DIR not in sys.path:
    sys.path.insert(0, SOLUTION_DIR)

try:
    from template import ChatbotBaseline, ReActAgent
except ImportError:
    from agent import ChatbotBaseline, ReActAgent

from tools import get_flight_info, get_weather_forecast

def test_flight_tool_execution():
    flights = get_flight_info(origin="HAN", destination="SGN", max_price=2000000)
    assert isinstance(flights, list)
    assert len(flights) == 2
    assert flights[0]["flight_number"] == "VN213" or flights[1]["flight_number"] == "VJ151"

def test_weather_tool_execution():
    weather = get_weather_forecast(city_code="SGN")
    assert isinstance(weather, dict)
    assert weather["city"] == "TP. Hồ Chí Minh"
    assert "recommendation" in weather

def test_chatbot_baseline_no_tools():
    chatbot = ChatbotBaseline()
    res = chatbot.query("Tìm vé HAN đến SGN")
    assert res["status"] == "success"
    assert len(res["tool_calls"]) == 0

def test_react_agent_multi_step_execution():
    agent = ReActAgent(max_iterations=5)
    res = agent.run("Tìm cho tôi chuyến bay từ HAN đi SGN dưới 2 triệu, rồi cho biết thời tiết SGN nên mặc gì?")
    
    assert res["status"] == "completed"
    assert res["iterations"] == 3
    assert len(res["trace"]) == 3
    assert "VJ151" in res["answer"] or "VN213" in res["answer"]
    assert "TP. Hồ Chí Minh" in res["answer"] or "32°C" in res["answer"]

def test_react_agent_single_step_flight():
    agent = ReActAgent(max_iterations=5)
    res = agent.run("Có chuyến bay nào từ HAN đi DAD giá dưới 1.5 triệu không?")
    assert res["status"] == "completed"
    assert res["iterations"] == 1
    assert "QH202" in res["answer"]

def test_react_agent_single_step_weather():
    agent = ReActAgent(max_iterations=5)
    res = agent.run("Thời tiết ở Đà Nẵng DAD hiện tại thế nào?")
    assert res["status"] == "completed"
    assert res["iterations"] == 1
    assert "28°C" in res["answer"]

def test_react_agent_faq_no_tool_call():
    agent = ReActAgent(max_iterations=5)
    res = agent.run("Chính sách đổi trả vé máy bay Vinpearl như thế nào?")
    assert res["status"] == "completed"
    assert res["iterations"] == 1
    assert "Vinpearl" in res["answer"]

def test_react_agent_max_iterations_safeguard():
    agent = ReActAgent(max_iterations=2)
    # Asking a multi-step query with max_iterations=2 forces safeguard limit
    res = agent.run("Tìm cho tôi chuyến bay từ HAN đi SGN dưới 2 triệu, rồi cho biết thời tiết SGN nên mặc gì?")
    assert res["status"] == "completed" or res["status"] == "max_iterations_reached"

if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
