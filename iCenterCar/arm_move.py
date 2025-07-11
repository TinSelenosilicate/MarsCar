'''
通过串口发送指令控制电机的转速,时间
参数：
编写信息
作者：郑养波
日期：2025年6月1日
函数框架说明：

函数变量说明：
1. 底盘电机ID可用范围:001-010 本次用4个
001---car_motor_fl---左前轮
002---car_motor_fr---右前轮
003---car_motor_bl---左后轮
004---car_motor_br---右后轮
2. 地盘舵机ID:011-020 本次用4个
011---car_servo_fl---左前轮
012---car_servo_fr---右前轮
013---car_servo_bl---左后轮
014---car_servo_br---右后轮
3. 机械臂舵机ID:021-030 其中，个数学生自己选择 可以增加运动学
021---arm_servo_1---机械臂1号舵机 自下而上
022---arm_servo_2---机械臂2号舵机
023---arm_servo_3---机械臂3号舵机
024---arm_servo_4---机械臂4号舵机
…

(-1000~1000)负值后退，正值前进，绝对值越大转速越高。这里是实际设置值
runtime 代表车轮转动时间，0代表一直转动，1000代表转动1秒，以此类推。
注意：PWM电机驱动格式 #xxxPyyyyTzzzz-  #xxx-ID；Pyyyy-PWM输出数值；Tzzzz-运行时间
PWM是20ms一个周期，PWM范围为500us-2500us之间，其中1500s电机停止，大于1500正转，小于1500反转
Tzzzz是运行时间，范围为0000-9999，单位为s  全部是0000代表一直运行
'''
#一、导入头文件
#程序运行，必须先导入串口模块，然后实例化串口对象，然后调用相应的函数
#1.导入串口模块
from iCenterCar.z_uart import Mars_UART    
#2.导入时间模块
import time

#二、定义全局变量
#1. 定义机械臂ID号
arm_servo_1=021
arm_servo_2=022
arm_servo_3=023
arm_servo_4=024

#2.定义机械臂舵机的初始位置PWM数值，并将测试得到数值对以下数值进行更新
arm_servo_1_init=1530
arm_servo_2_init=1500
arm_servo_3_init=1500
arm_servo_4_init=1500

#测试机械臂舵机的初始值 在Z_uart.py程序中运行。先运行整个Z_uart.py，再在命令栏中不断测试。找到舵机对中位置时的PWM数值，在1500附近
'''
uart.uart_send_str('#021P1500T2000!')
'''

#三、定义函数
#1. 定义底盘舵机初始化函数，即再一次对中
def arm_servos_init():
    Srt = '#021P{0:0>4d}T{4:0>4d}!#022P{1:0>4d}T{4:0>4d}!#023P{2:0>4d}T{4:0>4d}!#024P{3:0>4d}T{4:0>4d}!'.format(arm_servo_1_init,arm_servo_2_init,arm_servo_3_init,arm_servo_4_init,1000)
    print(Srt)
    print("Arm servos are tunning")
    uart.uart_send_str(Srt)
    
#2. 定义机械臂运动——任何1个关节运动，需要传递arm_id,arm_ang,move_time-ID号、角度和时间
def arm_move_1(arm_id,arm_ang,move_time):
    armSrt='#{0:0>3d}P{1:0>4d}T{2:0>4d}!'.format(arm_id,arm_ang,move_time)
    print(armSrt)
    print(arm_id,"is running")
    uart.uart_send_str(armSrt)

#4定义机械臂运动——4个关节的运动， 需要传递arm_ang1,arm_ang2,arm_ang3,arm_ang4,move_time
def arm_move_4(arm_ang1,arm_ang2,arm_ang3,arm_ang4,move_time):
    armSrt='#021P{0:0>4d}T{4:0>4d}!#022P{1:0>4d}T{4:0>4d}!#023P{2:0>4d}T{4:0>4d}!#024P{3:0>4d}T{4:0>4d}!'.format(arm_ang1,arm_ang2,arm_ang3,arm_ang4,move_time)
    print(armSrt)
    print("Arm is running")
    uart.uart_send_str(armSrt)

if __name__ == '__main__':
#     global uart,arm1_ang,arm2_ang,arm3_ang,arm4_ang,move_time,arm1_initial_ang,arm2_initial_ang,arm3_initial_ang,arm4_initial_ang
    uart = Mars_UART()                    #实例化串口对象
        
    #先对机械臂舵机初始值-程序对中
    arm_servos_init()
    
    #单个关节测试
    #机械臂1号舵机先转到2000，再转到1000，最后回到初始位置
    arm_move_1(arm_servo_1,2000,1000)  #机械臂1号舵机运动
    time.sleep(2)
    
    arm_move_1(arm_servo_1,1000,1000)  #机械臂1号舵机运动
    time.sleep(2)
    
    arm_move_1(arm_servo_1,arm_servo_1_init,1000)  #机械臂1号舵机运动
    time.sleep(2)
    
    #机械臂2号舵机先转到2000，再转到1000，最后回到初始位置
    arm_move_1(arm_servo_2,2000,1000)  #机械臂1号舵机运动
    time.sleep(2)
    
    arm_move_1(arm_servo_2,1000,1000)  #机械臂1号舵机运动
    time.sleep(2)
    
    arm_move_1(arm_servo_2,arm_servo_2_init,1000)  #机械臂1号舵机运动
    time.sleep(2)
    
    
    #机械臂3号舵机先转到2000，再转到1000，最后回到初始位置
    arm_move_1(arm_servo_3,2000,1000)  #机械臂1号舵机运动
    time.sleep(2)
    
    arm_move_1(arm_servo_3,1000,1000)  #机械臂1号舵机运动
    time.sleep(2)
    
    arm_move_1(arm_servo_3,arm_servo_3_init,1000)  #机械臂1号舵机运动
    time.sleep(2)
    
    
    #机械臂4号舵机先转到2000，再转到1000，最后回到初始位置
    arm_move_1(arm_servo_4,2000,1000)  #机械臂1号舵机运动
    time.sleep(2)
    
    arm_move_1(arm_servo_4,1000,1000)  #机械臂1号舵机运动
    time.sleep(2)
    
    arm_move_1(arm_servo_4,arm_servo_4_init,1000)  #机械臂1号舵机运动
    time.sleep(2)
    

    #机械臂的4个舵机同时调试  
    #1234关节
    arm_move_4(1800,1800,1900,1900,1000)
    time.sleep(2)
    arm_move_4(1300,1400,1600,1200,1000)
    time.sleep(2)
