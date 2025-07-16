'''
编写信息
作者：郑养波
日期：2025年6月1日
函数框架说明：

函数变量说明：
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
……
'''

#一、库文件导入
import re							#正则表达式模块，用于字符串匹配和处理
import time
import _thread
import math
import socket
import network
# 从`factory`包中导入各种自定义模块，分别用于控制LED、蜂鸣器、按键、ADC、串口、文件、舵机、运动学和PS2手柄
from iCenterCar.z_led import Mars_LED
from iCenterCar.z_beep import Mars_BEEP
from iCenterCar.z_key import Mars_KEY
from iCenterCar.z_uart import Mars_UART
from iCenterCar.z_ps2 import Mars_PS2


#二、全局变量定义
#2.1 定义总线设备ID号
car_motor_fl=001                #小车左前轮电机ID
car_motor_fr=002                #小车右前轮电机ID
car_motor_bl=003                #小车左后轮电机ID
car_motor_br=004                #小车右后轮电机ID

car_servo_fl=011                #小车左前轮舵机ID   
car_servo_fr=012                #小车右前轮舵机ID   
car_servo_bl=013                #小车左后轮舵机ID   
car_servo_br=014                #小车右后轮舵机ID

arm_servo_1=021                 #机械臂第1个舵机ID       
arm_servo_2=022                 #机械臂第2个舵机ID
arm_servo_3=023                 #机械臂第3个舵机ID
arm_servo_4=026                 #机械臂第4个舵机ID

#2.2定义底盘转向舵机的初始位置PWM数值，并将测试得到数值对以下数值进行更新
car_servo_fl_init=1400
car_servo_fr_init=1450
car_servo_bl_init=1500
car_servo_br_init=1550

#2.3定义机械臂舵机的初始位置PWM数值，并将测试得到数值对以下数值进行更新
arm_servo_1_init=1480
arm_servo_2_init=1520
arm_servo_3_init=1630
arm_servo_4_init=1500

#2.4定义机械臂舵机的实时PWM数值，初始数值为init,后面根据控制情况实时调整
arm_servo_1_pwm=arm_servo_1_init
arm_servo_2_pwm=arm_servo_2_init
arm_servo_3_pwm=arm_servo_3_init
arm_servo_4_pwm=arm_servo_4_init
#定义机械臂运动的时间
arm_move_time = 2000					#机械臂运动时间，单位ms

#2.5 定义车速
car_run_speed= 800   				#小车直行运动速度，范围0~1000us 此数值是PWM输出数值，范围为500us-2500us之间，其中1500us电机停止，大于1500us正转，小于1500us反转
car_run_time = 5000					#小车直行时间1000=1s	该数值用于启动车子的运动

#小车转弯参数
car_turn_speed = 400					#小车转弯时的速度
car_turn_angle = 200 					#小车转弯角度，范围0~1000
car_turn_time = 8000					#小车转弯时间，暂时赋值

#2.6定义手柄控制参数
#ps2_systick_ms = 0                      #记录手柄历史时间戳
ps2_arm_inc= 100						#手柄遥控的每一次增量 机械臂的舵机增量-PWM数值

#2.3机械臂参数
car_turn_arm1=0						#转弯舵机1初始值，默认是PWM是1500
car_turn_arm2=0						#转弯舵机1初始值，默认是PWM是1500
car_turn_arm3=0						#转弯舵机1初始值，默认是PWM是1500
car_turn_arm4=0						#转弯舵机1初始值，默认是PWM是1500


#2.4 根据推进的遥感模拟量来计算车速 取最小值
speed_pwm=0					            #通过遥感计算得到的速度

#2.5标志位定义
voice_flag = 0					    #语音控制开关标记  1-开启；0-关闭
car_move_tag=0					    #底盘运动控制标记，1-说明运动要变化，0-说明运动不变化
arm_move_tag=0					    #机械臂运动控制标记，1-说明运动要变化，0-说明运动不变化


