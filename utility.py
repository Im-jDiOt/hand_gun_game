import numpy as np

def detect_collision(obj1_pos, obj1_r, obj2_pos, obj2_r):
    distance = np.linalg.norm(np.array(obj1_pos) - np.array(obj2_pos))
    radius_sum = obj1_r+obj2_r
    return distance <= radius_sum






