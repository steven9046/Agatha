from paddleocr import PaddleOCR, draw_ocr
import cv2
import os
import numpy as np
np.set_printoptions(threshold=np.inf)
np.set_printoptions(linewidth=np.inf)
# 创建PaddleOCR对象
ocr = PaddleOCR(use_angle_cls=True, lang="ch")

# 读取图片
# img_path = os.path.join(os.getcwd(), 'marvel_script', 'resource', 'round_1.png')
img_path = os.path.join(os.getcwd(), 'marvel_script', 'resource', 'next_round_page.png')
image = cv2.imread(img_path)
print(image.shape) # (1247, 887, 3) y x 

# image = cv2.cvtColor(image[:,:,:], cv2.COLOR_BGR2GRAY) 
# imageb = image[100:180, 420:480,:1] # B

# imageg = image[:,:,1:2] # G
# imager = image[:,:,2:3] # R
# clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
# image = clahe.apply(image)
# print(imageb.shape) # 80,60,1
# print(imageb[:,:,0])
# ret, thresh_trunc = cv2.threshold(imageb, 200, 255, cv2.THRESH_BINARY_INV)
# cv2.imshow('Background', thresh_trunc)
# cv2.waitKey(0)

# num_labels, labels_im, stats, centroids = cv2.connectedComponentsWithStats(thresh_trunc, 8, cv2.CV_32S)

# background = np.zeros_like(imageb)

# # 遍历每个连通域并绘制
# for i in range(1, num_labels):  # 从1开始，因为0是背景
#     print("area : ",stats[i][4])
#     if stats[i][4] > 100:
#         # print("area : ",stats[i][4])
#         mask = (labels_im == i).astype(np.uint8) * 255
#         # print(mask.shape) #
#         ret, thresh_trunc = cv2.threshold(mask, 0, 255, cv2.THRESH_BINARY) 
#         # connected_component = cv2.bitwise_and(background, background, mask=mask)  # 使用掩码提取连通域
#         cv2.imshow(f'Connected Component {i}', thresh_trunc)  # 显示连通域
#         cv2.imwrite(f'Connected_Component_{i}.png', thresh_trunc)  # 保存连通域
#         cv2.waitKey(0)
#         result = ocr.ocr(thresh_trunc, cls=True)
#         print("result: ", result)

# # 显示背景图像
# cv2.imshow('Background', background)
# cv2.waitKey(0)
# cv2.destroyAllWindows()

# while True:
# 调用ocr函数进行检测和识别
result = ocr.ocr(image[260:330,370:510], cls=True)[0]

print(result[0][1][0])

# # 将识别结果绘制到图像上
# image = draw_ocr(image, result, font_path='path_to_your_font')

# # 显示图像
# image.show()

# print("-------------------")
# print(result)
# print(len(result))
# print(len(result[0]))
# print(result[0][0][1][0])
# cv2.imshow('thresh_trunc', opened_image) # [-150:,-200:] 这个坐标大概是结束回合的按钮

# cv2.imshow('OpenCV Image B', imageb) # [-150:,-200:] 这个坐标大概是结束回合的按钮
# cv2.imshow('OpenCV Image G', imageg) # [-150:,-200:] 这个坐标大概是结束回合的按钮
cv2.imshow('OpenCV Image R', image[260:330,370:510]) # [-150:,-200:] 这个坐标大概是结束回合的按钮
cv2.waitKey(0)
cv2.destroyAllWindows()
