import abc
import asyncio
import traceback

from app.utils.log_util import Lg


class Strategy(metaclass=abc.ABCMeta):
    """策略基类"""

    id_prefix = ""
    status = True
    
    @abc.abstractmethod
    async def init(self):
        pass    

    @abc.abstractmethod
    async def main(self):
        """main logic"""
        pass

    @abc.abstractmethod
    async def stop(self):
        """连接关闭"""
        pass
    
    @abc.abstractmethod
    async def clear_order(self):
        """持仓的平仓, 挂单的撤销"""
        pass
    

    async def run(self):
        """运行策略"""
        try:
            self.main()
        
        except asyncio.TimeoutError as e:
            Lg.error(f"{self.id_prefix} receiving data timeout error: {e}, strategy will be closed")
        except Exception as _e:
            traceback.print_exc()
            Lg.error(f"{self.id_prefix} 策略异常停止")
        else:
            # 业务代码出异常, 出了 main 函数会进入这里
            # 正常来说不会进入这里 
            Lg.error(f"{self.id_prefix} 执行停止")
        finally:
            await self.stop()