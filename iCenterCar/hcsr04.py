'''
修改信息
作者：郑养波
日期：2025年6月1日
'''
#超声波测距传感器实例子
import machine, time
from machine import Pin
__version__ = '0.2.0'
__author__ = 'Roberto Sánchez'
__license__ = "Apache License 2.0. https://www.apache.org/licenses/LICENSE-2.0"

class HCSR04:
    """
    Driver to use the untrasonic sensor HC-SR04.
    The sensor range is between 2cm and 4m.

    The timeouts received listening to echo pin are converted to OSError('Out of range')

    """
    # echo_timeout_us is based in chip range limit (400cm)
    def __init__(self, trigger_pin, echo_pin, echo_timeout_us=500*2*30):
        """
        trigger_pin: Output pin to send pulses 发送超声脉冲的引脚
        echo_pin: Readonly pin to measure the distance. The pin should be protected with 1k resistor  接收超声的引脚
        echo_timeout_us: Timeout in microseconds to listen to echo pin. 500*2*30=30000us=0.03s  0.03sX340m/s=10.2m 也就是往返可以5.1m
        By default is based in sensor limit range (4m)  传感器设置了默认探测4m 上述30秒时间足够4/340X2=0.0235s 设置的0.03s时间足够
        """
        self.echo_timeout_us = echo_timeout_us
        # Init trigger pin (out)
        self.trigger = Pin(trigger_pin, mode=Pin.OUT, pull=None)
        self.trigger.value(0)

        # Init echo pin (in)
        self.echo = Pin(echo_pin, mode=Pin.IN, pull=None)

    def _send_pulse_and_wait(self):
        """
        Send the pulse to trigger and listen on echo pin.
        We use the method `machine.time_pulse_us()` to get the microseconds until the echo is received.
        """
        self.trigger.value(0) # Stabilize the sensor
        time.sleep_us(2)
        self.trigger.value(1)      
        # Send a 10us pulse.
        time.sleep_us(10)
        self.trigger.value(0)
        #以上是 先拉低电平2us,在拉高电平10us,再拉低电平,相当于发送了一个10us的高电平脉冲信号
        try:
            pulse_time = machine.time_pulse_us(self.echo, 1, self.echo_timeout_us)
            #测量回波引脚从低变高后持续高电平的时间（单位微秒），设置了超时时间
            return pulse_time  #返回实际的回波时间
        #否则返回超时
        except OSError as ex:
            if ex.args[0] == 110: # 110 = ETIMEDOUT
                raise OSError('Out of range')
            raise ex

    def distance_mm(self):
        """
        Get the distance in milimeters without floating point operations.
        """
        pulse_time = self._send_pulse_and_wait()

        # To calculate the distance we get the pulse_time and divide it by 2 
        # (the pulse walk the distance twice) and by 29.1 becasue
        # the sound speed on air (343.2 m/s), that It's equivalent to
        # 0.34320 mm/us that is 1mm each 2.91us
        # pulse_time // 2 // 2.91 -> pulse_time // 5.82 -> pulse_time * 100 // 582 
        mm = pulse_time * 100 // 582
        return mm

    def distance_cm(self):
        """
        Get the distance in centimeters with floating point operations.
        It returns a float
        """
        pulse_time = self._send_pulse_and_wait()

        # To calculate the distance we get the pulse_time and divide it by 2 
        # (the pulse walk the distance twice) and by 29.1 becasue
        # the sound speed on air (343.2 m/s), that It's equivalent to
        # 0.034320 cm/us that is 1cm each 29.1us
        cms = (pulse_time / 2) / 29.1
        return cms

# 程序入口
if __name__ == "__main__":
    sensor = HCSR04(trigger_pin=2, echo_pin=4)  # 定义超声波模块Tring控制管脚及超声波模块Echo控制管脚,S3接口
    while True:
        us_dis = sensor.distance_cm()  # 获取超声波计算距离 ，也可以调用sensor.distance_mm() 得到mm值
        print (us_dis, 'cm')  # 打印超声波距离值
        print ('')
        time.sleep(0.5)  # 延时100ms