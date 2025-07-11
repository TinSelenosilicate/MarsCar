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
2. 底盘舵机ID:011-020 本次用4个
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
#1. 定义总线ID号
car_motor_fl=001                #小车左前轮电机ID
car_motor_fr=002                #小车右前轮电机ID
car_motor_bl=003                #小车左后轮电机ID
car_motor_br=004                #小车右后轮电机ID

car_servo_fl=011                #小车左前轮舵机ID   
car_servo_fr=012                #小车右前轮舵机ID   
car_servo_bl=013                #小车左后轮舵机ID   
car_servo_br=014                #小车右后轮舵机ID   

#2. 定义小车运动参数
car_run_speed = 800   				#小车直行运动速度，范围0~1000us 此数值是PWM输出数值，范围为500us-2500us之间，其中1500us电机停止，大于1500us正转，小于1500us反转
car_run_time = 5000				    #小车直行时间，小车直行时间1000=1s	#运行时间，范围为0000-9999，单位为ms

car_turn_speed = 400				#小车转弯时的速度  
car_turn_angle = 200				#小车转弯角度，范围0~1000us 此数值是PWM输出数值，偏转PWM=200us，270/2000*200=27度
car_turn_time = 2000				#小车转弯时间，小车直行时间1000=1s	

#3. 定义底盘转向舵机的初始位置PWM数值，并将测试得到数值对以下数值进行更新
car_servo_fl_init=1400
car_servo_fr_init=1600
car_servo_bl_init=1500
car_servo_br_init=1500

#测试底盘转向舵机的初始值 在Z_uart.py程序中运行。先运行整个Z_uart.py，再在命令栏中不断测试。找到舵机对中位置时的PWM数值，在1500附近
'''
uart.uart_send_str('#011P1500T2000!')
'''

#三、定义函数
#1.定义底盘舵机初始化函数，即再一次对中
def car_servos_init():
    Srt = '#011P{0:0>4d}T{4:0>4d}!#012P{1:0>4d}T{4:0>4d}!#013P{2:0>4d}T{4:0>4d}!#014P{3:0>4d}T{4:0>4d}!'.format(car_servo_fl_init,car_servo_fr_init,car_servo_bl_init,car_servo_br_init,1000)
    print(Srt)
    print("Car servos are tunning")
    uart.uart_send_str(Srt)
#2.小车直行运动函数
def car_run(run_speed,run_time):
    Srt = '#001P{0:0>4d}T{4:0>4d}!#002P{1:0>4d}T{4:0>4d}!#003P{2:0>4d}T{4:0>4d}!#004P{3:0>4d}T{4:0>4d}!'.format(1500-run_speed,1500+run_speed,1500-run_speed,1500+run_speed,run_time)
    print(Srt)
    print("Car is running")
    uart.uart_send_str(Srt)
        
#3.定义小车转弯运动
def car_turn(turn_angle,turn_time):
    Srt='#011P{0:0>4d}T{4:0>4d}!#012P{1:0>4d}T{4:0>4d}!#013P{2:0>4d}T{4:0>4d}!#014P{3:0>4d}T{4:0>4d}!'.format(1500-turn_angle,1500-turn_angle,1500+turn_angle,1500+turn_angle,turn_time)
    print(Srt)
    print("Car is turning")
    uart.uart_send_str(Srt)
        
#4.小车运动+转向
def car_run_and_turn(run_speed,turn_angle,run_time):
    Srt='#001P{0:0>4d}T{8:0>4d}!#002P{1:0>4d}T{8:0>4d}!#003P{2:0>4d}T{8:0>4d}!#004P{3:0>4d}T{8:0>4d}!#011P{4:0>4d}T{8:0>4d}!#012P{5:0>4d}T{8:0>4d}!#013P{6:0>4d}T{8:0>4d}!#014P{7:0>4d}T{8:0>4d}!'.format(1500-run_speed,1500+run_speed,1500-run_speed,1500+run_speed,1500-turn_angle,1500-turn_angle,1500+turn_angle,1500+turn_angle,run_time)
    print(Srt)
    print("Car is running and turning")
    uart.uart_send_str(Srt)
    
#5.小车停止函数 #停止车轮和转向
def car_stop():
    Srt = '#001P1500T1000!#002P1500T1000!#003P1500T1000!#004P1500T1000!#011P1500T1000!#012P1500T1000!#013P1500T1000!#014P1500T1000!'
    print(Srt)
    print("Car is stopping")
    uart.uart_send_str(Srt)

if __name__ == "__main__":
    
#     global uart,car_run_speed,car_run_time,car_turn_angle,car_turn_time
    uart = Mars_UART()                    #实例化串口对象
    
    #先对底盘舵机初始值-程序对中
    car_servos_init()
    
    car_stop()
    time.sleep(2)
    
    #小车前进运动
    car_run(car_run_speed,car_run_time) #前进
    time.sleep(2)
    
    car_stop()
    time.sleep(2)
    
     #小车后退运动
    car_run(-car_run_speed,car_run_time) #后退
    time.sleep(2)
    
    car_stop()
    time.sleep(2)

    #小车仅转向运动
    car_turn(car_turn_angle,car_turn_time)
    time.sleep(2)
    
    car_stop()
    time.sleep(2)
    
    #小车仅转向运动
    car_turn(-car_turn_angle,car_turn_time)
    time.sleep(2)
    
    car_stop()
    time.sleep(2)

    #小车运动+转向运动
    car_run_and_turn(car_run_speed,car_turn_angle,car_turn_time)
    time.sleep(2)
    
    car_stop()
    time.sleep(2) 

    car_run_and_turn(car_run_speed,-car_turn_angle,car_turn_time)
    time.sleep(2)

    car_stop()
    time.sleep(2) 