import json
import os
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from typing import Optional

from config import Config
from translator import ModTranslator
from local_knowledge_base import LocalKnowledgeBase
from logger_config import logger

# 确保目录存在
Config.ensure_directories()
logger.info("应用目录结构初始化完成")

# 创建FastAPI应用
app = FastAPI(
    title=Config.APP_TITLE,
    description=Config.APP_DESCRIPTION
)
logger.info(f"FastAPI应用创建完成: {Config.APP_TITLE}")

# 创建翻译器实例
translator = ModTranslator(
    api_key=Config.OPENAI_API_KEY,
    api_base=Config.OPENAI_API_BASE
)
logger.info(f"翻译器初始化完成，模型: {translator.chatmodel.model_name}")

# 设置模板
templates = Jinja2Templates(directory=Config.TEMPLATES_DIR)
logger.info(f"模板引擎初始化完成，目录: {Config.TEMPLATES_DIR}")

# 创建本地知识库管理器
try:
    kb_manager = LocalKnowledgeBase(
        kb_dir=Config.KNOWLEDGE_BASE_DIR,
        openai_api_key=Config.OPENAI_API_KEY,
        openai_api_base=Config.OPENAI_API_BASE,
        embedding_model=Config.EMBEDDING_MODEL
    )
    logger.info(f"知识库管理器初始化完成，存储目录: {Config.KNOWLEDGE_BASE_DIR}")
except Exception as e:
    logger.error(f"知识库管理器初始化失败: {e}")
    raise


@app.get("/")
async def home(request: Request):
    """返回主页"""
    client_ip = request.client.host
    logger.info(f"主页访问 - IP: {client_ip}")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/knowledge-base")
async def knowledge_base_page(request: Request):
    """返回知识库管理页面"""
    client_ip = request.client.host
    logger.info(f"知识库管理页面访问 - IP: {client_ip}")
    return templates.TemplateResponse("knowledge_base.html", {"request": request})

@app.get("/api/knowledge-base", response_model=list)
async def get_knowledge_bases():
    """获取所有知识库列表"""
    try:
        kb_list = kb_manager.get_knowledge_bases()
        logger.info(f"获取知识库列表成功，共 {len(kb_list)} 个知识库")
        return kb_list
    except Exception as e:
        logger.error(f"获取知识库列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取知识库列表失败: {str(e)}")

@app.post("/api/knowledge-base")
async def create_knowledge_base(
    name: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...)
):
    """创建新的知识库"""
    logger.info(f"开始创建知识库: {name}, 文件: {file.filename}")
    
    # 验证文件类型
    if not file.filename.endswith('.json'):
        logger.warning(f"文件类型不支持: {file.filename}")
        raise HTTPException(status_code=400, detail="只支持JSON格式文件")
    
    try:
        # 读取上传的文件内容
        content = await file.read()
        logger.debug(f"文件读取完成，大小: {len(content)} 字节")
        
        # 检测BOM
        has_bom = content.startswith(b'\xef\xbb\xbf')
        if has_bom:
            logger.info("检测到UTF-8 BOM标记")
        
        # 尝试不同的编码方式，优先处理BOM
        encoding_used = None
        try:
            content_str = content.decode('utf-8-sig')  # 优先处理BOM
            encoding_used = 'utf-8-sig'
        except UnicodeDecodeError:
            try:
                content_str = content.decode('utf-8')
                encoding_used = 'utf-8'
            except UnicodeDecodeError:
                content_str = content.decode('gbk')  # 尝试GBK编码
                encoding_used = 'gbk'
        
        logger.info(f"文件编码解析成功，使用编码: {encoding_used}")
        
        # 验证内容不为空
        if not content_str.strip():
            logger.warning("上传的文件内容为空")
            raise HTTPException(status_code=400, detail="文件内容为空")
        
        # 解析JSON
        try:
            json_data = json.loads(content_str)
            logger.info("JSON解析成功")
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            raise HTTPException(
                status_code=400, 
                detail=f"JSON格式错误: {str(e)}。请确保文件是有效的JSON格式"
            )
        
        # 验证JSON数据结构
        if not isinstance(json_data, dict):
            logger.warning(f"JSON数据类型错误: {type(json_data)}")
            raise HTTPException(
                status_code=400, 
                detail="JSON文件必须是对象格式（键值对），不能是数组或其他类型"
            )
        
        if len(json_data) == 0:
            logger.warning("JSON对象为空")
            raise HTTPException(status_code=400, detail="JSON文件不能为空对象")
        
        logger.info(f"JSON数据验证通过，包含 {len(json_data)} 个条目")
        
        # 创建知识库
        logger.info("开始创建向量知识库...")
        kb_id = kb_manager.create_knowledge_base(name, description, json_data)
        logger.info(f"知识库创建成功，ID: {kb_id}")
        
        result = {
            "message": "知识库创建成功",
            "id": kb_id,
            "name": name,
            "entry_count": len(json_data)
        }
        logger.info(f"知识库 '{name}' 创建完成，返回结果")
        return result
        
    except HTTPException as e:
        # 重新抛出HTTP异常
        logger.warning(f"知识库创建失败 (HTTP {e.status_code}): {e.detail}")
        raise
    except Exception as e:
        logger.error(f"知识库创建过程中发生未预期错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建知识库时出现错误: {str(e)}")

