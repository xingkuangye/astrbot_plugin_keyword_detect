import time

from astrbot.api import logger
from astrbot.api.star import Context, Star, register
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.core.star.filter.platform_adapter_type import PlatformAdapterType


# 获取对象属性或字典值的通用函数
def get_value(obj, key, default=None):
    try:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)
    except Exception:
        return default
    

@register("keyword_detect", "星星旁の旷野", "识别指定关键字并将消息转发至指定群聊", "1.1.1")
class MyPlugin(Star):
    
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        # 读取配置
        self.detect_groups = [str(g) for g in config.get("detect_groups", []) or []]
        self.targets_groups = [str(g) for g in config.get("target_groups", []) or []]
        self.keywords = [str(k) for k in config.get("keywords", []) or []]
        self.fuzzy_keywords = [str(k) for k in config.get("fuzzy_keywords", []) or []]
        self.white_keywords = [str(k) for k in config.get("white_keywords", []) or []]


    # 监听所有消息事件
    @filter.event_message_type(filter.EventMessageType.ALL, priority=10)
    @filter.platform_adapter_type(PlatformAdapterType.AIOCQHTTP)
    async def keyword_detect(self, event: AstrMessageEvent) :
        """处理消息，检测关键字并转发"""

        raw_message = event.message_obj.raw_message
        post_type = get_value(raw_message, "post_type")
        message_str = event.message_str

        if post_type == "message" and get_value(raw_message, "message_type") == "group": # 群消息
            group_id = str(get_value(raw_message, "group_id"))

            # 仅处理配置中指定的群聊
            if group_id in self.detect_groups:

                # 检测精确关键字
                for keyword in self.keywords:
                    if keyword == message_str:
                        logger.info(f"检测到关键字 '{keyword}'，开始转发消息")
                        group_name = str(group_id)
                        client = event.bot
                        # 获取群名称
                        try:
                            group_info = await client.api.call_action('get_group_info', group_id=int(group_id))
                            group_name = group_info.get('group_name', group_name)
                        except Exception as e:
                            logger.error(f"获取群名称失败，使用群号作为名称{e}")
                            pass

                        # 组装消息内容
                        forward_message = f"【关键字检测通知】\n群聊：{group_name}({group_id})\n发送者：{event.get_sender_name()}({event.get_sender_id()})\n时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}\n--------------------\n关键字：{keyword}\n{event.get_sender_name()}：{message_str}"

                        # 转发消息
                        
                        logger.debug(f"开始将消息转发至目标群聊{self.targets_groups}")
                        for target_group in self.targets_groups:
                            try:
                                logger.debug(f"正在将消息转发至群 {target_group}")
                                await client.api.call_action(
                                    'send_group_msg',
                                    group_id=int(target_group),
                                    message=forward_message
                                )

                                logger.info(f"已将消息通知至群 {target_group}")
                                
                            except Exception as e:
                                # 通知消息至群失败
                                logger.error(f"通知消息至群 {target_group} 失败: {e}")

                        return  # 只需检测到一个关键字即可
                    

                # 命中白名单关键字，不进行后续处理
                for white_keyword in self.white_keywords:
                    if white_keyword in message_str:
                        logger.info(f"检测到白名单关键字 '{white_keyword}'，不进行转发")
                        return  
                    
                    
                # 检测模糊关键字
                for fuzzy_keyword in self.fuzzy_keywords:
                    if fuzzy_keyword in message_str:

                        logger.info(f"检测到模糊关键字 '{fuzzy_keyword}'，开始转发消息")
                        group_name = str(group_id)
                        client = event.bot
                        # 获取群名称
                        try:
                            group_info = await client.api.call_action('get_group_info', group_id=int(group_id))
                            group_name = group_info.get('group_name', group_name)
                        except Exception as e:
                            logger.error(f"获取群名称失败，使用群号作为名称{e}")
                            pass

                        # 组装消息内容
                        forward_message = f"【模糊关键字提醒】\n群聊：{group_name}({group_id})\n发送者：{event.get_sender_name()}({event.get_sender_id()})\n时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}\n--------------------\n关键字：{fuzzy_keyword}\n{event.get_sender_name()}：{message_str}"

                        # 转发消息
                        
                        logger.debug(f"开始将消息转发至目标群聊{self.targets_groups}")
                        for target_group in self.targets_groups:
                            try:
                                logger.debug(f"正在将消息转发至群 {target_group}")
                                await client.api.call_action(
                                    'send_group_msg',
                                    group_id=int(target_group),
                                    message=forward_message
                                )

                                logger.info(f"已将消息通知至群 {target_group}")

                            except Exception as e:
                                # 通知消息至群失败
                                logger.error(f"通知消息至群 {target_group} 失败: {e}")

                        break  # 只需检测到一个关键字即可
            

        return
