from machine import Pin
import time

class Mars_BEEP(object):
    def __init__(self, PIN_beep=5):
        self.PIN_beep = PIN_beep                    # 蜂鸣器连接引脚
        self.beep_pin = Pin(self.PIN_beep, Pin.OUT) # 蜂鸣器初始化并设置为输出模式
  
    # 蜂鸣器响
    def beep_on(self):
        self.beep_pin.value(1)                      # 蜂鸣器响
    
    # 蜂鸣器不响
    def beep_off(self):
        self.beep_pin.value(0)                      # 蜂鸣器不响

    # 间接发出响声，c代表名叫次数，x代表间接的时间，单位为秒
    def beep_on_times(self, c=3, x=0.1):
        for i in range(c):                          # 循环执行
            self.beep_on()                          # 蜂鸣器响
            time.sleep(x)                           # 延时
            self.beep_off()                         # 蜂鸣器不响
            time.sleep(x)                           # 延时

# 程序入口
if __name__ == '__main__':
    beep = Mars_BEEP()                                # 实例化一个beep对象
    beep.beep_on_times()                            # 蜂鸣器响3声
    try:
        while 1:                                    # 无限循环
            beep.beep_on_times(10, 0.5)             # 循环执行蜂鸣器
    except:                                         # 异常处理
        beep.beep_off()                             # 程序异常时蜂鸣器不响