@app.delete("/api/knowledge-base/{kb_id}")
async def delete_knowledge_base(kb_id: str):
    """删除知识库"""
    logger.info(f"开始删除知识库: {kb_id}")
    
    try:
        success = kb_manager.delete_knowledge_base(kb_id)
        if not success:
            logger.warning(f"知识库不存在: {kb_id}")
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        logger.info(f"知识库删除成功: {kb_id}")
        return {"message": "知识库删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除知识库时发生错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除知识库失败: {str(e)}")

@app.post("/translate")
async def translate_file(
    file: UploadFile = File(...),
    knowledge_base_id: Optional[str] = Form(None)
):
    """上传并翻译JSON文件"""
    
    kb_info = f"使用知识库: {knowledge_base_id}" if knowledge_base_id else "不使用知识库"
    logger.info(f"开始翻译文件: {file.filename}, {kb_info}")
    
    # 验证文件类型
    if not file.filename.endswith('.json'):
        logger.warning(f"翻译文件类型不支持: {file.filename}")
        raise HTTPException(status_code=400, detail="只支持JSON格式文件")
    
    try:
        # 读取上传的文件内容
        content = await file.read()
        logger.debug(f"翻译文件读取完成，大小: {len(content)} 字节")
        
        json_data = json.loads(content.decode('utf-8'))
        logger.info(f"翻译文件解析成功，包含 {len(json_data)} 个条目")
        
        # 执行翻译（使用RAG知识库）
        logger.info("开始AI翻译...")
        translated_data = translator.translate_json(
            json_data, 
            kb_manager=kb_manager if knowledge_base_id else None,
            kb_id=knowledge_base_id
        )
        logger.info("AI翻译完成")
        
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        translated_filename = f"translated_{file_id}.json"
        translated_path = os.path.join(Config.TEMP_DIR, translated_filename)
        
        # 保存翻译后的文件
        with open(translated_path, 'w', encoding='utf-8') as f:
            json.dump(translated_data, f, ensure_ascii=False, indent=2)
        logger.info(f"翻译文件保存成功: {translated_filename}")
        
        result = {
            "message": "翻译完成",
            "original_filename": file.filename,
            "translated_filename": translated_filename,
            "download_url": f"/download/{translated_filename}"
        }
        logger.info(f"翻译任务完成: {file.filename} -> {translated_filename}")
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"翻译文件JSON解析失败: {e}")
        raise HTTPException(status_code=400, detail="无效的JSON文件格式")
    except Exception as e:
        logger.error(f"翻译过程中发生错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"翻译过程中出现错误: {str(e)}")

@app.get("/download/{filename}")
async def download_file(filename: str):
    """下载翻译后的文件"""
    logger.info(f"文件下载请求: {filename}")
    
    file_path = os.path.join(Config.TEMP_DIR, filename)
    
    if not os.path.exists(file_path):
        logger.warning(f"下载文件不存在: {filename}")
        raise HTTPException(status_code=404, detail="文件不存在")
    
    logger.info(f"开始下载文件: {filename}")
    return FileResponse(
        path=file_path,
        filename=f"汉化_{filename}",
        media_type='application/json'
    )

@app.get("/health")
async def health_check():
    """健康检查接口"""
    logger.debug("执行健康检查")
    
    try:
        kb_health = kb_manager.health_check()
        
        result = {
            "status": "ok", 
            "message": "模组翻译器运行正常",
            "knowledge_base": kb_health,
            "translator": {
                "model": translator.chatmodel.model_name,
                "api_base": translator.api_base
            }
        }
        logger.debug("健康检查通过")
        return result
    except Exception as e:
        logger.warning(f"健康检查部分失败: {e}")
        return {
            "status": "warning",
            "message": "模组翻译器运行正常，但知识库可能有问题",
            "error": str(e)
        }

@app.get("/api/knowledge-base/{kb_id}/search")
async def search_knowledge_base(kb_id: str, query: str, top_k: int = 10):
    """搜索知识库接口"""
    try:
        results = kb_manager.search_in_knowledge_base(kb_id, query, top_k)
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

if __name__ == "__main__":
    # 如果直接运行main.py，则导入并运行启动脚本
    from run import main
    main()