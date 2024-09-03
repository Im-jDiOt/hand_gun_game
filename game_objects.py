from OpenGL.GL import *
from OpenGL.GLU import *

from collections import deque
import random
import math

sphere = gluNewQuadric()
bullet_speed = 5.0

class Target:
    def __init__(self, x, y, z, radius, color:tuple):
        self.x = x
        self.y = y
        self.z = z
        self.radius = radius
        self.color = color

    def update(self):
        self.color = (random.random(), random.random(), random.random(), 1)

    def draw(self):
        glPushMatrix()

        glTranslatef(self.x, self.z, self.y)
        glColor4f(*self.color)
        gluSphere(sphere, self.radius, 32, 16)

        glPopMatrix()

class Bullet:
    def __init__(self, x, y, z, direction):
        self.x = x
        self.y = y
        self.z = z - 8
        self.size = 0.1
        self.lifetime = 0 # 3초 뒤 삭제
        self.direction = direction

    def update(self, dt):
        self.x += self.direction[0] * bullet_speed * dt
        self.y += self.direction[1] * bullet_speed * dt
        self.z += self.direction[2] * bullet_speed * dt
        self.lifetime += dt

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.z, self.y)
        glScale(self.size, self.size, self.size)

        glColor3f(1.0, 0.0, 0.0)
        glBegin(GL_LINES)
        # 앞면
        glVertex3f(-1, -1, -1)
        glVertex3f(1, -1, -1)
        glVertex3f(1, -1, -1)
        glVertex3f(1, 1, -1)
        glVertex3f(1, 1, -1)
        glVertex3f(-1, 1, -1)
        glVertex3f(-1, 1, -1)
        glVertex3f(-1, -1, -1)
        # 뒷면
        glVertex3f(-1, -1, 1)
        glVertex3f(1, -1, 1)
        glVertex3f(1, -1, 1)
        glVertex3f(1, 1, 1)
        glVertex3f(1, 1, 1)
        glVertex3f(-1, 1, 1)
        glVertex3f(-1, 1, 1)
        glVertex3f(-1, -1, 1)
        # 연결선
        glVertex3f(-1, -1, -1)
        glVertex3f(-1, -1, 1)
        glVertex3f(1, -1, -1)
        glVertex3f(1, -1, 1)
        glVertex3f(1, 1, -1)
        glVertex3f(1, 1, 1)
        glVertex3f(-1, 1, -1)
        glVertex3f(-1, 1, 1)
        glEnd()

        glPopMatrix()

class Player:
    def __init__(self, gun_width, gun_height, gunshot_sound):
        self.pos_history = deque([-100, -100], maxlen=2)
        self.rotation_angle = 0  # Store rotation angle
        self.angle = 0
        self.bullets = []
        self.gun_width = gun_width
        self.gun_height = gun_height
        self.gunshot_sound = gunshot_sound

    def update(self, results):
        self.multi_hands = results.multi_hand_landmarks
        if self.multi_hands:
            for idx, hand_handedness in enumerate(results.multi_handedness):
                label = hand_handedness.classification[0].label
                score = hand_handedness.classification[0].score

                if label == "Left" and score >= 0.9:
                    self.left_hand(results.multi_hand_landmarks[idx])
                if label == "Right" and score >= 0.9:
                    self.right_hand(results.multi_hand_landmarks[idx])
        else: self.rotation_angle = 0

        # 총알 업데이트
        dt = 1.0 / 60.0
        for bullet in self.bullets[:]:
            bullet.update(dt)
            if bullet.lifetime > 3.0:
                self.bullets.remove(bullet)

    def left_hand(self, left_hand_landmarks):
        index_finger = left_hand_landmarks.landmark[8]

        if index_finger.x > 0.8:
            print('right')
            self.rotation_angle = 2
            self.angle += 2
        elif index_finger.x < 0.2:
            print('left')
            self.rotation_angle = -2
            self.angle -= 2
        else:
            self.rotation_angle = 0

    def right_hand(self, right_hand_landmarks):
        index_finger = right_hand_landmarks.landmark[8]

        self.pos_history.append(index_finger.y  * 100)
        if self.pos_history[1] > self.pos_history[0]*1.1:
            print("BANG!")

            angle_rad = math.radians(self.angle)
            direction = [math.sin(angle_rad), 0, math.cos(angle_rad)]

            viewport = glGetIntegerv(GL_VIEWPORT)

            bullet_x = (viewport[2] - self.gun_width) / viewport[2] * 2 - 1
            bullet_y = self.gun_height / viewport[3] * 2 - 1
            self.bullets.append(Bullet(bullet_x * math.sin(angle_rad), bullet_y * math.cos(angle_rad), 0, direction))

            self.gunshot_sound.play()

    def draw_bullets(self):
        for bullet in self.bullets:
            bullet.draw()