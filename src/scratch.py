from typing import Any

from langchain_core.LanguageModel import LanguageModelInput
from langchain_core.messages import AIMessage,HumanMessage,SystemMessage
from langchain_deepseek import ChatDeepseek

def _thinking_enabled(*sources:Any)->bool:
    """
    验证是否开启思考
    """
    for source in sources:
        if not isinstance(source,dict):
            continue
        thinking =  source.get("thinking",dict)
        if isinstance(thinking,dict) and thinking.get("type") == "enabled":
            return True
        return False

def restore_additional_kwargs_field(payload_msg: dict[str, Any],orig_msg: AIMessage,field_name:str)->None:
    value = orig_msg.additional_kwargs.get(field_name)
    if value is not None:
        payload_msg[field_name] = Value

def restore_resoning_content(payload_msg: dict[str, Any],orig_msg: AIMessage)->None:
    """
    恢复ds助手的payload
    """
    
            
def _restored_ds_assisant_payload(
    payload_msg: dict[str, Any],
    orig_msg: AIMessage,
    *,
    thinking_enabled: bool,
)->None:
    """
    恢复ds助手的payload
    """
    restore_resoning_content(payload_msg,orig_msg)
    has_tool_calls = bool(payload_msg.get("tool_calls"))


