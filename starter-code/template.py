"""
Lab #3: Baseline Chatbot vs ReAct Agent
Học viên hoàn thiện các mục TODO để hoàn thành bài lab.
"""

import json
from tools import TOOL_DEFINITIONS, TOOL_MAP, get_flight_info, get_weather_forecast

SYSTEM_PROMPT = """Bạn là một ReAct Agent thông minh hỗ trợ khách hàng Vingroup.
Bạn chỉ sử dụng các công cụ sau:
{tools}

Quy trình trả lời bắt buộc:
Thought: <Suy nghĩ bước tiếp theo>
Action: {{"name": "<tên tool>", "args": {{<tham số>}}}}
Observation: <Kết quả từ tool>
... (Lặp lại cho tới khi có đủ dữ liệu)
Final Answer: <Câu trả lời hoàn chỉnh cho khách hàng>
"""

class ChatbotBaseline:
    """Baseline LLM Chatbot (Không sử dụng ReAct Loop hay Tools)"""
    def query(self, user_input: str) -> str:
        # TODO: Trả về câu trả lời tĩnh hoặc gọi LLM 1 lượt (không dùng tool)
        return f"[Chatbot Baseline] Trả lời cho: {user_input}"

class ReActAgent:
    """ReAct Agent có sử dụng Thought-Action-Observation Loop"""
    def __init__(self, max_iterations: int = 5):
        self.max_iterations = max_iterations
        self.trace = []

    def run(self, user_input: str) -> str:
        # TODO 1: Khởi tạo mảng lưu lịch sử conversation / traces
        # TODO 2: Thiết lập vòng lặp while iteration < self.max_iterations
        # TODO 3: Phân tích Thought / Action từ Agent
        # TODO 4: Thực thi Tool trong TOOL_MAP nếu có Action
        # TODO 5: Ghi lại Observation và lặp lại cho tới khi ra Final Answer
        
        # Skeleton return for starter code
        self.trace.append({"step": "init", "user_input": user_input})
        return "TODO: Implement ReAct Agent loop"

def main():
    user_query = "Tìm cho tôi chuyến bay từ HAN đi SGN dưới 2 triệu, rồi cho biết thời tiết SGN nên mặc gì?"
    
    print("=== RUNNING CHATBOT BASELINE ===")
    chatbot = ChatbotBaseline()
    print(chatbot.query(user_query))
    
    print("\n=== RUNNING REACT AGENT ===")
    agent = ReActAgent(max_iterations=5)
    result = agent.run(user_query)
    print("Result:", result)
    print("Trace Log:", json.dumps(agent.trace, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()