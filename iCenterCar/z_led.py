from machine import Pin
import time

class Mars_LED(object):
    def __init__(self, PIN_nled=2, nled_val=-1, nled_period=500*(10**6)):
        #`nled_val`：控制LED亮灭的状态值，初始为-1（表示初始状态为灭）
        #`nled_period`：LED闪烁的周期（单位为纳秒），默认为500毫秒（即0.5秒），计算为500*(10**6)纳秒（即500,000,000纳秒）
        self.PIN_nled = PIN_nled                    # led灯连接引脚2
        self.nled_val = nled_val                    # 通过该值来控制灯亮灭
        self.nled_systick_ms_bak = 0                # led灯时间控制，每隔一段时间亮一次
        self.nled_period = nled_period              # led亮灭的周期，每隔一段时间亮一次
        self.nled_pin = Pin(self.PIN_nled, Pin.OUT) # led灯连接引脚2，并设置为输出模式

    # led灯亮
    def nled_on(self):
        self.nled_pin.value(1)                      # led灯亮
        
    # led灯灭
    def nled_off(self):
        self.nled_pin.value(0)                      # led灯灭
    
    # led灯控制，flag=1灯亮，flag=-1灯灭
    def nled_flip(self, flag):
        if flag == 1:
            self.nled_on()                          # led灯亮
        elif flag == -1:
            self.nled_off()                         # led灯灭

    # led灯循环函数
    def loop_nled(self):
        if time.time_ns() - self.nled_systick_ms_bak > self.nled_period:  	# 每隔nled_period时间执行一次
            self.nled_systick_ms_bak = time.time_ns()                     	# 将当前时间赋值给nled_systick_ms_bak
            self.nled_flip(self.nled_val)           						# 执行led
            self.nled_val = -self.nled_val          						# 反转，即灯亮一次灭一次

# 程序入口
if __name__ == '__main__':
    nled = Mars_LED()                                 # 实例化一个nled对象
    try:
        while 1:                                    # 无限循环
            nled.loop_nled()                        # 循环执行led灯
    except:                                         # 异常处理
        nled.nled_off()                             # 程序异常时灯灭
