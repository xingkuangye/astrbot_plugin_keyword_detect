from astrbot.api import logger
from astrbot.api.star import Context, Star, register
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.core.star.filter.platform_adapter_type import PlatformAdapterType

def get_value(obj, key, default=None):
    try:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)
    except Exception:
        return default

@register("keyword_detect", "星星旁の旷野", "识别指定关键字并将消息转发至指定群聊", "0.5.0")
class MyPlugin(Star):
    
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.targets_groups = [str(g) for g in config.get("target_groups", []) or []]
        self.keywords = [str(k) for k in config.get("keywords", []) or []]

    @filter.event_message_type(filter.EventMessageType.ALL, priority=10)
    @filter.platform_adapter_type(PlatformAdapterType.AIOCQHTTP)
    async def keyword_detect(self, event: AstrMessageEvent) :
        """处理消息，检测关键字并转发"""
        raw_message = event.message_obj.raw_message
        post_type = get_value(raw_message, "post_type")
        message_str = event.message_str
        if post_type == "message" and get_value(raw_message, "message_type") == "group":
            logger.debug(f"收到消息: {message_str}")
            for keyword in self.keywords:
                if keyword == message_str:

                    logger.info(f"检测到关键字 '{keyword}'，开始转发消息")
                    group_id = str(get_value(raw_message, "group_id"))
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
                    forward_message = f"检测到关键字 \n{keyword} \n来自群 {group_name} "

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
