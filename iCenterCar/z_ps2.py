# '''
# 修改信息
# 作者：郑养波
# 日期：2025年6月1日
# 优化：2025年6月23日
# 修复：2025年6月23日 - 添加退出机制
# 修复：2025年6月24日 - 更新全部代码
# '''
from machine import Pin
import time

# 常量定义
READ_DELAY_MS = 10  
SHORT_DELAY_US = 5

# 定义按钮常量
BUTTONS = {
    'SELECT': 0x0001, 'L3': 0x0002, 'R3': 0x0004, 'START': 0x0008, 'PAD_UP': 0x0010,
    'PAD_RIGHT': 0x0020, 'PAD_DOWN': 0x0040, 'PAD_LEFT': 0x0080, 'L2': 0x0100,
    'R2': 0x0200, 'L1': 0x0400, 'R1': 0x0800, 'TRIANGLE': 0x1000, 'CIRCLE': 0x2000,
    'CROSS': 0x4000, 'SQUARE': 0x8000
}

# 文件开头的注释
"""
PS2 手柄通过 SPI 总线与主控进行通信。通信过程通过四个引脚实现：DAT 用于数据输入，
CMD 用于命令输出，SEL 用于选择信号，CLK 用于发送时钟信号。

本代码实现了读取 PS2 手柄的按键信息和模拟输入，并且支持振动功能。手柄需要先配置才能正常工作。
配置过程中通过发送和接收特定的指令序列来和手柄进行同步和设定模式。

手柄可以通过读取按键状态和模拟信号输出来获取用户的输入，并且在支持振动功能的情况下可以激活马达进行振动反馈。
"""