#三、函数定义
#3.0 指令发送
def send_order(order_list):
    order = ""
    for single in order_list:
        order += "#%03dP%04dT%04d!" % (single[0], single[1], single[2])
    uart.uart_send_str(order)
    
#3.1 定义时间函数
def millis():
    return int(time.time_ns()//1000000)

#3.2 定义传感器的模式
def loop_sensor():
    return

#3.3 LED灯处理函数-循环控制
def loop_nled():
    nled.loop_nled()                           # led灯循环亮灭

#3.4 定义小车运动函数
#3.4.1 定义底盘舵机初始化函数，即再一次对中位值进行校准
def car_servos_init():
    send_order([[11, car_servo_fl_init, 1000], [12, car_servo_fr_init, 1000], [13, car_servo_bl_init, 1000], [14, car_servo_br_init, 1000]])
    print("Car servos are tunning")
    
#3.4.2 小车直行运动函数
def car_run(run_speed,run_time):
    send_order([[1, 1500-run_speed, run_time], [2, 1500+run_speed, run_time], [3, 1500-run_speed, run_time], [4, 1500+run_speed, run_time]])
    print("Car is running")
        
#3.4.3 定义小车转弯运动
def car_turn(turn_angle,turn_time):
    send_order([[11, 1500-turn_angle, turn_time], [12, 1500-turn_angle, turn_time], [13, 1500+turn_angle, turn_time], [14, 1500+turn_angle, turn_time]])
    print("Car is turnning")
    Srt='#011P{0:0>4d}T{4:0>4d}!#012P{1:0>4d}T{4:0>4d}!#013P{2:0>4d}T{4:0>4d}!#014P{3:0>4d}T{4:0>4d}!'.format(1500-turn_angle,1500-turn_angle,1500+turn_angle,1500+turn_angle,turn_time)
    print(Srt)
    print("Car is turning")
    uart.uart_send_str(Srt)
        
#3.4.4 小车运动+转向
def car_run_and_turn(run_speed,turn_angle,run_time):
    Srt='#001P{0:0>4d}T{8:0>4d}!#002P{1:0>4d}T{8:0>4d}!#003P{2:0>4d}T{8:0>4d}!#004P{3:0>4d}T{8:0>4d}!#011P{4:0>4d}T{8:0>4d}!#012P{5:0>4d}T{8:0>4d}!#013P{6:0>4d}T{8:0>4d}!#014P{7:0>4d}T{8:0>4d}!'.format(1500-run_speed,1500+run_speed,1500-run_speed,1500+run_speed,1500-turn_angle,1500-turn_angle,1500+turn_angle,1500+turn_angle,run_time)
    print(Srt)
    print("Car is running and turning")
    uart.uart_send_str(Srt)
    
#3.4.5小车停止函数 #停止车轮和转向
def car_stop():
    Srt = '#001P1500T1000!#002P1500T1000!#003P1500T1000!#004P1500T1000!#011P{0:0>4d}T1000!#012P{1:0>4d}T1000!#013P{2:0>4d}T1000!#014P{3:0>4d}T1000!'.format(car_servo_fl_init,car_servo_fr_init,car_servo_bl_init,car_servo_br_init)
    print(Srt)
    print("Car is stopping")
    uart.uart_send_str(Srt)

#3.5 定义机械臂运动函数
#3.5.1 定义机械臂舵机初始化函数，即再一次对中
def arm_servos_init():
    send_order([[21, arm_servo_1_init, 1000], [22, arm_servo_2_init, 1000], [23, arm_servo_3_init, 1000]])
    print("Arm servos are tunning")
#2. 定义机械臂运动——任何1个关节运动，需要传递arm_id,arm_ang,move_time
def arm_move_1(arm_id,arm_ang,move_time):
    armSrt='#{0:0>3d}P{1:0>4d}T{2:0>4d}!'.format(arm_id,arm_ang,move_time)
    print(armSrt)
    print(arm_id,"is running")
    uart.uart_send_str(armSrt)    

#3.5.2定义机械臂运动——4个关节的运动， 需要传递arm_ang1,arm_ang2,arm_ang3,arm_ang4,move_time
def arm_move_4(arm_ang1,arm_ang2,arm_ang3,arm_ang4,move_time):
    armSrt='#021P{0:0>4d}T{4:0>4d}!#022P{1:0>4d}T{4:0>4d}!#023P{2:0>4d}T{4:0>4d}!#024P{3:0>4d}T{4:0>4d}!'.format(arm_ang1,arm_ang2,arm_ang3,arm_ang4,move_time)
    print(armSrt)
    print("Arm is running")
    uart.uart_send_str(armSrt)
    
#3.5.2定停止运动——4个关节的运动
def arm_stop():
    armSrt='#021P{0:0>4d}T{4:0>4d}!#022P{1:0>4d}T{4:0>4d}!#023P{2:0>4d}T{4:0>4d}!#024P{3:0>4d}T{4:0>4d}!'.format(arm_servo_1_init,arm_servo_2_init,arm_servo_3_init,arm_servo_4_init,1000)
    print(armSrt)
    print("Arm is running")
    uart.uart_send_str(armSrt)


#3.6主函数启动 车子机械臂初始化运动
def car_arm_initial():
     
    #初始化底盘舵机和机械臂舵机，使其位于目标中的初始位置
    car_servos_init()
    time.sleep(1)
    arm_servos_init()
    time.sleep(1)
    
    #直行前进运动测试
    car_run(int(car_run_speed/2),int(car_run_time/2)) #测试阶段速度 时间减半
    time.sleep(1)
    car_stop()
    time.sleep(1) 

    car_run(-int(car_run_speed/2),int(car_run_time/2)) #测试阶段速度 时间减半
    time.sleep(1)
    car_stop()
    time.sleep(1) 

    #转向测试
    car_turn(car_turn_angle,car_turn_time)
    time.sleep(1)
    car_stop()
    time.sleep(1) 

    car_turn(-car_turn_angle,car_turn_time)
    time.sleep(1)
    car_stop()
    time.sleep(1) 

    #转向运动测试
    car_run_and_turn(car_run_speed,car_turn_angle,car_turn_time)
    time.sleep(1)
    car_stop()
    time.sleep(1) 

    car_run_and_turn(-car_run_speed,-car_turn_angle,car_turn_time)
    time.sleep(1)
    car_stop()
    time.sleep(1) 
    
    arm_move_1(arm_servo_1,2000,1000)  #机械臂1号舵机运动
    time.sleep(1)
    
    arm_move_1(arm_servo_1,1000,1000)  #机械臂1号舵机运动
    time.sleep(1)
    
    arm_move_1(arm_servo_1,arm_servo_1_init,1000)  #机械臂1号舵机运动
    time.sleep(1)

    
    #机械臂2号舵机先转到2000，再转到1000，最后回到初始位置
    arm_move_1(arm_servo_2,2000,1000)  #机械臂1号舵机运动
    time.sleep(1)
    
    arm_move_1(arm_servo_2,1000,1000)  #机械臂1号舵机运动
    time.sleep(1)

    arm_move_1(arm_servo_2,arm_servo_2_init,1000)  #机械臂1号舵机运动
    time.sleep(1)
       
    #机械臂3号舵机先转到2000，再转到1000，最后回到初始位置
    arm_move_1(arm_servo_3,2000,1000)  #机械臂1号舵机运动
    time.sleep(2)
    
    arm_move_1(arm_servo_3,1000,1000)  #机械臂1号舵机运动
    time.sleep(2)

    arm_move_1(arm_servo_3,arm_servo_3_init,1000)  #机械臂1号舵机运动
    time.sleep(1)
       
    #机械臂4号舵机先转到2000，再转到1000，最后回到初始位置
    arm_move_1(arm_servo_4,2000,1000)  #机械臂1号舵机运动
    time.sleep(2)
    
    arm_move_1(arm_servo_4,1000,1000)  #机械臂1号舵机运动
    time.sleep(2)

    arm_move_1(arm_servo_4,arm_servo_4_init,1000)  #机械臂1号舵机运动
    time.sleep(1)

    #机械臂的4个舵机同时测试
    #…………
    #初始化车子和机械臂，为开始工作做准备
    car_servos_init()
    time.sleep(1)
    arm_servos_init()
    time.sleep(1)


#3.3处理串口接收的数据
'''
    - 调用uart.recv_str()接收数据
    - 根据接收完成标志（uart.uart_get_ok）判断数据类型：
    '<': '>',   # Type1: <...> 格式
    '{': '}',   # Type2: {...} 格式
    '#': '!',   # Type3: #...! 格式 #动作模式
    '$': '!'    # Type4: $...! 格式 #指令模式
'''
def loop_uart():
    global uart
    uart.recv_str()                           # 串口接收并根据格式处理数据
#     print(uart.uart_receive_str)
   
    #类似$111！
    if uart.uart_get_ok == 4:
#         print("uart.uart_get_ok=",uart.uart_get_ok)
        uart_data_handle(uart.uart_receive_str)         # 处理接收的数据-语音控制
#         uart.uart_receive_str = ''
#         uart.uart_get_ok = 0
#         #指令模式
#     elif uart.uart_get_ok == 1 or uart.uart_get_ok == 2 or uart.uart_get_ok == 3:
# #         print("uart.uart_get_ok=",uart.uart_get_ok)
#         uart.uart_receive_str = ''
#         uart.uart_get_ok = 0
#     else:
# #         print("uart.uart_get_ok=",uart.uart_get_ok)
#         uart.uart_receive_str = ''
#         uart.uart_get_ok = 0

    uart.uart_receive_str = ''
    uart.uart_get_ok = 0
  

def uart_data_handle(uart_data):
    global voice_flag,car_speed,car_turn_speed,car_turn_angle,car_turn_time
    # 唤醒指令
    if '$WAKE!' in uart_data:
        print('$WAKE!')
        car_stop()
        time.sleep(1)
#         voice_flag = 1
    # 停止指令
    elif '$TZ!' in uart_data:
        print('$TZ!')
        car_stop()
        time.sleep(1)
    # 前进指令
    elif '$QJ!' in uart_data:
        print('$QJ!')
        car_run(car_run_speed,0)   #一直前进
        time.sleep(1)

    # 后退指令
    elif '$HT!' in uart_data:
        print('$HT!')
        car_run(-car_run_speed,0)
        time.sleep(1)

    # 左转指令
    elif '$ZZ!' in uart_data:
        print('$ZZ!')
        car_stop()
        time.sleep(1)
        car_run_and_turn(car_turn_speed,car_turn_angle,0)
        time.sleep(1)

    # 右转指令
    elif '$YZ!' in uart_data:
        print('$YZ!')
        car_stop()
        time.sleep(1)
        car_run_and_turn(car_turn_speed,-car_turn_angle,0)
        time.sleep(1)

#     elif '$ZPY!' in uart_data:
#         print('$ZPY!')
#         Srt = '#021P2000T1000!'
#         print(Srt)
#         uart.uart_send_str(Srt)
#         time.sleep(1)
#     elif '$YPY!' in uart_data:
#         print('$YPY!')
#         Srt = '#021P1000T1000!'
#         print(Srt)
#         uart.uart_send_str(Srt)
#         time.sleep(1)

######################同学们需要在 loop_ps2()函数中增加自己的按键功能##########################
inits = [1500] * 30
inits[11] = 1400
inits[12] = 1450
inits[13] = 1500
inits[14] = 1550
inits[21] = 1480
inits[22] = 1520
inits[23] = 1630
inits[26] = 1500

current_pwms = inits[:]

my_run_speed = 400
horizontal = False

def clockwise_fix(servoid, degree, ms):
    if servoid >= 22:
        rg = 135
    else:
        rg = 180
    pwm = inits[servoid] - degree / rg * 1000
    send_order([[servoid, pwm, ms]])
    current_pwms[servoid] = pwm
    
def clockwise_fix_by_pwm(servoid, pwm, ms):
    send_order([[servoid, pwm, ms]])
    current_pwms[servoid] = pwm

def clockwise_rotate(servoid, degree, ms):
    global current_pwms
    if servoid >= 22:
        rg = 135
    else:
        rg = 180
    pwm = current_pwms[servoid] - degree / rg * 1000
    send_order([[servoid, pwm, ms]])
    current_pwms[servoid] = pwm
    
def clockwise_rotate_by_pwm(servoid, pwm, ms):
    global current_pwms
    send_order([[servoid, pwm, ms]])
    current_pwms[servoid] = pwm
    
def run(run_speed, run_time):
    send_order([[1, 1500-run_speed, run_time], [2, 1500+run_speed, run_time], [3, 1500-run_speed, run_time], [4, 1500+run_speed, run_time]])
    print("Car is running")
    
def turn(angle, turn_time):
    global current_pwms
    rg = 180
    pwm1 = current_pwms[11] - angle / rg * 1000
    pwm2 = current_pwms[12] - angle / rg * 1000
    pwm3 = current_pwms[13] + angle / rg * 1000
    pwm4 = current_pwms[14] + angle / rg * 1000
    send_order([[11, pwm1, turn_time],[12, pwm2, turn_time],[13, pwm3, turn_time],[14, pwm4, turn_time]])
    current_pwms[11] = pwm1
    current_pwms[12] = pwm2
    current_pwms[13] = pwm3
    current_pwms[14] = pwm4

def set_servo_angle(servoid, angle_deg, ms):
    if servoid >= 22:
        rg = 135
    else:
        rg = 180
    base_pwm = inits[servoid]
    pwm = int(base_pwm - (angle_deg / rg) * 1000)
    send_order([[servoid, pwm, ms]])
    current_pwms[servoid] = pwm

def parse_query(path):
    params = {}
    if '?' in path:
        _, qs = path.split('?', 1)
        for kv in qs.split('&'):
            if '=' in kv:
                k, v = kv.split('=', 1)
                params[k] = v
    return params

def handle_request(cl):
    try:
        req = cl.recv(512)
        first_line = req.split(b'\r\n', 1)[0].decode()
        _, full_path, _ = first_line.split()
        path = full_path.split('?', 1)[0]
        args = parse_query(full_path)
        
        if path == '/':
            try:
                with open('iCenterCar/web_client.html', 'rb') as f:
                    body = f.read()
                cl.send(b'HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n' + body)
            except OSError:
                cl.send(b'HTTP/1.0 404 Not Found\r\n\r\nPage not found')
        
        elif path == '/chassis':
            d = args.get('direction', 'stop')
            if d == 'up':
                car_run(car_run_speed, car_run_time)
            elif d == 'down':
                car_run(-car_run_speed, car_run_time)
            elif d == 'left':
                turn(15, 300)
            elif d == 'right':
                turn(-15, 300)
            else:
                car_stop()
            cl.send(b'HTTP/1.0 200 OK\r\n\r\nOK')
            
        elif path == '/arm':
            JOINT2SERVO = {
                1: 21,
                2: 22,
                3: 23,
                4: 26,
            }
            joint = int(args.get('joint'))
            direction = args.get('direction')
            servoid = JOINT2SERVO.get(joint)
            if servoid is None:
                cl.send(b'HTTP/1.0 400 Bad Request\r\n\r\nInvalid joint')
                return
            delta = 15 if direction == 'right' else -15
            
            print(f'{servoid} is turning by {delta}')
            clockwise_rotate(servoid, delta, 1000)

            cl.send(b'HTTP/1.0 200 OK\r\n\r\nOK')
 
        else:
            cl.send(b'HTTP/1.0 404 Not Found\r\n\r\nNot Found')
    except Exception as e:
        print('Request error:', e)
    finally:
        cl.close()

def start_socket_server():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 80))
    s.listen(5)
    print('Socket HTTP server running on port 80')
    while True:
        cl, addr = s.accept()
        handle_request(cl)
        
