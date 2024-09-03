import pygame
from pygame.locals import *

import cv2
import mediapipe as mp

from game_objects import *
from utility import *

pygame.init()
pygame.mixer.init()

gunshot_sound = pygame.mixer.Sound('assets/pew.mp3')
bomb_sound =  pygame.mixer.Sound('assets/bomb2.mp3')

screen = pygame.display.set_mode((0,0), DOUBLEBUF | OPENGL | pygame.FULLSCREEN)
window_w = pygame.display.Info().current_w
window_h = pygame.display.Info().current_h

clock = pygame.time.Clock()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.2)
cap = cv2.VideoCapture(0)

glEnable(GL_DEPTH_TEST)
glEnable(GL_LIGHTING)
glShadeModel(GL_SMOOTH)
glEnable(GL_COLOR_MATERIAL)
glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

glEnable(GL_LIGHT0)
glLightfv(GL_LIGHT0, GL_AMBIENT, [0.5, 0.5, 0.5, 1])
glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1])

glMatrixMode(GL_PROJECTION)
gluPerspective(45, (window_w / window_h), 0.1, 50.0)

glMatrixMode(GL_MODELVIEW)
gluLookAt(0, -8, 0, 0, 0, 0, 0, 0, 1)
viewMatrix = glGetFloatv(GL_MODELVIEW_MATRIX)
glLoadIdentity()

displayCenter = [window_w // 2, window_h // 2]
mouseMove = [0, 0]
pygame.mouse.set_pos(displayCenter)

up_down_angle = 0.0

paused = False
run = True

def load_texture(filename):
    textureSurface = pygame.image.load(filename)
    textureData = pygame.image.tostring(textureSurface, "RGBA", 1)
    width = textureSurface.get_width()
    height = textureSurface.get_height()

    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, textureData)

    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

    return texture, width, height

gun_texture, gun_width, gun_height = load_texture('assets/my_gun.png')

def draw_gun():
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, gun_texture)

    viewport = glGetIntegerv(GL_VIEWPORT)

    # 오른쪽 하단에 위치시키기 위한 좌표 계산
    x = viewport[2] - gun_width * gun_scale
    y = 0

    # 2D 직교 투영으로 전환
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, viewport[2], 0, viewport[3], -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # 깊이 테스트 비활성화 (다른 3D 객체에 가려지지 않도록)
    glDisable(GL_DEPTH_TEST)

    # 블렌딩 활성화
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # 텍스처 환경 설정
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)

    # 총 이미지 그리기
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex2f(x, y)
    glTexCoord2f(1, 0)
    glVertex2f(x + gun_width * gun_scale, y)
    glTexCoord2f(1, 1)
    glVertex2f(x + gun_width * gun_scale, y + gun_height * gun_scale)
    glTexCoord2f(0, 1)
    glVertex2f(x, y + gun_height * gun_scale)
    glEnd()

    # 원래 상태로 복원
    glDisable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

    glDisable(GL_TEXTURE_2D)

player = Player(gun_width, gun_height, gunshot_sound)
target1 = Target(-1.5, 0, 0, 1, (0.5, 0.2, 0.2, 1))
target2 = Target(3, 0, 0, 1, (0.2, 0.2, 0.5, 1))
bullet_speed = 5.0
gun_scale = 1

# main loop
while cap.isOpened() and run:
    ret, frame = cap.read()
    if not ret:
        print("카메라에서 영상을 읽을 수 없습니다.")
        break

    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = cv2.flip(image, 1)
    image.flags.writeable = False

    results = hands.process(image)
    player.update(results)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                run = False
            if event.key == pygame.K_PAUSE or event.key == pygame.K_p:
                paused = not paused
                pygame.mouse.set_pos(displayCenter)
        if not paused:
            if event.type == pygame.MOUSEMOTION:
                mouseMove = [event.pos[i] - displayCenter[i] for i in range(2)]
            pygame.mouse.set_pos(displayCenter)

    if not paused:
        # Get keys
        keypress = pygame.key.get_pressed()

        # Init model view matrix
        glLoadIdentity()

        # Apply the look up and down
        up_down_angle += mouseMove[1] * 0.1
        glRotatef(up_down_angle, 1.0, 0.0, 0.0)

        # Init the view matrix
        glPushMatrix()
        glLoadIdentity()

        glRotatef(player.rotation_angle, 0.0, 1.0, 0.0)

        # Multiply the current matrix by the get the new view matrix and store the final view matrix
        glMultMatrixf(viewMatrix)
        viewMatrix = glGetFloatv(GL_MODELVIEW_MATRIX)

        # Apply view matrix
        glPopMatrix()
        glMultMatrixf(viewMatrix)

        glLightfv(GL_LIGHT0, GL_POSITION, [1, -1, 1, 0])

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glPushMatrix()

        glColor4f(0.5, 0.5, 0.5, 1)
        glBegin(GL_QUADS)
        glVertex3f(-10, -10, -2)
        glVertex3f(10, -10, -2)
        glVertex3f(10, 10, -2)
        glVertex3f(-10, 10, -2)
        glEnd()

        target1.draw()
        target2.draw()

        glPopMatrix()

        glDisable(GL_LIGHTING)
        player.draw_bullets()
        glEnable(GL_LIGHTING)

        # 추후 좀더 디벨롭한다면 target들을 리스트에 넣어놓고 하는 것도 괜찮을 듯.
        for i in range(len(player.bullets) - 1, -1, -1):
            if detect_collision((target1.x, target1.y, target1.z), target1.radius,
                                (player.bullets[i].x, player.bullets[i].y, player.bullets[i].z),
                                player.bullets[i].size):
                print("bomb!")
                bomb_sound.play()
                target1.update()
                del player.bullets[i]
            elif detect_collision((target2.x, target2.y, target2.z), target2.radius,
                                  (player.bullets[i].x, player.bullets[i].y, player.bullets[i].z),
                                  player.bullets[i].size):
                print("bomb!")
                bomb_sound.play()
                target2.update()
                del player.bullets[i]

        draw_gun()

        pygame.display.flip()
        pygame.time.wait(10)

    clock.tick(60)

pygame.quit()
