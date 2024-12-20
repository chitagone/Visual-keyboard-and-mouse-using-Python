import cv2
from cvzone.HandTrackingModule import HandDetector
from time import sleep
import numpy as np
import cvzone
from pynput.keyboard import Controller, Key
from pynput.mouse import Button as MouseButton, Controller as MouseController
import webbrowser
import os
import psutil

class Butt
    def __init__(self, pos, text, size=[85, 85]):
        self.pos = pos
        self.size = size
        self.text = text


def drawAll(img, buttonList):
    for button in buttonList:
        x, y = button.pos
        w, h = button.size
        cvzone.cornerRect(img, (button.pos[0], button.pos[1], button.size[0], button.size[1]),
                          20, rt=0)
        cv2.rectangle(img, button.pos, (x + w, y + h), (255, 0, 255), cv2.FILLED)
        cv2.putText(img, button.text, (x + 20, y + 65),
                    cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
    return img


def close_edge():
    """Function to close Microsoft Edge browser"""
    for proc in psutil.process_iter(['name']):
        try:
            # Check for both possible process names
            if proc.info['name'].lower() in ['msedge.exe', 'microsoftedge.exe']:
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass


def main():
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)
    cap.set(4, 720)

    youtube = 0  # Track YouTube state

    # Initialize both keyboard and mouse controllers
    keyboard = Controller()
    mouse = MouseController()

    detector = HandDetector(detectionCon=0.8, maxHands=2)  # Make sure maxHands is set to 2

    # Screen dimensions (adjust these to match your screen resolution)
    SCREEN_WIDTH = 1920
    SCREEN_HEIGHT = 1080

    # Keyboard layout
    keys = [
        ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
        ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";"],
        ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/"],
        ["SPACE", "BACKSPACE", "YOUTUBE"]
    ]

    buttonList = []
    for i in range(len(keys)):
        for j, key in enumerate(keys[i]):
            if key == "SPACE":
                buttonList.append(Button([50, 450], key, [250, 85]))
            elif key == "BACKSPACE":
                buttonList.append(Button([350, 450], key, [400, 84]))
            elif key == "YOUTUBE":
                buttonList.append(Button([850, 450], key, [400, 85]))
            else:
                buttonList.append(Button([100 * j + 50, 100 * i + 50], key))

    finalText = ""
    typingCooldown = 0
    clickCooldown = 0
    prev_hand_y = None
    scroll_sensitivity = 0.2
    two_hands_cooldown = 0  # Add cooldown for two-hand gesture

    while True:
        success, img = cap.read()
        img = cv2.flip(img, 1)

        if not success:
            print("Failed to capture frame")
            break

        hands, img = detector.findHands(img, draw=True)

        if youtube == 1:  # YouTube/Edge Mode
            if len(hands) == 2 and two_hands_cooldown == 0:  # Check if both hands are detected
                # Get indices for each hand
                hand1 = hands[0]
                hand2 = hands[1]

                # Check if both hands are showing palms (using index and middle fingers up)
                def is_palm_up(hand):
                    lmList = hand['lmList']
                    return (lmList[8][1] < lmList[5][1] and  # Index finger up
                            lmList[12][1] < lmList[9][1])  # Middle finger up

                if is_palm_up(hand1) and is_palm_up(hand2):
                    close_edge()  # Close Microsoft Edge
                    youtube = 0  # Switch back to keyboard mode
                    print("Closing Edge and switching to Keyboard Mode...")
                    finalText = ""  # Reset text
                    two_hands_cooldown = 20  # Set cooldown to prevent multiple triggers

            if two_hands_cooldown > 0:
                two_hands_cooldown -= 1

            # Rest of the YouTube/Edge mode code...
            if hands:
                for hand in hands:
                    lmList = hand['lmList']
                    if lmList:
                        # Mouse control code...
                        index_x, index_y = lmList[8][:2]
                        screen_x = np.interp(index_x, [0, 1280], [0, SCREEN_WIDTH])
                        screen_y = np.interp(index_y, [0, 720], [0, SCREEN_HEIGHT])
                        mouse.position = (screen_x, screen_y)

                        if clickCooldown == 0:
                            l = detector.findDistance(lmList[8][:2], lmList[12][:2], img)[0]
                            if l < 30:
                                mouse.click(MouseButton.left)
                                clickCooldown = 10

                        palm_y = lmList[0][1]
                        if prev_hand_y is not None:
                            y_movement = prev_hand_y - palm_y
                            middle_up = lmList[12][1] < lmList[9][1]
                            ring_up = lmList[16][1] < lmList[13][1]

                            if middle_up and ring_up:
                                if abs(y_movement) > 2:
                                    scroll_amount = int(y_movement * scroll_sensitivity)
                                    mouse.scroll(0, scroll_amount)

                        prev_hand_y = palm_y

            if clickCooldown > 0:
                clickCooldown -= 1

            # Updated instructions for exiting Edge mode
            cv2.putText(img, "Mouse Control Mode", (50, 50),
                        cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
            cv2.putText(img, "Show both palms to close Edge", (50, 100),
                        cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
            cv2.putText(img, "Hold up middle + ring fingers to scroll", (50, 150),
                        cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)

        else:  # Keyboard Mode
            img = drawAll(img, buttonList)

            if typingCooldown > 0:
                typingCooldown -= 1

            if hands:
                for hand in hands:
                    lmList = hand['lmList']
                    if lmList:
                        index_tip = lmList[8][:2]
                        middle_tip = lmList[12][:2]
                        ring_tip = lmList[16][:2]

                        for button in buttonList:
                            bx, by = button.pos
                            bw, bh = button.size

                            if bx < index_tip[0] < bx + bw and by < index_tip[1] < by + bh:
                                cv2.rectangle(img, (bx - 5, by - 5), (bx + bw + 5, by + bh + 5),
                                              (175, 0, 175), cv2.FILLED)
                                cv2.putText(img, button.text, (bx + 20, by + 65),
                                            cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)

                                l = detector.findDistance(lmList[8][:2], lmList[12][:2], img)[0]

                                if l < 30 and typingCooldown == 0:
                                    if button.text == "SPACE":
                                        keyboard.press(Key.space)
                                        finalText += " "
                                    elif button.text == "BACKSPACE":
                                        if finalText:
                                            finalText = finalText[:-1]
                                        keyboard.press(Key.backspace)
                                    elif button.text == "YOUTUBE":
                                        webbrowser.open('https://www.youtube.com')
                                        youtube = 1
                                        print("Opening YouTube...")
                                    else:
                                        keyboard.press(button.text)
                                        finalText += button.text

                                    cv2.rectangle(img, button.pos, (bx + bw, by + bh),
                                                  (0, 255, 0), cv2.FILLED)
                                    cv2.putText(img, button.text, (bx + 20, by + 65),
                                                cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
                                    typingCooldown = 10

            cv2.rectangle(img, (50, 580), (1000, 680), (175, 0, 175), cv2.FILLED)
            cv2.putText(img, finalText, (60, 650),
                        cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)

        cv2.imshow("Virtual Hand Control", img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()