#3.4 处理PS2手柄输入
def loop_ps2(): 
    global arm_move_tag,car_move_tag
    global arm_servo_1_pwm,arm_servo_2_pwm,arm_servo_3_pwm,arm_servo_4_pwm
    global speed_pwm
    global current_pwms
    global my_run_speed
    global horizontal
    
    if not ps2.read_gamepad():
        return
    
    ######################这里是 “START”按键的应用示范########################## 
    if ps2.ButtonPressed('START'):
        car_servos_init()
        time.sleep(1)
        arm_servos_init()
        time.sleep(1)
        current_pwms = inits[:]
        horizontal = False
        print("Start button pressed. ")

    ######################请同学们自己补充各个按键功能 开始##########################
    if ps2.ButtonPressed('SQUARE'):
        clockwise_rotate(21, -15, 1000)
    if ps2.ButtonPressed('CIRCLE'):
        clockwise_rotate(21, 15, 1000)
    if ps2.ButtonPressed('TRIANGLE'):
        clockwise_rotate(22, -15, 1000)
    if ps2.ButtonPressed('CROSS'):
        clockwise_rotate(22, 15, 1000)
        
    if ps2.en_Pressures:
#         for button, label in zip([5, 6, 7, 8], ['Right X', 'Right Y', 'Left X', 'Left Y']):
#             if ps2.Button('L3') or ps2.Button('R3'):
#                 value = ps2.Analog(button)
#                 
#                 print(f"{label} Joystick: {value}")
        if ps2.Button('L3'):
             lx_dpwm = (ps2.Analog(7) - 128) * 1000 // 128
             ly_dpwm = (ps2.Analog(8) - 128) * 1000 // 128
             
             clockwise_fix_by_pwm(1, 1500+ly_dpwm, 200)
             clockwise_fix_by_pwm(2, 1500-ly_dpwm, 200)
             clockwise_fix_by_pwm(3, 1500+ly_dpwm, 200)
             clockwise_fix_by_pwm(4, 1500-ly_dpwm, 200)
            
             clockwise_fix_by_pwm(11, 1500+lx_dpwm, 200)
             clockwise_fix_by_pwm(12, 1500-lx_dpwm, 200)
             clockwise_fix_by_pwm(13, 1500+lx_dpwm, 200)
             clockwise_fix_by_pwm(14, 1500-lx_dpwm, 200)
             
        if ps2.Button('R3'):
            rx_dpwm = (ps2.Analog(5) - 128) * 1000 // 128
            ry_dpwm = (ps2.Analog(6) - 128) * 1000 // 128
            clockwise_fix_by_pwm(21, 1500-rx_dpwm, 200)
            clockwise_fix_by_pwm(22, 1500+ry_dpwm, 200)
            
