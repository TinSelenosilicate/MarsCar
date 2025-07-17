from iCenterCar.z_uart import Mars_UART
import time

uart = Mars_UART()

def send_order(order_list):
    order = ""
    for single in order_list:
        order += "#%03dP%04dT%04d!" % (single[0], single[1], single[2])
    uart.uart_send_str(order)
    
def read_pwm(servoid):
    uart.uart_send_str("#011PRAD!")
    uart.recv_str()
    print(uart.uart_receive_str+"1234")
    print(uart.uart2)
    print(uart.uart2.read())
    print("123")
    
def pre_hold():
    send_order([[23, 1300, 2000], [22, 1200, 2000]])
    time.sleep(1)
    send_order([[21, 1500, 3000]])
    time.sleep(3)
    send_order([[23, 800, 2000], [25, 1500, 2000]])

def hold():
    send_order([[25, 1900, 2000]])
    
def pre_release():
    send_order([[23, 1300, 2000]])
    time.sleep(2)
    send_order([[21, 2400, 3000], [22, 1500, 3000], [23, 800, 3000]])
    
def release():
    send_order([[25, 1500, 2000]])
    
#用于卷线的027号舵机为定时马达模式（MOD7）
#P参数与1500的差值为转速，T参数为时间
#警告：T的单位是秒！

def wind():
    send_order([[27, 2000, 3]])
def unwind():
    send_order([[27, 1000, 3]])
