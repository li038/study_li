from typing import List, Dict, Any
import re
from langchain.schema import Document
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

class DocumentAnalyzer:
    """智能文档分析器"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        
        # 摘要模板
        self.summary_prompt = PromptTemplate(
            input_variables=["text"],
            template="""请为以下文档内容生成一个简洁的中文摘要：

{text}

摘要："""
        )
        
        # 关键词提取模板
        self.keywords_prompt = PromptTemplate(
            input_variables=["text"],
            template="""从以下文档中提取5-10个最重要的关键词：

{text}

关键词："""
        )
        
        # 实体识别模板
        self.entities_prompt = PromptTemplate(
            input_variables=["text"],
            template="""从以下文档中提取重要实体（人名、地点、时间、组织等）：

{text}

实体："""
        )
        
        # 使用新的LangChain API
        self.summary_chain = self.summary_prompt | self.llm
        self.keywords_chain = self.keywords_prompt | self.llm
        self.entities_chain = self.entities_prompt | self.llm
    
    def analyze_document(self, documents: List[Document]) -> Dict[str, Any]:
        """分析文档并返回综合信息"""
        if not documents:
            return {}
        
        # 合并所有文档内容
        full_text = "\n".join([doc.page_content for doc in documents])
        
        # 基础统计
        word_count = len(full_text)
        char_count = len(full_text.replace(" ", ""))
        sentence_count = len(re.split(r'[。！？]', full_text))
        
        # AI分析
        summary = self.summary_chain.invoke({"text": full_text[:4000]}).content  # 限制长度
        keywords = self.keywords_chain.invoke({"text": full_text[:2000]}).content
        entities = self.entities_chain.invoke({"text": full_text[:2000]}).content
        
        return {
            "统计信息": {
                "总字数": word_count,
                "总字符数": char_count,
                "句子数": sentence_count,
                "文档数": len(documents)
            },
            "摘要": summary.strip(),
            "关键词": [k.strip() for k in keywords.split(",") if k.strip()],
            "实体": [e.strip() for e in entities.split(",") if e.strip()],
            "文档来源": list(set([doc.metadata.get("source", "未知") for doc in documents]))
        }
    
    def generate_qa_pairs(self, documents: List[Document]) -> List[Dict[str, str]]:
        """基于文档生成可能的问答对"""
        if not documents:
            return []
        
        full_text = "\n".join([doc.page_content for doc in documents])[:3000]
        
        qa_prompt = PromptTemplate(
            input_variables=["text"],
            template="""基于以下文档内容，生成5个可能的问题和对应的答案：

{text}

请按以下格式输出：
Q1: [问题]
A1: [答案]

Q2: [问题]
A2: [答案]
..."""
        )
        
        qa_chain = qa_prompt | self.llm
        result = qa_chain.invoke({"text": full_text}).content
        
        # 解析结果
        qa_pairs = []
        lines = result.strip().split("\n")
        
        current_q = ""
        current_a = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith("Q") and ":" in line:
                if current_q and current_a:
                    qa_pairs.append({"question": current_q, "answer": current_a})
                current_q = line.split(":", 1)[1].strip()
            elif line.startswith("A") and ":" in line:
                current_a = line.split(":", 1)[1].strip()
        
        if current_q and current_a:
            qa_pairs.append({"question": current_q, "answer": current_a})
        
        return qa_pairs