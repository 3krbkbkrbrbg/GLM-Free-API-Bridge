#!/usr/bin/env python3
"""
GLM / Z.ai Free API Bridge
High-performance, zero-dependency OpenAI-compatible API proxy for Z.ai (GLM-5, GLM-4.7, GLM-4.6V) with built-in Modern Admin Dashboard.
"""

import sys
import json
import re
import os
import time
import uuid
import hmac
import hashlib
import base64
import urllib.request
import urllib.error
from urllib.parse import urlencode
from http.server import HTTPServer, BaseHTTPRequestHandler

UPSTREAM = os.environ.get("ZAI_UPSTREAM", "https://chat.z.ai")
TOKEN_FILE = os.environ.get("ZAI_TOKEN_FILE", ".secrets/zai_token.txt")
DASHBOARD_FILE = os.environ.get("ZAI_DASHBOARD_FILE", "dashboard.html")
PORT = int(os.environ.get("PORT", 8080))
FE_VERSION = os.environ.get("ZAI_FE_VERSION", "2026.03.01")

SUPPORTED_MODELS = [
    {"id": "glm-5", "object": "model", "owned_by": "zhipu", "description": "Flagship next-gen GLM-5 model"},
    {"id": "glm-4.7", "object": "model", "owned_by": "zhipu", "description": "High performance general reasoning model"},
    {"id": "glm-4.7-thinking", "object": "model", "owned_by": "zhipu", "description": "Deep thinking and reasoning model"},
    {"id": "glm-4.7-search", "object": "model", "owned_by": "zhipu", "description": "Web search augmented GLM-4.7"},
    {"id": "glm-4.6v", "object": "model", "owned_by": "zhipu", "description": "Multimodal vision & image analysis"},
    {"id": "GLM-4.5", "object": "model", "owned_by": "zhipu", "description": "Standard 360B parameter model"},
    {"id": "GLM-4.5-Thinking", "object": "model", "owned_by": "zhipu", "description": "GLM-4.5 with chain-of-thought reasoning"},
    {"id": "GLM-4.5-Air", "object": "model", "owned_by": "zhipu", "description": "Lightweight high-speed 106B model"}
]

def get_token():
    if os.environ.get("ZAI_TOKEN"):
        return os.environ.get("ZAI_TOKEN").strip()
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    return ""