class Mars_PS2:
    def __init__(self, dat_pin=19, cmd_pin=18, sel_pin=15, clk_pin=23):
        # 初始化引脚
        self.PS2_DAT = Pin(dat_pin, Pin.IN, Pin.PULL_UP)  # 数据输入引脚
        self.PS2_CMD = Pin(cmd_pin, Pin.OUT)              # 命令输出引脚
        self.PS2_SEL = Pin(sel_pin, Pin.OUT)              # 选择信号引脚
        self.PS2_CLK = Pin(clk_pin, Pin.OUT)              # 时钟信号引脚
        
        # 初始化内部状态变量
        self.PS2data = [0] * 21
        self.last_buttons = 0
        self.buttons = 0
        self.last_read = 0
        self.read_delay = 1
        self.controller_type = 0
        self.en_Rumble = False
        self.en_Pressures = False
    
    def _gamepad_shiftinout(self, byte):
        """发送和接收一个字节的数据，与手柄通信。
        
        通过时钟引脚逐位发送和接收数据。
        """
        tmp = 0
        for i in range(8):
            self.PS2_CMD.value(byte & (1 << i))  # 设置命令引脚的状态
            self.PS2_CLK.value(0)                # 拉低时钟信号开始传输
            time.sleep_us(SHORT_DELAY_US)        # 短暂等待
            
            # 读取数据引脚的当前值并记录
            if self.PS2_DAT.value():
                tmp |= (1 << i)
            
            self.PS2_CLK.value(1)                # 拉高时钟信号结束当前位的传输
            time.sleep_us(SHORT_DELAY_US)        # 短暂等待
        self.PS2_CMD.value(1)                    # 释放命令引脚
        time.sleep_us(SHORT_DELAY_US)            # 等待状态稳定
        return tmp

    def read_gamepad(self, motor1=False, motor2=0):
        """从手柄读取当前状态，包括按键和模拟信号。
        
        如果启用了振动，则根据参数设置手柄振动强度。
        """
        elapsed = time.ticks_ms() - self.last_read
        if elapsed > 1500:
            self.reconfig_gamepad()              # 如果读取时间过长，重新配置手柄
        if elapsed < self.read_delay:
            time.sleep_ms(self.read_delay - elapsed)

        data_to_send = [0x01, 0x42, 0, motor1, int((motor2 / 255) * 0xFF), 0, 0, 0, 0]
        extra_data = [0] * 12

        for _ in range(5):  # 尝试最多5次
            self.PS2_CMD.value(1)
            self.PS2_CLK.value(1)
            self.PS2_SEL.value(0)                # 选择手柄开始通信
            time.sleep_us(SHORT_DELAY_US)

            for i in range(9):
                self.PS2data[i] = self._gamepad_shiftinout(data_to_send[i])
            
            if self.PS2data[1] == 0x79:
                for i in range(12):
                    self.PS2data[i + 9] = self._gamepad_shiftinout(extra_data[i])
            
            self.PS2_SEL.value(1)                # 结束通信

            if (self.PS2data[1] & 0xF0) == 0x70:
                break
            
            self.reconfig_gamepad()              # 重新配置手柄
            time.sleep_ms(self.read_delay)

        if (self.PS2data[1] & 0xF0) != 0x70:
            self.read_delay = min(self.read_delay + 1, 10)

        self.last_buttons = self.buttons
        self.buttons = (self.PS2data[4] << 8) + self.PS2data[3]
        self.last_read = time.ticks_ms()
        return (self.PS2data[1] & 0xF0) == 0x70

    def config_gamepad(self, pressures=False, rumble=False):
        """配置手柄并检测其功能支持。
        
        配置压力感应和振动功能。
        """
        self.PS2_CMD.value(1)
        self.PS2_CLK.value(1)

        for _ in range(10):
            self.sendCommandString([0x01, 0x43, 0x00, 0x01, 0x00])
            time.sleep_us(SHORT_DELAY_US)

            self.PS2_CMD.value(1)
            self.PS2_CLK.value(1)
            self.PS2_SEL.value(0)                # 选择手柄
            time.sleep_us(SHORT_DELAY_US)

            temp = [self._gamepad_shiftinout(byte) for byte in [0x01, 0x45, 0x00, 0x5A, 0x5A, 0x5A, 0x5A, 0x5A, 0x5A]]

            self.PS2_SEL.value(1)
            self.controller_type = temp[3]

            self.sendCommandString([0x01, 0x44, 0x00, 0x01, 0x03, 0x00, 0x00, 0x00, 0x00])
            if rumble:
                self.sendCommandString([0x01, 0x4D, 0x00, 0x00, 0x01])
                self.en_Rumble = True
            if pressures:
                self.sendCommandString([0x01, 0x4F, 0x00, 0xFF, 0xFF, 0x03, 0x00, 0x00, 0x00])
                self.en_Pressures = True

            self.sendCommandString([0x01, 0x43, 0x00, 0x00, 0x5A, 0x5A, 0x5A, 0x5A, 0x5A])
            self.read_gamepad()

            if pressures and self.PS2data[1] == 0x79:
                break
            if self.PS2data[1] == 0x73:
                break
        
        if self.PS2data[1] not in [0x41, 0x42, 0x73, 0x79]:
            return 1  # 配置错误

        self.read_delay = 1
        return 0  # 配置成功

    def sendCommandString(self, command):
        """向手柄发送一系列命令。
        
        用于配置手柄或更新其状态。
        """
        self.PS2_SEL.value(0)  # 选择手柄
        time.sleep_us(SHORT_DELAY_US)
        for byte in command:
            self._gamepad_shiftinout(byte)
        self.PS2_SEL.value(1)  # 取消选择
        time.sleep_ms(self.read_delay)

    def reconfig_gamepad(self):
        """重新配置手柄，通常在通信中断时使用。"""
        self.sendCommandString([0x01, 0x43, 0x00, 0x01, 0x00])
        self.sendCommandString([0x01, 0x44, 0x00, 0x01, 0x03, 0x00, 0x00, 0x00, 0x00])
        if self.en_Rumble:
            self.sendCommandString([0x01, 0x4D, 0x00, 0x00, 0x01])
        if self.en_Pressures:
            self.sendCommandString([0x01, 0x4F, 0x00, 0xFF, 0xFF, 0x03, 0x00, 0x00, 0x00])
        self.sendCommandString([0x01, 0x43, 0x00, 0x00, 0x5A, 0x5A, 0x5A, 0x5A, 0x5A])

    def Button(self, button_name):
        """检查某个按钮是否被按下。
        
        返回按键是否按下的布尔值。
        """
        return not self.buttons & BUTTONS[button_name]

    def NewButtonState(self, button_name=None):
        """检查按键状态是否有变化。
        
        返回特定按钮或所有按钮的状态是否发生了变化。
        """
        if button_name:
            return bool(self.last_buttons ^ self.buttons & BUTTONS[button_name])
        return bool(self.last_buttons ^ self.buttons)

    def ButtonPressed(self, button_name):
        """检查某个按钮是否刚刚被按下。
        
        返回布尔值表示按钮是否刚刚从未按状态变为按下状态。
        """
        return self.NewButtonState(button_name) and self.Button(button_name)

    def ButtonReleased(self, button_name):
        """检查某个按钮是否刚刚被释放。
        
        返回布尔值表示按钮是否刚刚从按下状态变为释放状态。
        """
        return self.NewButtonState(button_name) and (not self.last_buttons & BUTTONS[button_name])

    def Analog(self, index):
        """获取指定索引位置的模拟量数据。
        
        用于获取摇杆或触摸板的模拟输入值。
        """
        return self.PS2data[index]

    def readType(self):
        """读取并返回手柄类型。
        
        返回值表示手柄类型的不同模式。
        """
        type_map = {0x03: 1, 0x01: 4 if self.PS2data[1] == 0x42 else 2, 0x0C: 3}
        return type_map.get(self.controller_type, 0)

    def enableRumble(self):
        """启用振动功能。
        
        发送命令激活手柄的振动马达。
        """
        self.sendCommandString([0x01, 0x43, 0x00, 0x01, 0x00])
        self.sendCommandString([0x01, 0x4D, 0x00, 0x00, 0x01])
        self.sendCommandString([0x01, 0x43, 0x00, 0x00, 0x5A, 0x5A, 0x5A, 0x5A, 0x5A])
        self.en_Rumble = True

    def enablePressures(self):
        """启用压力感应功能。
        
        配置手柄以启用对按钮的压力感应。
        """
        self.sendCommandString([0x01, 0x43, 0x00, 0x01, 0x00])
        self.sendCommandString([0x01, 0x4F, 0x00, 0xFF, 0xFF, 0x03, 0x00, 0x00, 0x00])
        self.sendCommandString([0x01, 0x43, 0x00, 0x00, 0x5A, 0x5A, 0x5A, 0x5A, 0x5A])
        self.read_gamepad()
        self.read_gamepad()
        self.en_Pressures = self.PS2data[1] == 0x79
        return self.en_Pressures

