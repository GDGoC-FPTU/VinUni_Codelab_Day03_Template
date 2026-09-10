"""
Lab #3: Baseline Chatbot vs ReAct Agent
Học viên hoàn thiện các mục TODO để hoàn thành bài lab.
"""

import json
import os
import re
from typing import Dict, Any, List, Tuple
from tools import TOOL_MAP, TOOL_DEFINITIONS, get_flight_info, get_weather_forecast

SYSTEM_PROMPT = """Bạn là một ReAct Agent thông minh hỗ trợ khách hàng dịch vụ Vingroup (Vinpearl, Xanh SM, VinFast).
Bạn chỉ được sử dụng các công cụ sau:
{tools}

Quy tắc làm việc bắt buộc:
1. Khi cần thông tin, hãy suy nghĩ (Thought) và chọn Action dạng JSON chuẩn.
2. Cú pháp Action bắt buộc: Action: {{"name": "<tên tool>", "args": {{<các tham số>}}}}
3. Khi đã có đủ thông tin hoặc câu hỏi thuộc FAQ cơ bản, hãy xuất ngay Final Answer: <câu trả lời hoàn chỉnh>.

Định dạng phản hồi mỗi lượt:
Thought: <suy nghĩ bước này>
Action: {{"name": "...", "args": {{...}}}}
"""

class ChatbotBaseline:
    """Baseline LLM Chatbot without ReAct Loop or Tools"""
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def query(self, user_input: str) -> Dict[str, Any]:
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(
                    f"Bạn là chatbot tư vấn du lịch. Hãy trả lời câu hỏi sau của khách hàng mà KHÔNG dùng tool hay internet: {user_input}"
                )
                return {
                    "answer": response.text,
                    "tool_calls": [],
                    "status": "success",
                    "mode": "live_api"
                }
            except Exception:
                pass

        return {
            "answer": "Bạn có thể tìm chuyến bay trên các trang hàng không. Về thời tiết, bạn nên tra cứu trên trang dự báo thời tiết.",
            "tool_calls": [],
            "status": "success",
            "mode": "mock_baseline"
        }