#         if ps2.Button('L3'):
#             lx_dpwm = ps2.Analog(7) - 128
#             ly_dpwm = ps2.Analog(8) - 128
#             
#             clockwise_fix_by_pwm(1, 1500+ly_dpwm, 200)
#             clockwise_fix_by_pwm(2, 1500-ly_dpwm, 200)
#             clockwise_fix_by_pwm(3, 1500+ly_dpwm, 200)
#             clockwise_fix_by_pwm(4, 1500-ly_dpwm, 200)
#             
#             clockwise_fix_by_pwm(11, 1500+lx_dpwm, lx_dpwm)
#             clockwise_fix_by_pwm(12, 1500-lx_dpwm, lx_dpwm)
#             clockwise_fix_by_pwm(13, 1500+lx_dpwm, lx_dpwm)
#             clockwise_fix_by_pwm(14, 1500-lx_dpwm, lx_dpwm)
            
        if ps2.Button('R3'):
            rx_dpwm = (ps2.Analog(5) - 128)
            ry_dpwm = (ps2.Analog(6) - 128)
            if rx_dpwm > 16:
                clockwise_rotate(21, 5, 100)
            if rx_dpwm < -16:
                clockwise_rotate(21, -5, 100)
            if ry_dpwm > 16:
                clockwise_rotate(22, -5, 100)
            if ry_dpwm < -16:
                clockwise_rotate(22, 5, 100)
        
    if not horizontal:
        if ps2.ButtonPressed('PAD_UP'):
            run(my_run_speed, 1000)
        if ps2.ButtonPressed('PAD_DOWN'):
            run(-my_run_speed, 1000)
        if ps2.ButtonPressed('PAD_LEFT'):
            turn(15, 300)
        if ps2.ButtonPressed('PAD_RIGHT'):
            turn(-15, 300)
    else:
        if ps2.ButtonPressed('PAD_LEFT'):
            send_order([[1, 1500+my_run_speed, 1000], [2, 1500-my_run_speed, 1000], \
                        [3, 1500-my_run_speed, 1000], [4, 1500+my_run_speed, 1000]])
        if ps2.ButtonPressed('PAD_RIGHT'):
            send_order([[1, 1500-my_run_speed, 1000], [2, 1500+my_run_speed, 1000], \
                        [3, 1500+my_run_speed, 1000], [4, 1500-my_run_speed, 1000]])
        
    if ps2.ButtonPressed('SELECT'):
        if not horizontal:
            clockwise_fix(11, -95, 1000)
            clockwise_fix(12, -95, 1000)
            clockwise_fix(13, 95, 1000)
            clockwise_fix(14, 95, 1000)
        else:
            clockwise_fix(11, 0, 1000)
            clockwise_fix(12, 0, 1000)
            clockwise_fix(13, 0, 1000)
            clockwise_fix(14, 0, 1000)
        horizontal = not horizontal
        time.sleep(2)
        
        
    if ps2.ButtonPressed('L2'):
        my_run_speed += 100
    if ps2.ButtonPressed('L1'):
        my_run_speed -= 100




    ######################请同学们自己补充各个按键功能 结束##########################
        
    #四、主函数定义

