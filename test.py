import pyautogui
import cv2
import os
import numpy as np
# from loguru import snap_logger
import time
import threading
import json
# from cnocr import CnOcr
from paddleocr import PaddleOCR
import logging
import msvcrt


run_flag = True

ppocr_logger = logging.getLogger('ppocr')
ppocr_logger.setLevel(logging.CRITICAL)


# 配置日志
# 获取Logger实例
snap_logger = logging.getLogger(__name__)
snap_logger.setLevel(logging.DEBUG)  # 设置Logger的级别为DEBUG

# 创建一个文件处理器，并设置级别为DEBUG
current_timestamp = time.time()
# print("当前时间戳:", current_timestamp)
# 将时间戳转换为本地时间
local_time = time.localtime(current_timestamp)
# print(local_time)
# print("本地时间:", time.strftime("%Y-%m-%d-%H-%M-%S", local_time))
file_handler = logging.FileHandler('./snap_log/' + time.strftime("%Y-%m-%d-%H-%M-%S", local_time) + ".log", encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
# 创建一个日志格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# 设置文件处理器的日志格式
file_handler.setFormatter(formatter)
# 将文件处理器添加到Logger实例
snap_logger.addHandler(file_handler)
# 记录不同级别的日志
# snap_logger.debug('This is a debug message')
# snap_logger.info('This is an info message')
# snap_logger.warning('This is a warning message')
# snap_logger.error('This is an error message')
# snap_logger.critical('This is a critical message')



class BaseInfo():
    '''
    屏幕上的文字，但是不能按的，需要用 OCR 进行检测的
    '''
    def __init__(self, data, ocr_):
        self.name = data["name"]
        print("name : ", self.name)
        self.top_left =  data["tl"] # y,x
        self.height_width =  data["hw"] # h,w
        self.down_right = [self.top_left[0]+self.height_width[0], self.top_left[1]+self.height_width[1]]
        self.ocr = ocr_
        # print("top_left: ", self.top_left)
        # print("down_right: ", self.down_right)
    def checkInfo(self, screen_shot):
        # print("screen_shot : ", screen_shot.shape)
        res = self.ocr.ocr(screen_shot[self.top_left[0]:self.down_right[0],self.top_left[1]:self.down_right[1]], cls=True)
        # res = res[0]
        # cv2.imshow('OpenCV ', screen_shot)
        # cv2.imshow('OpenCV Image', screen_shot[self.top_left[0]:self.down_right[0],self.top_left[1]:self.down_right[1]])
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        return res[0][0][1][0]


### 这里需要派生多种 button
class BaseButton():
    def __init__(self, data):
        self.name = data["name"]
        print("name : ", self.name)
        self.position = data["position"]
        print("position : ", self.position)

    def click(self):
        '''
        pyautogui 的 x 是左右方向, y 是上下方向
        region 参数是 left, top, width, height 格式
        '''
        pyautogui.click(x=self.position[0], y=self.position[1])
        time.sleep(1)


class GameButton(BaseButton):
    '''
    这种按钮外观是不会变化的，我们称之为 GameButton，可以通过查找界面里有没有这个按钮来确定当前处于哪个阶段
    '''
    def __init__(self, data):
        super().__init__(data)
        self.image_path = os.path.join(os.getcwd(), 'marvel_script', 'resource', data["icon"])
        print("image_path: ", self.image_path)
        self.img = cv2.imread(self.image_path)

    def checkExisting(self, searching_region=None, searching_confidence=0.8):
        try:
            # 这里最好用 opencv 的模板匹配
            self.location = pyautogui.locateCenterOnScreen(self.image_path, grayscale=True, region=searching_region, confidence=searching_confidence)
            # print("self.location: ", self.location)
            return 1
        except pyautogui.ImageNotFoundException:
            # print("没有找到按钮")
            return 0

class InfoButton(BaseButton):
    '''
    这种按钮外观会变化，只能靠 position 位置找到
    '''
    def __init__(self, data):
        super().__init__(data)

class BattleField(BaseButton):
    '''
    地形，当然他也是一个按钮，至于信息部分还没想好怎么抽象
    '''
    def __init__(self, data):
        super().__init__(data)
        self.m_score_pos = data["m_score_pos"]
        self.e_score_pos = data["e_score_pos"]
    
class CardField(BaseButton):
    '''
    卡牌位置，当然他也是一个按钮，至于信息部分还没想好怎么抽象
    '''
    def __init__(self, data):
        super().__init__(data)

            

class SnapWin():
    def __init__(self, win, config_, logger_):

        self.logger = logger_
        self.logger.debug("Creating a SnapWin instance...")
        self.win = win  # 实例属性       

        self.config = config_

        self.ocr = PaddleOCR(use_angle_cls=False, lang="ch")

        self.game_buttons = {}
        for data in self.config["game_buttons"]:
            self.game_buttons[data["name"]] = GameButton(data)
        
        self.round_idx = 0
        self.rounds_6 = ["1/6", "2/6", "3/6", "4/6", "5/6", "最终回合"]
        self.rounds_7 = ["1/7", "2/7", "3/7", "4/7", "5/7", "6/7", "最终回合"]
        self.is_7_round = False

        self.energy = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        self.current_round = self.rounds_6[0]
        self.current_energy = None
        self.cube = None

        self.snapped = 0
        
        self.total_games = 0

        self.battle_fields = {}
        for data in self.config["battle_fields"]:
            self.battle_fields[data["name"]] = BattleField(data)

        self.card_fields = {}
        for data in self.config["cards_fields"]:
            self.card_fields[data["name"]] = CardField(data)

        self.info_buttons = {}
        for data in self.config["info_buttons"]:
            self.info_buttons[data["name"]] = InfoButton(data)

        self.info_areas = {}
        for data in self.config["info_areas"]:
            self.info_areas[data["name"]] = BaseInfo(data, self.ocr)            
    
    def retreat(self):
        self.game_buttons["game_retreat"].click()
        time.sleep(1)
        self.game_buttons["game_confirm_retreat"].click()

    # def checkCube(self, app_screenshot):
    #     # 提取中间部分，数字所在位置
    #     energy_area_blue = app_screenshot[100:180, 420:480,:1] # B
    #     # 二值化
    #     ret, thresh_trunc = cv2.threshold(energy_area_blue, 200, 255, cv2.THRESH_BINARY_INV)
    #     # 找连通域
    #     num_labels, labels_im, stats, centroids = cv2.connectedComponentsWithStats(thresh_trunc, 8, cv2.CV_32S)
    #     # 找到联通阈面积大于 200 个像素的（那些小的是噪点）
    #     for i in range(1, num_labels):  # 从1开始，因为0是背景
    #         if stats[i][4] > 100: # 
    #             # print("area : ",stats[i][4])
    #             mask = (labels_im == i).astype(np.uint8) * 255
    #             ret, thresh_trunc = cv2.threshold(mask, 0, 255, cv2.THRESH_BINARY) 
    #             result = self.checkText(thresh_trunc)
    #             # print("Cube: ", result)
    #             if result[0]:
    #                 self.cube = result[0][0][1][0]
    #             else:
    #                 pass
    #     # res = self.checkText(app_screenshot[-160:,400:500]) # 能量在中间 (1258, 900)
    #     # print(res)
    #     # self.current_energy = res[0][0][1][0]
    #     # print("Cube: ", self.cube)        


    ## 检测能量的优先级比较高，因为能量会变化, 所以应该
    ## 这里应该是如何能够确定已经切换到下一个回合了，
    ## 放置中... 每个回合之间有这个？有阿加莎时时被动的，需要检测这个，如果是自己放牌那就直接点击一次结束以后再检测
    ## 但是如果没有放手牌，那就不会有放置中了, 这里需要设计一个比较复杂的逻辑啊

    # def checkEnergy(self, app_screenshot):
    #     # 返回的是一个 list
    #     res = self.checkText(app_screenshot[-160:,400:500])[0] # 能量在中间 (1258, 900)
    #     # print(res)
    #     ## res 得有内容，并且是检测出来了 [回合结束，1/6] 这种文字，才会去改当前回合数
    #     if res and len(res) == 2:
    #         ## 只有检测出变化了才会去改, 这样可以保持只修改一次回合数和能量数
    #         ## 主要是能量会变，所以我只需要知道回合开始时的能量就好了
    #         if self.current_energy != res[0][1][0]:
    #             if res[0][1][0] in self.energy:
    #                 self.current_energy = res[0][1][0]
    #                 # print("Updating Energy: ", self.current_energy)        


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
                self.last_round_idx = self.round_idx
                self.round_idx = self.rounds_6.index(res[1][1][0]) + 1
                self.current_round = res[1][1][0]
                self.is_7_round = False
                # print("回合中... ", self.round_idx)
            elif res[1][1][0] in self.rounds_7 : # and res[0][1][0] == "回合结束"
                self.round_idx = self.rounds_7.index(res[1][1][0]) + 1
                self.current_round = res[1][1][0]
                self.is_7_round = True
                # print("回合中... ", self.round_idx)
            if self.last_round_idx != self.round_idx: # 回合变了打印一次就行了
                self.logger.debug(f"回合中... {self.round_idx}")
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
    # 阿加莎被丢弃了或者删除了会自动撤退
    def checkRetreat(self, img):
        if self.game_buttons["game_snap"].checkExisting((286, 96, 342, 139), 0.8) :  # X = 286, Y = 96  X = 628, Y = 235
            self.snapped = 1
        if self.round_idx > 4:
            if self.is_7_round:
                self.logger.warning("7 回合啦，快跑！")
                self.retreat()
                return
            # if self.snapped:
            #     print("加倍啦，快跑！")
            #     self.retreat()
            #     return

    def checkFinish(self, img):
        if self.game_buttons["game_get_reward"].checkExisting((600, 1100, 900, 1258)) :
            self.game_buttons["game_get_reward"].click()
            time.sleep(1)

        if self.game_buttons["game_next_game"].checkExisting((600, 1100, 900, 1258)):
            res = self.info_areas["game_result"].checkInfo(img)
            self.logger.debug("Game result: " + res)
            self.game_buttons["game_next_game"].click()
            self.logger.debug(f"Click next game.")

    def checkStart(self, img):
        if self.game_buttons["game_start"].checkExisting((300, 940, 300, 200)) :
            self.logger.debug(f"Click start game.")
            self.logger.debug(f"Total games: {self.total_games}")
            self.game_buttons["game_start"].click()
            time.sleep(1)
            self.round_idx = 0
            self.snapped = 0
            self.total_games += 1

def get_screen():
    screenshot = pyautogui.screenshot()
    image_np = np.array(screenshot)
    return image_np

def resetWindow(win):
    snap_logger.debug("Resize sanp window to 900x1258 and mover to 0,0")
    win.resizeTo(900, 1258)
    win.moveTo(0, 0)

# 需要监控当前游戏状态
# 1. 第几个回合了
# 2. 是否有加倍？
# 
# def winStatusMonitoring(win):
#     while True:
        
def terminate_loop():
    global run_flag
    while True:
        if msvcrt.kbhit():  # 检查键盘是否有按键按下
            key = msvcrt.getch()  # 读取按键
            if key.decode().upper() == 'Q':
                snap_logger.warning("Pressing Q to terminate!")
                run_flag = False
                print("run_flag :", run_flag)
                break

def main_loop():
    global run_flag
    while run_flag:
        # snap_logger.warning("looping ...")
        app_screenshot = pyautogui.screenshot(region=(sanp_win.left, sanp_win.top, sanp_win.width, sanp_win.height))
        app_screenshot = np.array(app_screenshot)
        app_screenshot = cv2.cvtColor(app_screenshot, cv2.COLOR_RGB2BGR)
        # app_screenshot = cv2.imread(os.path.join(os.getcwd(), 'marvel_script', 'resource', 'next_round_page.png'))

        snapWin.checkRound(app_screenshot)

        snapWin.checkRetreat(app_screenshot)

        snapWin.checkFinish(app_screenshot)

        snapWin.checkStart(app_screenshot)
        time.sleep(1)

        # # 打印鼠标的位置
        # currentMouseX, currentMouseY = pyautogui.position()        
        # print(f"当前鼠标位置：X = {currentMouseX}, Y = {currentMouseY}") # 799, Y = 1167


if __name__ == "__main__":
    snap_logger.info('Hello Snap!')
    screen_width, screen_height = pyautogui.size()
    snap_logger.debug(f"Screen size: {screen_width}x{screen_height}")
    snap_logger.debug(f"Current working directory: " + os.getcwd())

    snap_window_name = "SnapCN"
    # allWindows = pyautogui.getAllWindows()
    allTitles = pyautogui.getAllTitles() # SnapCN
    if snap_window_name not in allTitles:
        snap_logger.error("SnapCN is not activated!!!")
    else:
        sanp_win = pyautogui.getWindowsWithTitle(snap_window_name)[0]
        resetWindow(sanp_win)

        snap_logger.debug("Activate snap window.")
        sanp_win.activate()
        
        time.sleep(2) # 等待窗口切换到前台
        file_path = "./marvel_script/resource/config.json"
        with open(file_path, 'r', encoding='utf-8') as file:
            config_file = json.load(file)
        snapWin = SnapWin(sanp_win, config_file, snap_logger)


    # app_screenshot = cv2.imread(os.path.join(os.getcwd(), 'marvel_script', 'resource', 'round_2.png'))
    # print("app_screenshot: ", app_screenshot.shape) #  (1258, 900, 3)
    # cv2.imshow('OpenCV Image', app_screenshot[-140:,400:500]) # [-150:,-200:] 这个坐标大概是结束回合的按钮
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    terminate_loop_thread = threading.Thread(target=terminate_loop)
    terminate_loop_thread.start()


    main_loop_thread = threading.Thread(target=main_loop)
    main_loop_thread.start()
    
    terminate_loop_thread.join()
    main_loop_thread.join()

    # currentMouseX, currentMouseY = pyautogui.position()
    # # region=(600, 1100, 900, 1258)
    # # 打印鼠标的位置
    # print(f"当前鼠标位置：X = {currentMouseX}, Y = {currentMouseY}") # 799, Y = 1167













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