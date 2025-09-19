import json
from typing import Dict, Any
from fastapi import HTTPException
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from logger_config import logger


class ModTranslator:
    def __init__(self, api_key: str = None, api_base: str = None):
        # 默认配置
        self.api_base = api_base or "https://api.chatanywhere.tech"
        self.api_key = api_key or "sk-emQwzHKtOCBdpQcHiISFu5zU6WbgIUQCczI0JuPjjPh60uzK"
        
        self.chatmodel = ChatOpenAI(
            openai_api_key=self.api_key,
            openai_api_base=self.api_base,
            model="gpt-4o-mini",
            temperature=0
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的我的世界模组翻译员。
            你会收到一个JSON格式的文本，需要将其中的英文内容翻译成中文。
            
            翻译规则：
            1. 如果包含原版我的世界的专业名词（物品、生物、方块等），请使用官方中文译名
            2. 保持JSON结构不变，只翻译值（value）部分
            3. 键（key）保持英文不变
            4. 数字、布尔值等非文本内容保持不变
            5. 只返回翻译后的JSON，不要添加任何解释
            6. 如果提供了参考知识库，优先参考其中的翻译，保持翻译的一致性
            
            {reference_prompt}
            
            请翻译以下JSON内容："""),
            ("user", "{json_content}")
        ])
        
        self.parser = JsonOutputParser()
    
    def translate_json(self, json_data: Dict[str, Any], kb_manager=None, kb_id: str = None) -> Dict[str, Any]:
        """使用RAG技术翻译JSON数据"""
        try:
            # 将JSON转换为字符串
            json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
            
            # 准备参考知识库提示
            reference_prompt = ""
            if kb_manager and kb_id:
                # 使用RAG获取相关翻译
                relevant_translations = kb_manager.get_relevant_translations(kb_id, json_data)
                if relevant_translations:
                    ref_examples = []
                    for key, ref_info in relevant_translations.items():
                        ref_examples.append(f"'{ref_info['reference_key']}': '{ref_info['reference_value']}'")
                    
                    if ref_examples:
                        reference_prompt = f"""参考知识库中的相关翻译示例：
                                            {chr(10).join(ref_examples)}

                                            请参考这些翻译保持术语和风格的一致性。"""
                        logger.info(f"找到{len(ref_examples)}条相关数据:{str(ref_examples)}")
            
            # 创建链式调用
            chain = self.prompt | self.chatmodel | self.parser
            
            # 执行翻译
            result = chain.invoke({
                "json_content": json_str,
                "reference_prompt": reference_prompt
            })
            
            return result
        except Exception as e:
            error = str(e)
            raise HTTPException(status_code=500, detail=f"翻译失败: {error}")
    