# 示例代码
if __name__ == "__main__":
    # 指定引脚号来初始化PS2X
    PS2_DAT_PIN = 19
    PS2_CMD_PIN = 18
    PS2_SEL_PIN = 15
    PS2_CLK_PIN = 23
    
    ps2x = Mars_PS2(PS2_DAT_PIN, PS2_CMD_PIN, PS2_SEL_PIN, PS2_CLK_PIN)
    error = ps2x.config_gamepad(pressures=True, rumble=True)
    if error:
        print("Error configuring controller")
        while True:
            pass  # 如果配置失败，进入无限循环

    print("Found Controller, configured successful")

    # 让手柄震动以表明启动完成
    if ps2x.en_Rumble:
        print("Vibrating controller for 1 second...")
        ps2x.read_gamepad(True, 255)  # 启动震动
        time.sleep(1)
        ps2x.read_gamepad(False, 0)  # 停止震动

    print("Controller is ready. Press START + SELECT together to exit.")
    
    while True:
        # 如果有配置错误则跳过
        if error:
            continue

        # 读取手柄数据
        if not ps2x.read_gamepad():
            continue

        # 检查是否同时按下START和SELECT键
        if ps2x.ButtonPressed('START') and ps2x.ButtonPressed('SELECT'):
            print("START and SELECT pressed together. Exiting...")
            break

        # 检查并打印每个按钮的状态
        for name in BUTTONS:
            if ps2x.Button(name):
                print(f"{name} is being held")

        # 如果启用了压力感应功能，读取并打印摇杆的模拟值
        if ps2x.en_Pressures:
            for button, label in zip([5, 6, 7, 8], ['Right X', 'Right Y', 'Left X', 'Left Y']):
                if ps2x.Button('L1') or ps2x.Button('R1'):
                    value = ps2x.Analog(button)
                    print(f"{label} Joystick: {value}")

        time.sleep_ms(READ_DELAY_MS)  # 添加小延时以减少控制台刷屏