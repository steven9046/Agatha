import pyautogui
import cv2
import os
import numpy as np
from loguru import logger
import time
import threading
import json

regions = [(600, 1100, 900, 1258)]

class Button():
    def __init__(self, name):
        self.name = name
        print("name : ", name)
        self.image_path = os.path.join(os.getcwd(), 'marvel_script', 'resource', name + '.png')
        print("image_path: ", self.image_path)
        self.img = cv2.imread(self.image_path)
        # self.location = pyautogui.locateCenterOnScreen(self.image_path, grayscale=True, confidence=0.5)
        # if self.location:
        #     # 移动鼠标到按钮中心并点击
        #     # pyautogui.click(self.location)
        #     print(self.location)
        # else:
        #     print("按钮未找到")
    
    # pyautogui 的 x 是左右方向, y 是上下方向
    # region 参数是 left, top, width, height 格式
    def checkExisting(self, searching_region=None, searching_confidence=0.8):
        try:
            self.location = pyautogui.locateCenterOnScreen(self.image_path, grayscale=True, region=searching_region, confidence=searching_confidence)
            # print("self.location: ", self.location)
            return 1
        except pyautogui.ImageNotFoundException:
            # print("没有找到按钮")
            return 0
    
 

class SnapWin():
    def __init__(self, win):
        self.win = win  # 实例属性
        self.buttons = []
        self.button_names = ["start_button", "snap", "giveup_button", "get_reward", "next", "confirm_retreat"]
        self.pages_names = ["main_page", "searching_player", "round_1", "round_2", "round_3", "round_4", "round_5", "round_6", "round_7"]
        self.current_page = None
    def loadButtons(self):
        for button_name in self.button_names:
            tmp_button = Button(button_name)
            self.buttons.append(tmp_button)

    def loadImg(self, path):
        return cv2.imread(path)
    
    # def locateButtons(self):
    #     for button in self.buttons:
    #         x,y = 
    #         button.

def get_screen():
    screenshot = pyautogui.screenshot()
    image_np = np.array(screenshot)
    return image_np

def resetWindow(win):
    win.resizeTo(900, 1258)
    win.moveTo(0, 0)

# 需要监控当前游戏状态
# 1. 第几个回合了
# 2. 是否有加倍？
# 
# def winStatusMonitoring(win):
#     while True:
        

if __name__ == "__main__":
    print("hello, marvel!")
    screen_width, screen_height = pyautogui.size()
    print(f"Screen size: {screen_width}x{screen_height}")
    print("Current working directory:", os.getcwd())

    snap_window_name = "SnapCN"
    # allWindows = pyautogui.getAllWindows()
    # print(allWindows)
    allTitles = pyautogui.getAllTitles() # SnapCN
    if snap_window_name not in allTitles:
        logger.error("SnapCN is not activated!!!")
    else:
        sanp_win = pyautogui.getWindowsWithTitle(snap_window_name)[0]
        resetWindow(sanp_win)
        sanp_win.activate()
        time.sleep(2) # 等待窗口切换到前台
        snapWin = SnapWin(sanp_win)
        snapWin.loadButtons()

    # thread = threading.Thread(target=thread_function, args=("1",))


    # app_screenshot = pyautogui.screenshot(region=(sanp_win.left, sanp_win.top, sanp_win.width, sanp_win.height))
    # print(type(app_screenshot))
    # app_screenshot = np.array(app_screenshot)
    # app_screenshot = cv2.cvtColor(app_screenshot, cv2.COLOR_RGB2BGR)
    # cv2.imshow('OpenCV Image', app_screenshot)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    snapped = 0
    while True:
        #2. 查看当前有没有加倍, 如果有加倍就撤退
        if snapped:
            pyautogui.click(x=88, y=1166)
            time.sleep(1)
            pyautogui.click(x=587, y=938)
            snapped = 0
            # if snapWin.buttons[5].checkExisting(searching_confidence=0.6):
            #     pyautogui.click(snapWin.buttons[5].location)
            #     snapped = 0
            # continue
        
        # 3.查看有没有领取奖励按钮，如果有就点一下，然后再点下一步  
        if snapWin.buttons[3].checkExisting((600, 1100, 900, 1258)) :
            pyautogui.click(snapWin.buttons[3].location)
            print("click reward : ", snapWin.buttons[3].location)
        elif snapWin.buttons[4].checkExisting((600, 1100, 900, 1258)):
            pyautogui.click(snapWin.buttons[4].location)
            print("click next round: ", snapWin.buttons[4].location) 
        elif snapWin.buttons[1].checkExisting((286, 96, 342, 139), 0.8) :  # X = 286, Y = 96  X = 628, Y = 235
            # snapWin.buttons[2].checkExisting((600, 1100, 900, 1258)) # X = 14, Y = 1101 X = 222, Y = 1230
            # pyautogui.click(x=88, y=1166) # 下一回合才能点
            snapped = 1
            # print("click withdraw: ", snapWin.buttons[2].location)
        # 1. 查看当前是否是标题界面，如果是则点击开始
        elif snapWin.buttons[0].checkExisting((300, 940, 300, 200)) :
            print("click start : ", snapWin.buttons[0].location)
            pyautogui.click(snapWin.buttons[0].location)
        # break

    currentMouseX, currentMouseY = pyautogui.position()
    # region=(600, 1100, 900, 1258)
    # 打印鼠标的位置
    print(f"当前鼠标位置：X = {currentMouseX}, Y = {currentMouseY}") # 799, Y = 1167













    # #### 抓屏幕截图
    # # print("title_img shape: ", title_img.shape)
    # screenshot = get_screen()
    # # print(type(screenshot))
    # # print(screenshot.mode) # RGB
    # # print("image_np shape: ", image_np.shape)

    # #### 在截图中找到 标题框 位置
    # result = cv2.matchTemplate(screenshot, title_img, cv2.TM_CCOEFF_NORMED)
    # # 寻找最佳匹配位置
    # min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
   
    # if max_val > 0.8:  # 这里的阈值可以根据实际情况调整
    #     # # 绘制矩形框
    #     # top_left = max_loc
    #     # bottom_right = (top_left[0] + w, top_left[1] + h)
    #     # cv2.circle(screenshot, min_loc, 10, (0, 255, 0), 5)# 这个 min 不能用
    #     cv2.circle(screenshot, max_loc, 10, (0, 255, 0), 5) 
    #     title_x = max_loc[0] + 3
    #     title_y = max_loc[1] + 3
    #     print(max_loc)
        
    #     pyautogui.moveTo(title_x, title_y)

    # cv2.imshow('Detected Template', snapWin.buttons[0].img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()