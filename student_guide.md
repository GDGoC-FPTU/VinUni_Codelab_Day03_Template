# Hướng Dẫn Chi Tiết Bài Thực Hành (Student Guide) — Lab #3

> **Dành cho:** Học viên chương trình VinUni AI Training Program  
> **Tài liệu:** Hướng dẫn thực hành từng bước (Step-by-Step Lab Walkthrough)

---

## 🧭 Hướng Dẫn Thực Hiện 4 Milestones

### 1. Milestone 1: Khởi Tạo Chatbot Baseline
Mở file `starter-code/template.py` và quan sát class `ChatbotBaseline`:
```python
class ChatbotBaseline:
    def query(self, user_input: str) -> str:
        # TODO: Trả về câu trả lời không dùng tool
```
* **Mục tiêu:** Hãy chạy phương thức `query()` với câu hỏi: `"Tìm chuyến bay từ HAN đi SGN dưới 2 triệu, và thời tiết SGN nên mặc gì?"`.
* **Quan sát:** Chatbot sẽ bịa ra thông tin chuyến bay hoặc từ chối tra cứu vì không có kết nối cơ sở dữ liệu.

---

### 2. Milestone 2: Đăng Ký Tool Registry
Mở file `starter-code/tools.py` và kiểm tra 2 hàm công cụ:
* `get_flight_info(origin, destination, max_price)`: Tìm kiếm trong `flight_data.json`.
* `get_weather_forecast(city_code)`: Tìm kiếm trong `weather_data.json`.

Hãy đảm bảo danh mục `TOOL_MAP` khai báo chính xác:
```python
TOOL_MAP = {
    "get_flight_info": get_flight_info,
    "get_weather_forecast": get_weather_forecast
}
```

---

### 3. Milestone 3: Xây Dựng ReAct Loop
Trong class `ReActAgent`, thuật toán vòng lặp được cài đặt theo sơ đồ sau:

```
[User Input] ──> (Iteration = 1)
                    │
                    ▼
           ┌─────────────────┐
           │     Thought     │ (Phân tích xem cần làm gì)
           └────────┬────────┘
                    │
                    ▼
           ┌─────────────────┐
           │     Action      │ ──> [Có Action?] ──Yes──> Call Tool ──> [Observation]
           └─────────────────┘                                              │
                    │ No (Is Final Answer?)                                 │
                    ▼                                                       │
             [Final Answer] <───────────────────────────────────────────────┘
```

Trong mỗi bước lặp:
1. Tạo đoạn suy luận `Thought`.
2. Chọn `Action` chứa tên tool và tham số JSON.
3. Thực thi hàm trong `TOOL_MAP` và thu về `Observation`.
4. Append thông tin vào mảng `self.trace`.

---

### 4. Milestone 4: Safegaurds & Trace Logging
Để phòng ngừa sự cố lặp vô tận, luôn kiểm tra điều kiện ngắt:
```python
if iteration >= self.max_iterations:
    return {
        "status": "max_iterations_reached",
        "answer": "Không thể hoàn thành trong số bước tối đa.",
        "trace": self.trace
    }
```

---

## 🪤 3 Bẫy Thường Gặp & Cách Khắc Phục (Traps & Gotchas)

1. **Trap 1: KeyError khi gọi Tool**
   * *Nguyên nhân:* Tên tool LLM trả về có khoảng trắng hoặc viết hoa (`Get_Flight_Info`).
   * *Cách khắc phục:* Gọi `.strip().lower()` trước khi tra cứu trong `TOOL_MAP`.

2. **Trap 2: Format Drift trong Action JSON**
   * *Nguyên nhân:* LLM trả về `Action: get_flight_info('HAN')` thay vì chuỗi JSON chuẩn `{"name": "get_flight_info", "args": {"origin": "HAN"}}`.
   * *Cách khắc phục:* Dùng `json.loads()` trong khối `try...except` và gửi lại thông báo lỗi `Observation: Invalid JSON format` nếu parse thất bại.

3. **Trap 3: Lặp vô tận khi API lỗi**
   * *Nguyên nhân:* Tool trả về dictionary chứa lỗi `{"error": "City not found"}`, Agent không biết dừng mà liên tục gọi lại.
   * *Cách khắc phục:* Giới hạn `max_iterations = 5` và hướng dẫn System Prompt nếu gặp lỗi 2 lần thì đưa ra Final Answer báo lỗi cho khách hàng.

---

## 🧪 Cách Kiểm Thử Kết Quả Bài Làm

Sau khi hoàn thành `template.py`, chạy lệnh pytest tại thư mục gốc dự án:
```bash
python3 -m pytest Day03-Chatbot-vs-ReAct-Agent/02-lab/autograder/test_agent.py -v
```

Nếu 5/5 test cases báo `PASSED`, chúc mừng bạn đã hoàn thành xuất sắc Lab #3!