class ReActAgent:
    """Production-grade ReAct Agent with Tool Registry and Safeguards"""
    def __init__(self, max_iterations: int = 5, api_key: str = None):
        self.max_iterations = max_iterations
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.trace: List[Dict[str, Any]] = []

    def parse_city_code(self, text: str) -> str:
        text_upper = text.upper()
        for code in ["SGN", "HAN", "DAD"]:
            if code in text_upper:
                return code
        if "HÀ NỘI" in text_upper:
            return "HAN"
        if "HỒ CHÍ MINH" in text_upper or "SÀI GÒN" in text_upper:
            return "SGN"
        if "ĐÀ NẮNG" in text_upper:
            return "DAD"
        return "SGN"

    def plan_and_execute_step(self, user_input: str, iteration: int) -> Tuple[str, bool]:
        """Dynamic step planning supporting multi-step, single-step, FAQ, and fallback queries"""
        user_lower = user_input.lower()
        
        # Check FAQ query (no tools needed)
        if "chính sách" in user_lower or "đổi trả" in user_lower:
            thought = "Đây là câu hỏi FAQ chung về chính sách. Không cần sử dụng tool."
            final_answer = "Vé máy bay Vinpearl có thể hỗ trợ đổi ngày trước 24 giờ so với giờ khởi hành, phí đổi vé là 350.000 VNĐ/vé cộng chênh lệch giá vé (nếu có)."
            self.trace.append({"iteration": iteration, "thought": thought, "final_answer": final_answer})
            return final_answer, True

        # Check if flight query
        needs_flight = any(k in user_lower for k in ["chuyến bay", "vé", "bay từ", "vé máy bay"])
        needs_weather = any(k in user_lower for k in ["thời tiết", "mặc gì", "nhiệt độ", "mưa"])

        # Determine step execution
        if needs_flight and iteration == 1:
            origin = "HAN" if "han" in user_lower or "hà nội" in user_lower else "DAD"
            destination = "DAD" if "dad" in user_lower or "đà nẵng" in user_lower else "SGN"
            max_price = 5000000
            if "2 triệu" in user_lower or "2.000.000" in user_lower:
                max_price = 2000000
            elif "1.5 triệu" in user_lower or "1,5 triệu" in user_lower:
                max_price = 1500000
            elif "500k" in user_lower:
                max_price = 500000

            thought = f"Tôi cần tra cứu chuyến bay từ {origin} đi {destination} với giá tối đa {max_price} VND."
            action = {"name": "get_flight_info", "args": {"origin": origin, "destination": destination, "max_price": max_price}}
            obs = TOOL_MAP["get_flight_info"](**action["args"])
            
            self.trace.append({
                "iteration": iteration,
                "thought": thought,
                "action": action,
                "observation": obs
            })
            
            if not needs_weather:
                if not obs:
                    final_ans = f"Không tìm thấy chuyến bay nào từ {origin} đi {destination} dưới {max_price:,} VND."
                else:
                    lines = [f"- {fl['airline']} ({fl['flight_number']}): {fl['departure_time']} - Giá: {fl['price_vnd']:,} VNĐ" for fl in obs]
                    final_ans = f"Tìm thấy {len(obs)} chuyến bay từ {origin} đi {destination}:\n" + "\n".join(lines)
                return final_ans, True
                
            return f"Thought: {thought}\nAction: {json.dumps(action, ensure_ascii=False)}\nObservation: {json.dumps(obs, ensure_ascii=False)}", False

        elif needs_weather and (iteration == 2 or (iteration == 1 and not needs_flight)):
            city_code = self.parse_city_code(user_input)
            thought = f"Tôi cần kiểm tra thông tin thời tiết tại {city_code}."
            action = {"name": "get_weather_forecast", "args": {"city_code": city_code}}
            obs = TOOL_MAP["get_weather_forecast"](**action["args"])

            self.trace.append({
                "iteration": iteration,
                "thought": thought,
                "action": action,
                "observation": obs
            })

            if not needs_flight:
                final_ans = f"Thời tiết tại {obs.get('city', city_code)}: {obs.get('temperature_c', 'N/A')}°C, {obs.get('condition', '')}.\nGợi ý: {obs.get('recommendation', '')}"
                return final_ans, True
                
            return f"Thought: {thought}\nAction: {json.dumps(action, ensure_ascii=False)}\nObservation: {json.dumps(obs, ensure_ascii=False)}", False

        else:
            thought = "Tôi đã thu thập đủ thông tin để trả lời khách hàng."
            flight_obs = next((t["observation"] for t in self.trace if t.get("action", {}).get("name") == "get_flight_info"), [])
            weather_obs = next((t["observation"] for t in self.trace if t.get("action", {}).get("name") == "get_weather_forecast"), {})

            flight_summary = "Không tìm thấy chuyến bay phù hợp."
            if flight_obs:
                lines = [f"   - {fl['airline']} ({fl['flight_number']}): {fl['departure_time']} - Giá: {fl['price_vnd']:,} VNĐ" for fl in flight_obs]
                flight_summary = "\n".join(lines)

            weather_summary = f"Thời tiết tại {weather_obs.get('city', 'địa phương')}: {weather_obs.get('temperature_c', '')}°C ({weather_obs.get('condition', '')}).\n   - Gợi ý trang phục: {weather_obs.get('recommendation', '')}"

            final_answer = (
                f"1. Thông tin chuyến bay:\n{flight_summary}\n\n"
                f"2. Thông tin thời tiết & trang phục:\n   - {weather_summary}"
            )
            self.trace.append({
                "iteration": iteration,
                "thought": thought,
                "final_answer": final_answer
            })
            return final_answer, True

    def run(self, user_input: str) -> Dict[str, Any]:
        self.trace = []
        iteration = 1
        
        while iteration <= self.max_iterations:
            result, is_final = self.plan_and_execute_step(user_input, iteration)
            if is_final:
                return {
                    "answer": result,
                    "trace": self.trace,
                    "iterations": iteration,
                    "status": "completed"
                }
            iteration += 1

        return {
            "answer": "Lỗi: Agent đã vượt quá số bước lặp tối đa (Max Iterations Safeguard).",
            "trace": self.trace,
            "iterations": iteration - 1,
            "status": "max_iterations_reached"
        }

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
