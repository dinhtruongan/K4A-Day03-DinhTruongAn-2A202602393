"""
🔌 MULTI-PROVIDER LLM ADAPTER (Google Gemini, OpenAI & Offline Mock)
Hỗ trợ Native Tool Calling và chuyển đổi linh hoạt qua biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import re
from typing import Dict, Any, List
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho các LLM Provider hỗ trợ Native Tool Calling"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        raise NotImplementedError


class MockOfflineProvider(BaseLLMProvider):
    """Offline Mock Provider dùng để chạy thử mà không tốn API Key"""
    def __init__(self):
        self.model_name = "Offline-Mock-Model-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return f"[Mock Chatbot Response]: Xin chào! Tôi đã nhận được câu hỏi '{prompt}'. (Chế độ Chatbot không có Tool tra cứu dữ liệu thời gian thực)."

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        prompt_lower = prompt.lower()
        student_match = re.search(r"sv\d{7,}", prompt_lower)
        student_id = student_match.group(0).upper() if student_match else "SV2026001"
        datetime_match = re.search(r"(\d{1,2}:\d{2})\s*(?:ngày\s*)?(\d{1,2}/\d{1,2}/\d{4})", prompt_lower)
        datetime_str = f"{datetime_match.group(1)} {datetime_match.group(2)}" if datetime_match else "14:00 15/09/2026"
        
        # Mô phỏng nhận diện intent gọi Tool
        if "observation từ tool" in prompt_lower and "booking_id" in prompt_lower:
            message_match = re.search(r'"message"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', prompt)
            return {
                "type": "text",
                "content": message_match.group(1) if message_match else "Đã đặt lịch tư vấn thành công dựa trên kết quả từ MCP Server.",
                "thought": "Observation xác nhận booking thành công, tôi trả lời kết luận cuối cùng."
            }
        elif "observation từ tool" in prompt_lower and "đặt lịch" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "schedule_appointment",
                "arguments": {"student_id": student_id, "datetime_str": datetime_str, "advisor_name": "PGS.TS Nguyễn Văn A"},
                "thought": "Observation cung cấp cố vấn học tập. Tôi sẽ dùng cố vấn đó để đặt lịch."
            }
        elif "observation từ tool" in prompt_lower:
            message_match = re.search(r'"message"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', prompt)
            name_match = re.search(r'"full_name"\s*:\s*"([^"]+)"', prompt)
            gpa_match = re.search(r'"gpa"\s*:\s*([0-9.]+)', prompt)
            advisor_match = re.search(r'"advisor"\s*:\s*"([^"]+)"', prompt)
            if name_match:
                content = (
                    f"Tra cứu thành công: {name_match.group(1)}, "
                    f"GPA {gpa_match.group(1) if gpa_match else 'N/A'}, "
                    f"cố vấn {advisor_match.group(1) if advisor_match else 'N/A'}."
                )
            else:
                content = message_match.group(1) if message_match else "Đã nhận được dữ liệu học vụ từ MCP Server."
            return {
                "type": "text",
                "content": content,
                "thought": "Observation đã đủ để trả lời câu hỏi của người dùng."
            }
        elif "tra cứu cố vấn" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "academic_query",
                "arguments": {"student_id": student_id},
                "thought": f"Trước khi đặt lịch, tôi cần tra cứu cố vấn học tập của {student_id}."
            }
        elif "đặt lịch" in prompt_lower and "cố vấn: pgs.ts nguyễn văn a" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "schedule_appointment",
                "arguments": {"student_id": student_id, "datetime_str": datetime_str, "advisor_name": "PGS.TS Nguyễn Văn A"},
                "thought": "Người dùng yêu cầu đặt lịch hẹn tư vấn cho sinh viên SV2026001. Tôi sẽ gọi tool schedule_appointment."
            }
        elif "sv2026001" in prompt_lower and "đặt lịch" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "schedule_appointment",
                "arguments": {"student_id": student_id, "datetime_str": datetime_str, "advisor_name": "PGS.TS Nguyễn Văn A"},
                "thought": "Đã xác định cố vấn của SV2026001 từ yêu cầu và Observation. Tôi sẽ gọi tool schedule_appointment."
            }
        elif student_match or "tra cứu" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "academic_query",
                "arguments": {"student_id": student_id},
                "thought": f"Người dùng muốn tra cứu thông tin học vụ của sinh viên {student_id}. Tôi sẽ gọi tool academic_query."
            }
        elif any(keyword in prompt_lower for keyword in ["bạn là ai", "ban la ai", "who are you", "who are u", "what are you"]):
            return {
                "type": "text",
                "content": "Mình là Trợ lý Tác tử Học vụ VinUni. Mình có thể trả lời câu hỏi chung, tra cứu thông tin sinh viên và hỗ trợ đặt lịch với cố vấn học tập.",
                "thought": "Người dùng hỏi danh tính, tôi giới thiệu vai trò của mình mà không cần gọi Tool."
            }
        elif any(keyword in prompt_lower for keyword in ["làm được gì", "lam duoc gi", "có thể làm gì", "co the lam gi", "what can you do"]):
            return {
                "type": "text",
                "content": "Mình có thể: (1) trả lời câu hỏi chung về học vụ, (2) tra cứu hồ sơ sinh viên theo mã sinh viên, (3) đặt lịch tư vấn với cố vấn học tập, và (4) xử lý trường hợp không tìm thấy dữ liệu.",
                "thought": "Người dùng hỏi về khả năng của Agent, tôi liệt kê các chức năng mà không cần gọi Tool."
            }
        elif any(keyword in prompt_lower for keyword in ["xin chào", "xin chao", "hello", "hi ", "chào bạn", "chao ban"]):
            return {
                "type": "text",
                "content": "Xin chào! Mình là Trợ lý Học vụ VinUni. Bạn cần hỗ trợ tra cứu sinh viên, quy chế học vụ hay đặt lịch tư vấn?",
                "thought": "Người dùng chào hỏi, tôi phản hồi xã giao và gợi ý các chức năng hỗ trợ."
            }
        elif any(keyword in prompt_lower for keyword in ["quy chế", "quy che", "học vụ", "hoc vu", "tín chỉ", "tin chi", "tốt nghiệp", "tot nghiep", "gpa", "điểm", "diem", "môn học", "mon hoc"]):
            return {
                "type": "text",
                "content": "Quy chế học vụ VinUni yêu cầu sinh viên tích lũy đủ tín chỉ theo chương trình đào tạo, duy trì kết quả học tập đạt yêu cầu và tuân thủ quy định đăng ký môn học. Với thông tin chính thức, bạn nên kiểm tra Sổ tay sinh viên hoặc liên hệ Phòng Đào tạo.",
                "thought": "Câu hỏi thuộc phạm vi học vụ nhưng không cần dữ liệu cá nhân, tôi trả lời thông tin chung không gọi Tool."
            }
        else:
            return {
                "type": "text",
                "content": "Mình là Trợ lý Học vụ VinUni và chỉ hỗ trợ các vấn đề liên quan đến học vụ, hồ sơ sinh viên và lịch tư vấn. Mình chưa thể hỗ trợ câu hỏi này; bạn có thể hỏi về quy chế, tra cứu mã sinh viên hoặc đặt lịch với cố vấn.",
                "thought": "Câu hỏi nằm ngoài phạm vi học vụ, tôi nêu rõ giới hạn thay vì bịa đặt câu trả lời."
            }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider (Native Tool Calling với Google GenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(model=self.model_name, contents=contents)
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("ℹ️ [Gemini Provider]: Chưa tìm thấy GEMINI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)
        
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            
            # Chuẩn hóa function declarations cho Gemini SDK
            function_declarations = []
            for tool in tools_schema:
                # Bỏ qua các tool schema chưa được định nghĩa hoàn chỉnh
                if not tool.get("name") or not tool.get("parameters"):
                    continue
                function_declarations.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                })

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                temperature=0.2
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )

            # Kiểm tra xem Gemini có trả về Tool Call không
            if response.function_calls:
                call = response.function_calls[0]
                args = dict(call.args) if hasattr(call, 'args') and call.args else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": f"Gemini quyết định gọi công cụ '{call.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": response.text or "",
                    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }

        except Exception as e:
            print(f"⚠️ [Gemini API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (Native Tool Calling với OpenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        self.base_url = None

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("ℹ️ [OpenAI Provider]: Chưa tìm thấy OPENAI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": f"OpenAI quyết định gọi công cụ '{call.function.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": msg.content or "",
                    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }
        except Exception as e:
            print(f"⚠️ [OpenAI API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


class OpenRouterProvider(OpenAIProvider):
    """OpenRouter Provider dùng OpenAI-compatible API và Native Tool Calling."""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "openai/gpt-4o-mini"
        self.base_url = "https://openrouter.ai/api/v1"


def get_llm_provider() -> BaseLLMProvider:
    """Factory function khởi tạo Provider theo LLM_PROVIDER env variable"""
    provider_type = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if key and key != "your_gemini_api_key_here":
            return GeminiProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if key and key != "your_openai_api_key_here":
            return OpenAIProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openrouter":
        key = os.getenv("OPENROUTER_API_KEY")
        if key and key != "your_openrouter_api_key_here":
            return OpenRouterProvider()
        return MockOfflineProvider()
    elif provider_type == "mock":
        return MockOfflineProvider()
    else:
        return MockOfflineProvider()