def set_token(token):
    os.makedirs(os.path.dirname(os.path.abspath(TOKEN_FILE)), exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        f.write(token.strip())

def _urlsafe_b64decode(data):
    if isinstance(data, str):
        data_bytes = data.encode("utf-8")
    else:
        data_bytes = data
    padding = b"=" * (-len(data_bytes) % 4)
    return base64.urlsafe_b64decode(data_bytes + padding)

def extract_user_id(token):
    try:
        parts = token.split(".")
        if len(parts) >= 2:
            payload = json.loads(_urlsafe_b64decode(parts[1]).decode("utf-8", errors="ignore"))
            for k in ("id", "user_id", "uid", "sub"):
                if k in payload and payload[k]:
                    return str(payload[k])
    except Exception:
        pass
    return "guest"

def generate_signature(canonical_payload, prompt, timestamp_ms):
    """
    Generate client signature (zs algorithm) for Z.ai request validation.
    """
    a = prompt.encode("utf-8")
    w = base64.b64encode(a).decode("ascii")
    c = f"{canonical_payload}|{w}|{timestamp_ms}"
    E = timestamp_ms // (5 * 60 * 1000)
    secret = "key-@@@@)))()((9))-xxxx&&&%%%%%"
    A = hmac.new(secret.encode("utf-8"), str(E).encode("utf-8"), hashlib.sha256).hexdigest()
    k = hmac.new(A.encode("utf-8"), c.encode("utf-8"), hashlib.sha256).hexdigest()
    return k

class ZaiBridgeHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE, HEAD")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_GET(self):
        # Serve Admin Dashboard
        if self.path in ["/", "/admin", "/dashboard"]:
            if os.path.exists(DASHBOARD_FILE):
                with open(DASHBOARD_FILE, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(content)
                return

        # Models endpoint
        if self.path in ["/v1/models", "/models"]:
            models_data = {
                "object": "list",
                "data": SUPPORTED_MODELS
            }
            body = json.dumps(models_data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
            return

        self._forward_raw("GET")

    def do_POST(self):
        # Update token API from Dashboard
        if self.path == "/admin/token":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8"))
                new_token = data.get("token", "").strip()
                if new_token:
                    set_token(new_token)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(b'{"status":"ok"}')
                    return
            except Exception:
                pass
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"error":"invalid token"}')
            return

        # Chat Completions
        if self.path in ["/v1/chat/completions", "/chat/completions"]:
            self._handle_chat_completions()
            return

        self._forward_raw("POST")

    def _handle_chat_completions(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)
        try:
            req_data = json.loads(raw_body.decode("utf-8"))
        except Exception as e:
            self._send_error(400, f"Invalid JSON body: {str(e)}")
            return

        model = req_data.get("model", "glm-4.7")
        messages = req_data.get("messages", [])
        stream = bool(req_data.get("stream", False))
        temperature = req_data.get("temperature", 0.7)

        # Extract last user message for signature
        last_user_text = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                c = m.get("content", "")
                if isinstance(c, str):
                    last_user_text = c
                elif isinstance(c, list):
                    last_user_text = " ".join([p.get("text", "") for p in c if isinstance(p, dict) and p.get("type") == "text"])
                break

        current_token = get_token()
        user_id = extract_user_id(current_token)
        timestamp_ms = int(time.time() * 1000)
        request_id = str(uuid.uuid4())
        message_id = str(uuid.uuid4())
        user_msg_id = str(uuid.uuid4())

        enable_thinking = "thinking" in model.lower() or model in ["glm-5", "GLM-4.5-Thinking"]
        web_search = "search" in model.lower()

        # Map friendly model IDs to upstream model strings if needed
        upstream_model = model
        if model in ["GLM-4.5", "GLM-4.5-Thinking", "GLM-4.5-Search"]:
            upstream_model = "0727-360B-API"
        elif model == "GLM-4.5-Air":
            upstream_model = "0727-106B-API"

        # Create upstream chat session
        chat_id = str(uuid.uuid4()).replace("-", "")[:24]
        try:
            chat_init_url = f"{UPSTREAM}/api/v1/chats/new"
            init_payload = {
                "chat": {
                    "id": "",
                    "title": "New Chat",
                    "models": [upstream_model],
                    "params": {},
                    "history": {
                        "messages": {
                            user_msg_id: {
                                "id": user_msg_id,
                                "parentId": None,
                                "childrenIds": [],
                                "role": "user",
                                "content": last_user_text[:200] if last_user_text else "Hello",
                                "timestamp": int(time.time()),
                                "models": [upstream_model]
                            }
                        },
                        "currentId": user_msg_id
                    },
                    "tags": [],
                    "flags": [],
                    "features": [{"type": "tool_selector", "server": "tool_selector_h", "status": "hidden"}],
                    "mcp_servers": [],
                    "enable_thinking": enable_thinking,
                    "auto_web_search": web_search,
                    "message_version": 1,
                    "timestamp": timestamp_ms
                }
            }
            init_req = urllib.request.Request(
                chat_init_url,
                data=json.dumps(init_payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {current_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
                    "Origin": UPSTREAM,
                    "Referer": f"{UPSTREAM}/"
                },
                method="POST"
            )
            with urllib.request.urlopen(init_req, timeout=10) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                chat_id = str(resp_data.get("id") or resp_data.get("chat", {}).get("id") or chat_id)
        except Exception:
            # If chat creation endpoint is not supported or failed, fallback to uuid chat_id
            pass

        # Build signature
        canonical = f"requestId,{request_id},timestamp,{timestamp_ms},user_id,{user_id}"
        sig = generate_signature(canonical, last_user_text, timestamp_ms)

        query_params = {
            "requestId": request_id,
            "timestamp": str(timestamp_ms),
            "user_id": user_id,
            "token": current_token,
            "version": "0.0.1",
            "platform": "web",
            "current_url": f"{UPSTREAM}/c/{chat_id}",
            "pathname": f"/c/{chat_id}",
            "signature_timestamp": str(timestamp_ms)
        }

        upstream_req_url = f"{UPSTREAM}/api/v2/chat/completions?{urlencode(query_params)}"

        upstream_body = {
            "stream": True,
            "model": upstream_model,
            "messages": messages,
            "signature_prompt": last_user_text,
            "params": {"temperature": temperature},
            "features": {
                "image_generation": False,
                "web_search": web_search,
                "auto_web_search": web_search,
                "preview_mode": True,
                "flags": [],
                "enable_thinking": enable_thinking
            },
            "chat_id": chat_id,
            "id": message_id,
            "current_user_message_id": user_msg_id,
            "current_user_message_parent_id": None,
            "background_tasks": {"title_generation": True, "tags_generation": True}
        }

        req_headers = {
            "Authorization": f"Bearer {current_token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "X-FE-Version": FE_VERSION,
            "Origin": UPSTREAM,
            "Referer": f"{UPSTREAM}/c/{chat_id}"
        }

        req = urllib.request.Request(
            upstream_req_url,
            data=json.dumps(upstream_body).encode("utf-8"),
            headers=req_headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Headers", "*")

                if stream:
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Cache-Control", "no-cache")
                    self.send_header("Connection", "keep-alive")
                    self.end_headers()

                    created_ts = int(time.time())
                    chunk_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

                    for line in resp:
                        line_str = line.decode("utf-8", errors="ignore")
                        if line_str.startswith("data:"):
                            data_part = line_str[5:].strip()
                            if data_part == "[DONE]":
                                self.wfile.write(b"data: [DONE]\n\n")
                                self.wfile.flush()
                                break
                            try:
                                chunk_json = json.loads(data_part)
                                delta_content = ""
                                
                                # Handle multiple Z.ai stream formats
                                if "choices" in chunk_json:
                                    delta_content = chunk_json["choices"][0].get("delta", {}).get("content", "")
                                elif "delta" in chunk_json:
                                    delta_content = chunk_json["delta"].get("content", "")
                                elif "text" in chunk_json:
                                    delta_content = chunk_json.get("text", "")
                                elif "content" in chunk_json:
                                    delta_content = chunk_json.get("content", "")

                                # Clean thought tags / metadata
                                if delta_content:
                                    cleaned = re.sub(r'<!--.*?-->', '', delta_content)
                                    cleaned = re.sub(r'</?details.*?>', '', cleaned)
                                    cleaned = re.sub(r'</?summary.*?>', '', cleaned)
                                    
                                    openai_chunk = {
                                        "id": chunk_id,
                                        "object": "chat.completion.chunk",
                                        "created": created_ts,
                                        "model": model,
                                        "choices": [{
                                            "index": 0,
                                            "delta": {"content": cleaned},
                                            "finish_reason": None
                                        }]
                                    }
                                    out_line = f"data: {json.dumps(openai_chunk)}\n\n"
                                    self.wfile.write(out_line.encode("utf-8"))
                                    self.wfile.flush()
                            except Exception:
                                pass

                    # Send final chunk
                    final_chunk = {
                        "id": chunk_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "delta": {},
                            "finish_reason": "stop"
                        }]
                    }
                    self.wfile.write(f"data: {json.dumps(final_chunk)}\n\ndata: [DONE]\n\n".encode("utf-8"))
                    self.wfile.flush()
                else:
                    # Non-streaming response aggregation
                    full_content = []
                    for line in resp:
                        line_str = line.decode("utf-8", errors="ignore")
                        if line_str.startswith("data:"):
                            data_part = line_str[5:].strip()
                            if data_part == "[DONE]":
                                break
                            try:
                                chunk_json = json.loads(data_part)
                                text = ""
                                if "choices" in chunk_json:
                                    text = chunk_json["choices"][0].get("delta", {}).get("content", "")
                                elif "text" in chunk_json:
                                    text = chunk_json.get("text", "")
                                if text:
                                    full_content.append(text)
                            except Exception:
                                pass

                    combined_text = "".join(full_content)
                    cleaned_text = re.sub(r'<!--.*?-->', '', combined_text)
                    cleaned_text = re.sub(r'</?details.*?>', '', cleaned_text)
                    cleaned_text = re.sub(r'</?summary.*?>', '', cleaned_text).strip()

                    openai_resp = {
                        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
                        "object": "chat.completion",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": cleaned_text
                            },
                            "finish_reason": "stop"
                        }],
                        "usage": {
                            "prompt_tokens": len(last_user_text) // 4,
                            "completion_tokens": len(cleaned_text) // 4,
                            "total_tokens": (len(last_user_text) + len(cleaned_text)) // 4
                        }
                    }
                    body_bytes = json.dumps(openai_resp).encode("utf-8")
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body_bytes)))
                    self.end_headers()
                    self.wfile.write(body_bytes)

        except urllib.error.HTTPError as e:
            self._send_error(e.code, f"Upstream Z.ai HTTP Error: {e.reason}")
        except Exception as e:
            self._send_error(500, f"Bridge Internal Error: {str(e)}")

    def _forward_raw(self, method):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else None

        req_url = f"{UPSTREAM}{self.path}"
        current_token = get_token()
        headers = {
            "Authorization": f"Bearer {current_token}",
            "Content-Type": self.headers.get("Content-Type", "application/json"),
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        req = urllib.request.Request(req_url, data=post_data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                self.send_response(resp.status)
                for k, v in resp.getheaders():
                    if k.lower() not in ["transfer-encoding", "content-encoding", "content-length"]:
                        self.send_header(k, v)
                self.send_header("Access-Control-Allow-Origin", "*")
                raw = resp.read()
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
        except urllib.error.HTTPError as e:
            self._send_error(e.code, e.read().decode("utf-8", errors="ignore"))
        except Exception as e:
            self._send_error(500, str(e))

    def _send_error(self, code, message):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        err_body = {"error": {"message": message, "code": code}}
        self.wfile.write(json.dumps(err_body).encode("utf-8"))

def run():
    server = HTTPServer(("0.0.0.0", PORT), ZaiBridgeHandler)
    print(f"🚀 GLM / Z.ai Free API Bridge running on http://0.0.0.0:{PORT}")
    print(f"📊 Dashboard available at http://localhost:{PORT}/admin")
    server.serve_forever()

if __name__ == "__main__":
    run()
