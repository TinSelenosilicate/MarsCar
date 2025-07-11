from machine import Pin
import time
from iCenterCar.z_led import Mars_LED

class Mars_KEY(object):
    def __init__(self, KEY1_PIN=36, KEY2_PIN=34):
        self.KEY1_PIN = KEY1_PIN                      # 定义按键1引脚
        self.KEY2_PIN = KEY2_PIN                      # 定义按键2引脚
        self.key1_pin = Pin(self.KEY1_PIN, Pin.IN)    # 将按键1对应引脚设置为输入模式
        self.key2_pin = Pin(self.KEY2_PIN, Pin.IN)    # 将按键2对应引脚设置为输入模式
     
    # 读取KEY1的值，按键按下为低电平
    def key1(self):
        return self.key1_pin.value()                  # 读取KEY1的值

    # 读取KEY2的值，按键按下为低电平
    def key2(self):
        return self.key2_pin.value()                  # 读取KEY2的值
    
# 循环检测按键引脚， key1控制led灯的亮灭，key2控制蜂鸣器的响灭
def loop_key():
    global key,led
    if key.key1() == 0:                          # 检测按键1是否为低电平
        time.sleep(0.02)                          # 消除抖动
        if key.key1() == 0:                      # 当key1按下时
            led.nled_on()                    # led灯亮
            while key.key1() == 0:               # 按住按键1时灯亮
                pass
            led.nled_off()                   # 按键1松开时led灯灭
    if key.key2() == 0:                          # 检测按键1是否为低电平
        time.sleep(0.02)                          # 消除抖动
        if key.key2() == 0:                      # 当key1按下时
            led.nled_on()                    # led灯亮
            while key.key2() == 0:               # 按住按键1时灯亮
                pass
            led.nled_off()                   # 按键1松开时led灯灭

# 程序入口
if __name__ == '__main__':
    key = Mars_KEY()                           # 实例化按键对象
    led = Mars_LED()                           # 实例化一个led灯对象
    try:                                              # 异常处理
        while 1:                                      # 无限循环
            loop_key()                            # 循环检测按键        
    except:
        led.nled_off()                            # 程序异常时led灯灭
