import torch
import torchvision
print("PyTorch version:", torch.__version__)
print("Torchvision version:", torchvision.__version__)
print("CUDA is available:", torch.cuda.is_available())
import sys
import os
import numpy as np
import sys
sys.path.append("..")
from segment_anything import sam_model_registry, SamPredictor
import cv2
import matplotlib.pyplot as plt
from ultralytics import YOLO

path_to_yolo_model = path/to/yolo/model
path_to_sam_model =  path/to/sam/model

model = YOLO(path_to_yolo_model)

sam_checkpoint = path_to_sam_model
model_type = "vit_h"
sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
device = "cuda"

images_dir = path/to/image
image_files = [file for file in os.listdir(images_dir) if file.endswith('.jpg')]

def yolov8_detection(image, probability=0.7):
    results = model(image, stream=True)
    # generator of Results objects
    bounding_boxes = []
    for result in results:
        for box in result.boxes:
            if box.conf > probability:
                boundbox = box.xyxy.tolist()[0]
                bounding_boxes.append(boundbox)

    return bounding_boxes


def process_image(image, image_dir, result_dir, sam, device):
    path_image = os.path.join(image_dir, image)
    bbox = np.array(yolov8_detection(path_image))
    print(bbox)
    img = cv2.imread(path_image)

    if len(bbox) == 0:
        print("rien à voir ici")
        show_image(img)
    else:
        for i, bounding in enumerate(bbox):
            sam.to(device=device)
            predictor = SamPredictor(sam)
            predictor.set_image(img)
            masks, _, _ = predictor.predict(
                point_coords=None,
                point_labels=None,
                box=bounding[None, :],
                multimask_output=False,
            )

            show_result_image(img, masks[0], bounding, result_dir, image, i)


def show_image(img):
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    plt.show()


def show_result_image(img, mask, bounding, result_dir, image, i):
    mask_path = os.path.join(result_dir, f"{image}_mask_{i}.png")
    cv2.imwrite(mask_path, mask * 255)  # Assurez-vous que les valeurs sont dans [0, 255]

    mask_color = (0, 255, 0)  # Couleur du masque (vert ici)
    mask_alpha = 0.5  # Opacité du masque

    mask_image = (mask_alpha * np.array(mask_color) * mask[:, :, None]).astype(np.uint8)
    result_img = cv2.addWeighted(img, 1.0, mask_image, 1.0, 0)

    cv2.rectangle(result_img, (int(bounding[0]), int(bounding[1])), (int(bounding[2]), int(bounding[3])), mask_color, 2)

    result_path = os.path.join(result_dir, f"{image}_result_{i}.png")
    cv2.imwrite(result_path, result_img)
    plt.imshow(result_img)
    plt.axis('off')
    plt.show()

result_dir = "result"

if not os.path.exists(result_dir):
    os.makedirs(result_dir)

for image in image_files:
    process_image(image, images_dir, result_dir, sam, device)

"""
these functions can be useful to facilitate the display of results



def show_mask(mask, ax, random_color=False):
    if random_color:
        color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
    else:
        color = np.array([30 / 255, 144 / 255, 255 / 255, 0.6])
    h, w = mask.shape[-2:]
    mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
    ax.imshow(mask_image)


def show_points(coords, labels, ax, marker_size=375):
    pos_points = coords[labels == 1]
    neg_points = coords[labels == 0]
    ax.scatter(pos_points[:, 0], pos_points[:, 1], color='green', marker='*', s=marker_size, edgecolor='white',
               linewidth=1.25)
    ax.scatter(neg_points[:, 0], neg_points[:, 1], color='red', marker='*', s=marker_size, edgecolor='white',
               linewidth=1.25)


def show_box(box, ax):
    x0, y0 = box[0], box[1]
    w, h = box[2] - box[0], box[3] - box[1]
    ax.add_patch(plt.Rectangle((x0, y0), w, h, edgecolor='green', facecolor=(0, 0, 0, 0), lw=2))

"""
