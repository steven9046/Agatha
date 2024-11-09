import pyautogui
import cv2
import os
import numpy as np
# from loguru import logger
import time
import threading
import json
# from cnocr import CnOcr
from paddleocr import PaddleOCR
import logging

logger = logging.getLogger('ppocr')
logger.setLevel(logging.WARNING)


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
        self.pages_names = ["main_page", "round_1", "round_2", "round_3", "round_4", "round_5", "round_6", "round_7"]
        self.ocr = PaddleOCR(use_angle_cls=True, lang="ch")

        self.round_idx = 0
        self.rounds_6 = ["1/6", "2/6", "3/6", "4/6", "5/6", "最终回合"]
        self.rounds_7 = ["1/7", "2/7", "3/7", "4/7", "5/7", "6/7", "最终回合"]
        self.is_7_round = False

        self.energy = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        self.current_round = self.rounds_6[0]
        self.current_energy = None
        self.cube = None

        self.snapped = 0
        
        self.total_round = 0

        
    def loadButtons(self):
        for button_name in self.button_names:
            tmp_button = Button(button_name)
            self.buttons.append(tmp_button)

    def loadImg(self, path):
        return cv2.imread(path)
    
    def retreat(self):
        pyautogui.click(x=88, y=1166)
        time.sleep(1)
        pyautogui.click(x=587, y=938)

    def checkCube(self, app_screenshot):
        # 提取中间部分，数字所在位置
        energy_area_blue = app_screenshot[100:180, 420:480,:1] # B
        # 二值化
        ret, thresh_trunc = cv2.threshold(energy_area_blue, 200, 255, cv2.THRESH_BINARY_INV)
        # 找连通域
        num_labels, labels_im, stats, centroids = cv2.connectedComponentsWithStats(thresh_trunc, 8, cv2.CV_32S)
        # 找到联通阈面积大于 200 个像素的（那些小的是噪点）
        for i in range(1, num_labels):  # 从1开始，因为0是背景
            if stats[i][4] > 100: # 
                # print("area : ",stats[i][4])
                mask = (labels_im == i).astype(np.uint8) * 255
                ret, thresh_trunc = cv2.threshold(mask, 0, 255, cv2.THRESH_BINARY) 
                result = self.checkText(thresh_trunc)
                print("Cube: ", result)
                if result[0]:
                    self.cube = result[0][0][1][0]
                else:
                    pass
        # res = self.checkText(app_screenshot[-160:,400:500]) # 能量在中间 (1258, 900)
        # print(res)
        # self.current_energy = res[0][0][1][0]
        print("Cube: ", self.cube)        


    ## 检测能量的优先级比较高，因为能量会变化, 所以应该
    ## 这里应该是如何能够确定已经切换到下一个回合了，
    ## 放置中... 每个回合之间有这个？有阿加莎时时被动的，需要检测这个，如果是自己放牌那就直接点击一次结束以后再检测
    ## 但是如果没有放手牌，那就不会有放置中了, 这里需要设计一个比较复杂的逻辑啊

    def checkEnergy(self, app_screenshot):
        # 返回的是一个 list
        res = self.checkText(app_screenshot[-160:,400:500])[0] # 能量在中间 (1258, 900)
        print(res)
        ## res 得有内容，并且是检测出来了 [回合结束，1/6] 这种文字，才会去改当前回合数
        if res and len(res) == 2:
            ## 只有检测出变化了才会去改, 这样可以保持只修改一次回合数和能量数
            ## 主要是能量会变，所以我只需要知道回合开始时的能量就好了
            if self.current_energy != res[0][1][0]:
                if res[0][1][0] in self.energy:
                    self.current_energy = res[0][1][0]
                    print("Updating Energy: ", self.current_energy)        


    def checkRound(self, app_screenshot):
        res = self.checkText(app_screenshot[-150:,-200:])[0] # 回合数在右下角
        # print(res)
        # [
        #   [   [[37.0, 24.0], [164.0, 33.0], [161.0, 66.0], [35.0, 56.0]],   ('结束回合', 0.9246547222137451)   ], 
        #   [   [[71.0, 57.0], [125.0, 63.0], [121.0, 97.0], [66.0, 91.0]],   ('5/6', 0.9823111891746521)       ]
        # ]
        if  res and len(res) == 2:
            # print("res[1][1][0]: ", res[1][1][0])
            # print("res[0][1][0]: ", res[0][1][0])
            if res[1][1][0] in self.rounds_6 : # and res[0][1][0] == "回合结束"
                self.round_idx = self.rounds_6.index(res[1][1][0]) + 1
                self.current_round = res[1][1][0]
                self.is_7_round = False
                # print("回合中... ", self.round_idx)
            elif res[1][1][0] in self.rounds_7 : # and res[0][1][0] == "回合结束"
                self.round_idx = self.rounds_7.index(res[1][1][0]) + 1
                self.current_round = res[1][1][0]
                self.is_7_round = True
                # print("回合中... ", self.round_idx)
            # elif res[0][1][0] != "回合结束":
            #     print("放置卡牌中...")
            #     self.round_idx += 1
            # if self.current_round != res[1][1][0]:
            #     # 检测结果可能出错，这里限制一下
            #     if res[1][1][0] in self.rounds: 
            #         self.current_round = res[1][1][0]
            #         print("Updating Round: ", self.current_round)

    def checkText(self, img):
        return self.ocr.ocr(img, cls=True) # list[{dict}]

    ## 加倍的情况还是很多的，加倍不能跑！
    # total round:  125
    # 
    def checkRetreat(self, img):
        if self.buttons[1].checkExisting((286, 96, 342, 139), 0.8) :  # X = 286, Y = 96  X = 628, Y = 235
            self.snapped = 1
        if self.round_idx > 4:
            if self.is_7_round:
                print("7 回合啦，快跑！")
                self.retreat()
                return
            # if self.snapped:
            #     print("加倍啦，快跑！")
            #     self.retreat()
            #     return

    def checkFinish(self, img):
        if self.buttons[3].checkExisting((600, 1100, 900, 1258)) :
            pyautogui.click(self.buttons[3].location)
            print("click reward : ", self.buttons[3].location)
            time.sleep(1)
        if self.buttons[4].checkExisting((600, 1100, 900, 1258)):
            pyautogui.click(self.buttons[4].location)
            print("click next round: ", self.buttons[4].location) 

    def checkStart(self, img):
        if self.buttons[0].checkExisting((300, 940, 300, 200)) :
            print("click start : ", self.buttons[0].location)
            print("total round: ", self.total_round)
            pyautogui.click(self.buttons[0].location)
            time.sleep(1)
            self.round_idx = 0
            self.snapped = 0
            self.total_round += 1

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



    # app_screenshot = cv2.imread(os.path.join(os.getcwd(), 'marvel_script', 'resource', 'round_2.png'))

    # print("app_screenshot: ", app_screenshot.shape) #  (1258, 900, 3)


    # cv2.imshow('OpenCV Image', app_screenshot[-140:,400:500]) # [-150:,-200:] 这个坐标大概是结束回合的按钮
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()


    # snapWin.checkRound(app_screenshot)
    # snapWin.checkEnergy(app_screenshot)
    # snapWin.checkCube(app_screenshot)

    # snapped = 0
    while True:

        app_screenshot = pyautogui.screenshot(region=(sanp_win.left, sanp_win.top, sanp_win.width, sanp_win.height))
        app_screenshot = np.array(app_screenshot)
        app_screenshot = cv2.cvtColor(app_screenshot, cv2.COLOR_RGB2BGR)

        snapWin.checkRound(app_screenshot)

        snapWin.checkRetreat(app_screenshot)

        snapWin.checkFinish(app_screenshot)

        snapWin.checkStart(app_screenshot)
        time.sleep(1)

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