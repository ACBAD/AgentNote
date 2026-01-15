import time
import json
from datetime import datetime
from openai import OpenAI
from .config import config
from ..utils.setup_logger import get_logger

logger = get_logger('DeepseekClient', debug=True)

class DeepSeekClient:
    """DeepSeek API客户端"""
    
    def __init__(self, api_key=None, enable_thinking=False):
        self.api_key = api_key or config.deepseek.api_key
        if not self.api_key:
            raise ValueError("DeepSeek API密钥未提供")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=config.deepseek.base_url
        )
        if enable_thinking:
            logger.debug('已启用思考模型')
        self.enable_thinking = enable_thinking
        # 初始化日志
        self.log_file = "deepseek_api_log.jsonl"

    def _log_api_call(self, request_data, response_data, error=None):
        """记录API调用到日志文件"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "request": request_data,
            "response": response_data,
            "error": error
        }
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def generate_content(self, system_prompt, user_prompt, model=None, temperature=None):
        """生成内容"""
        model = model or config.deepseek.model
        temperature = temperature or config.deepseek.temperature
        
        # 准备请求数据用于日志记录
        request_data = {
            "model": model,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "temperature": temperature,
        }
        
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            stream=False,
            extra_body={"thinking": {"type": "enabled"}} if self.enable_thinking else None
        )
        
        response_content = response.choices[0].message.content
        if self.enable_thinking:
            reasoning_content = response.choices[0].message.reasoning_content # type: ignore
        else:
            reasoning_content = None
        
        # 记录成功的API调用
        response_data = {
            "content": response_content,
            'think': reasoning_content,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            } if response.usage else None
        }
        
        self._log_api_call(request_data, response_data)
        return response_content

    def generate_with_retry(self, system_prompt, user_prompt, max_retries=3):
        """带重试的内容生成"""
        for attempt in range(max_retries):
            content = self.generate_content(system_prompt, user_prompt)
            if content:
                return content
            logger.error(f"生成失败，第 {attempt + 1} 次重试...")
            time.sleep(2)
        return None