# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3

> **Họ và Tên Học viên:** Đinh Trường An
> **Mã Sinh Viên / Mã Học viên:** 2A202602393
> **Chủ đề Lựa chọn:** Trợ lý Học vụ Sinh viên VinUni

## 1. Agentic Fit Scoring Matrix

| Tiêu chí | Mức độ | Giải trình |
| :--- | :---: | :--- |
| **Multi-step Reasoning** | **5 / 5** | Với yêu cầu nhiều bước, Agent phải tra cứu hồ sơ để lấy cố vấn, sau đó dùng kết quả đó để đặt lịch. Nếu tra cứu thất bại, Agent phải dừng thay vì đặt lịch sai. |
| **Tool Interaction** | **5 / 5** | Agent cần gọi `academic_query` để lấy dữ liệu học vụ và `schedule_appointment` để tạo lịch hẹn qua MCP Server. |
| **Dynamic Decision** | **4 / 5** | Bước tiếp theo phụ thuộc vào Observation: sinh viên có tồn tại không, cố vấn là ai và dữ liệu đặt lịch có hợp lệ không. |
| **Long Horizon Goal** | **4 / 5** | Mục tiêu xuyên suốt là hoàn tất yêu cầu học vụ, có thể cần nhiều lượt suy luận và gọi tool liên tiếp. |
| **TỔNG ĐIỂM** | **18 / 20** | Điểm trên 12/20 cho thấy chủ đề phù hợp để triển khai Agentic System. |

### Mục tiêu hệ thống

Hệ thống hỗ trợ sinh viên VinUni:

- Trả lời câu hỏi chung về quy chế học vụ.
- Tra cứu hồ sơ theo mã sinh viên.
- Đặt lịch tư vấn với cố vấn học tập.
- Xử lý trường hợp không tìm thấy sinh viên mà không bịa đặt dữ liệu.

## 2. Kiến trúc và lý do thiết kế

```text
User Query
    ↓
LLM Provider quyết định có cần Tool hay không
    ↓
MCPAcademicServer.call_tool()
    ↓
dispatch_tool_call()
    ↓
Tool Backend
    ↓
Observation JSON
    ↓
Final Answer hoặc Action tiếp theo
```

- `src/tools.py` chứa Tool Schema và logic backend. Schema giúp LLM biết tên tool, mục đích và tham số bắt buộc.
- `src/mcp_server.py` tách Agent khỏi backend và đóng gói kết quả theo JSON-RPC 2.0.
- `src/providers.py` cung cấp Gemini/OpenAI và Mock Provider để kiểm thử logic offline.
- `src/app.py` điều phối vòng lặp `Thought → Action → Observation`, xử lý lỗi và ghi waterfall trace.

## 3. Test Cases nghiệm thu

| ID | Kịch bản | Kết quả mong đợi |
| :--- | :--- | :--- |
| **TC01** | Hỏi quy chế học vụ chung | Trả lời trực tiếp, không gọi tool. |
| **TC02** | Tra cứu `SV2026001` | Gọi `academic_query`, trả về Nguyễn Văn An và GPA 3.85. |
| **TC03** | Đặt lịch cho `SV2026001` | Gọi `schedule_appointment` và trả booking thành công. |
| **TC04** | Tra cứu cố vấn rồi đặt lịch | `academic_query` thành công trước, sau đó `schedule_appointment` dùng đúng cố vấn. |
| **TC05** | Tra cứu `SV9999999` | Trả `NOT_FOUND`, không đặt lịch và không bịa dữ liệu. |

## 4. Trích xuất Waterfall Trace

Đoạn dưới đây trích theo cấu trúc trace thực tế sau khi chạy test suite. Trace đầy đủ được lưu tại `docs/trace_waterfall.json`.

```json
[
  {
    "step": 1,
    "action_type": "TOOL_EXECUTION",
    "thought": "Trước khi đặt lịch, tôi cần tra cứu cố vấn học tập của SV2026001.",
    "tool_name": "academic_query",
    "arguments": {"student_id": "SV2026001"},
    "observation": {
      "status": "SUCCESS",
      "student_id": "SV2026001",
      "data": {
        "full_name": "Nguyễn Văn An",
        "advisor": "PGS.TS Nguyễn Văn A"
      }
    },
    "latency_ms": 0.0
  },
  {
    "step": 2,
    "action_type": "TOOL_EXECUTION",
    "thought": "Đã có thông tin cố vấn, tiếp tục đặt lịch tư vấn.",
    "tool_name": "schedule_appointment",
    "arguments": {
      "student_id": "SV2026001",
      "datetime_str": "09:00 20/09/2026",
      "advisor_name": "PGS.TS Nguyễn Văn A"
    },
    "observation": {
      "status": "SUCCESS",
      "booking_id": "BK-SV2026001-99"
    },
    "latency_ms": 0.0
  }
]
```

## 5. Tổng kết nghiệm thu

- [x] Đã chạy lại test suite; provider đã thực thi luồng LLM và fallback offline khi bị giới hạn quota.
- **Tổng số Test Cases đã chạy thành công:** **5 / 5**.
- **Số lượt gọi Tool qua MCP Server:** TC02: 1, TC03: 1, TC04: 2, TC05: 1; tổng cộng **5 lượt**.
- **Kết quả đẩy Repo:** Chưa commit/push trong môi trường hiện tại.

### Lệnh nghiệm thu

```powershell
python src\app.py --all
```

Kết quả trên đã được ghi vào `docs/trace_waterfall.json`. Trước khi nộp, cập nhật thêm trạng thái commit/push nếu đã thực hiện trên GitHub cá nhân.

## 6. Kết luận

Đề tài phù hợp với Agentic System vì có dữ liệu động, nhiều công cụ và quyết định phụ thuộc vào Observation. Thiết kế hiện tại thể hiện được MCP Server, Tool Schema, ReAct loop, validation và Waterfall Trace; TC04 minh họa chuỗi `academic_query → Observation → schedule_appointment`.