def z_main_test():
    global nled,beep,key,ps2,uart
    
    nled = Mars_LED()                                    # 实例化一个led灯对象
    beep = Mars_BEEP()                                   # 实例化一个蜂鸣器对象
    key = Mars_KEY()                                     # 实例化按键对象
    uart = Mars_UART()                                   # 实例化串口对象
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid='Tsinghua-Danger', password='12345678')

   #################################此处是手柄实例化及初始化 开始#################################### 
    ps2 = Mars_PS2()                                     # 实例化手柄对象
    ps2.enablePressures()
    # 让手柄震动以表明启动完成
    error = ps2.config_gamepad(pressures=True, rumble=True)
    if error:
        print("Error configuring controller")
        while True:
            pass  # 如果配置失败，进入无限循环
    print("Found Controller, configured successful")

    # 让手柄震动以表明启动完成
    if ps2.en_Rumble:
        print("Vibrating controller for 1 second...")
        ps2.read_gamepad(True, 255)  # 启动震动
        time.sleep(1)
        ps2.read_gamepad(False, 0)  # 停止震动
        
    print('AP ifconfig:', ap.ifconfig())
   #################################此处是手柄实例化及初始化 结束#################################### 
    #初始化车子和机械臂

    #car_arm_initial()
        
    car_servos_init()
    time.sleep(1)
    arm_servos_init()
    time.sleep(1)
    
    beep.beep_on_times(3,0.1)                          # 启动完成
    
    print('main init ok')
    
    uart.uart_send_str('0,10,10\r\n')
    
    _thread.start_new_thread(start_socket_server, ())
    #################################此处是主程序进入无线循环#################################### 
    while 1:                                           # 无限循环
        loop_nled()
        loop_uart()
        loop_ps2()                                     # 手柄数据读写
        
        time.sleep(0.1)

# 程序入口
if __name__ == '__main__':
    z_main_test()
