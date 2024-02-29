import anki
import datetime
import json
import random
import threading
import time
import os

from aqt import gui_hooks, mw
# import the "show info" tool from utils.py
from aqt.utils import showInfo, qconnect
# import all of the Qt GUI library
from aqt.qt import *
from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt, QRect
from PyQt6.QtGui import QFont
from PyQt6 import QtWidgets

# define the XP needed to reach each level
level_xp = [0, 83, 174, 276, 388, 512, 650, 801, 969, 1154, 1358, 1584, 1833, 2107, 2411, 2746, 3115, 3523, 3973, 4470, 5018, 5624, 6291, 7028, 7842, 8740, 9730, 10824, 12031, 13363, 14833, 16456, 18247, 20224, 22406, 24815, 27473, 30408, 33648, 37224, 41171, 45529, 50339, 55649, 61512, 67983, 75127, 83014, 91721, 101333, 111945, 123660, 136594, 150872, 166636, 184040, 203254, 224466, 247886, 273742, 302288, 333804, 368599, 407015, 449428, 496254, 547953, 605032, 668051, 737627, 814445, 899257, 992895, 1096278, 1210421, 1336443, 1475581, 1629200, 1798808, 1986068, 2192818, 2421087, 2673114, 2951373, 3258594, 3597792, 3972294, 4385776, 4842295, 5346332, 5902831, 6517253, 7195629, 7944614, 8771558, 9684577, 10692629, 11805606, 13034431]

# define skill names and labels
skill_symbols = {"focus": "🎯", "curiosity": "💡", "endurance": "❤️", "recall": "💾", "speed": "⚡"}

# define a variable to keep track of the number of consecutive reviews the user has completed
consecutive_reviews = 0

# define a function to save the current state of the skills dictionary to a file
def save_skills():
    with open(skill_path + "/skills.json", "w") as f:
        json.dump(skills, f)

# define a function to load the saved state of the skills dictionary
def load_skills():
    global skills
    global skill_path
    skill_path = os.path.realpath(os.path.dirname(__file__) + "/user_files")
    try:
        with open(skill_path + "/skills.json", "r") as f:
            skills = json.load(f)
    except:
        skills = {"focus": {"level": 1, "xp": 0}, "curiosity": {"level": 1, "xp": 0}, "endurance": {"level": 1, "xp": 0}, "recall": {"level": 1, "xp": 0}, "speed": {"level": 1, "xp": 0}}

    if not all(skill in skills for skill in skill_symbols):
        # Add a dictionary entry for each missing skill
        for skill in skill_symbols:
            if skill not in skills:
                skills[skill] = {"level": 1, "xp": 0}
    
def skill_label_color_change(skill_label, duration):
    # sleep for 500 milliseconds
    time.sleep(duration)
    # reset the style sheet of the skill label
    #skill_label.setStyleSheet("color: white;")
    skill_label.setStyleSheet("")

def level_up(skill_label, skill):
    if skill_label is not None:
        # change the text color of the label to green
        skill_label.setStyleSheet("color: green;")
        skill_label.setText("{} {}".format(skill_symbols[skill], skills[skill]["level"]))
        # create a thread to update the position of the skill label
        thread = threading.Thread(target=skill_label_color_change, args=(skill_label, 5))
        thread.start()  # start the thread
    
def animate_xp_gain(skill_label, skill):
    if skill_label is not None:
        # change the text color of the label to orange
        skill_label.setStyleSheet("color: orange;")
        # create a thread to update the position of the skill label
        thread = threading.Thread(target=skill_label_color_change, args=(skill_label, 3))
        thread.start()  # start the thread

# define a function to increase the user's progress on a skill
def increase_skill_progress(skill, amount):
    if amount > 0:
        skills[skill]["xp"] += amount

        # get the dock widget
        dock = mw.findChild(QtWidgets.QDockWidget)
        # get the label that displays the skill
        skill_label = dock.findChild(QtWidgets.QLabel, f"{skill}_label")
        
        if skills[skill]["xp"] >= level_xp[skills[skill]["level"]]:
            while skills[skill]["xp"] >= level_xp[skills[skill]["level"]]:
                skills[skill]["level"] += 1
            # update the text of the label to display the updated level
            # show the level up animation for the skill label
            level_up(skill_label, skill)
        else:
            animate_xp_gain(skill_label, skill)
       
def find_and_update_skill_tool_tip(skill):
    # get the dock widget
    dock = mw.findChild(QtWidgets.QDockWidget)
    # get the label that displays the skill
    skill_label = dock.findChild(QtWidgets.QLabel, f"{skill}_label")
    if skill_label is not None:
        update_skill_tool_tip(skill_label, skill)

def update_skill_tool_tip(skill_label, skill):
    # Current xp for skill
    current_xp = skills[skill]["xp"]
    # Get the amount of xp that was required to reach current level
    xp_for_current_level = level_xp[skills[skill]["level"]-1]
    # Calculate the experience gained during this level
    xp_this_level = current_xp - xp_for_current_level
    # Calculate the total experience needed to advance to the next level
    xp_for_next_level = level_xp[skills[skill]["level"]]
    # Amount of xp required to reach next level
    xp_remaining = xp_for_next_level - current_xp
    
    # update the tool tip for the label to display the updated skill level and XP of the tool tip
    skill_label.setToolTip("Level: {} (Current XP: {}, Next Lvl: {}, Remaining: {})".format(skills[skill]["level"], skills[skill]["xp"], xp_for_next_level, xp_remaining))

# define a function to reset the consecutive reviews counter
def reset_consecutive_reviews():
    global consecutive_reviews
    consecutive_reviews = 0
 
#def on_show_question(reviewer, card, ease):
def on_show_question():
    global start_time
    start_time = datetime.datetime.now()

# define a function to handle the completion of an Anki review
def on_show_answer():
    # determine the elapsed time between when the question was shown and when the user clicked the "Show Answer" button
    global elapsed_time
    elapsed_time = datetime.datetime.now() - start_time
    global elapsed_time_seconds 
    elapsed_time_seconds = elapsed_time.total_seconds()
    # determine the amount of XP to award for the "speed" skill based on the elapsed time
    speed_xp = 0
    if elapsed_time_seconds < 10:
        speed_xp = 100
    elif elapsed_time_seconds < 15:
        speed_xp = 50
    elif elapsed_time_seconds < 30:
        speed_xp = 20

    # increase the user's progress on the "speed" skill
    increase_skill_progress("speed", speed_xp)
    # update the tool tip for the label to display the updated "speed" level and XP
    find_and_update_skill_tool_tip("speed")
    
def on_answer_button(reviewer, card, ease):
    if elapsed_time_seconds < 90:
        global consecutive_reviews
        # increment the consecutive reviews counter
        consecutive_reviews += 1
        increase_skill_progress("focus", consecutive_reviews*4)
        # get the label that displays the "focus" skill and update the tool tip label
        find_and_update_skill_tool_tip("focus")
    else:
        reset_consecutive_reviews()
    
    endurance_xp = random.sample([60, 80, 100], k=1)
    increase_skill_progress("endurance", endurance_xp[0])
    # update the tool tip for the label to display the updated "endurance" level and XP
    find_and_update_skill_tool_tip("endurance")

     # determine the amount of XP to award for the "recall" skill based on the user's answer
    recall_xp = 0
    if ease >= 2:
        recall_xp = random.sample([3,4,4,5,5,6], k=1)[0]
        recall_xp = pow(recall_xp, ease)
        # ease 1 = 0
        # ease 2 = 9, 16, 25, 36
        # ease 3 = 27, 64, 125, 216
        # ease 4 = 81, 256, 625, 1296
      
    # increase the user's progress on the "recall" skill
    increase_skill_progress("recall", recall_xp)
    find_and_update_skill_tool_tip("recall")

    # Increase curiosity xp for new cards
    if card.ivl == 0:
        curiosity_xp = random.sample([260, 325, 435, 435, 650, 650, 1300], k=1)
        # Rates = 13034431 (level 99 xp requirement) / by 50000, 40000, 30000, 20000, 10000 respectively.
        increase_skill_progress("curiosity", curiosity_xp[0])
        find_and_update_skill_tool_tip("curiosity")

# define a function to display the skill levels on the Anki home screen
def display_skills_on_home_screen():
    global label
    # create a QDockWidget and set it to be floatable
    dock = QtWidgets.QDockWidget()
    dock.setFloating(True)
    # create a horizontal layout to hold the skill labels
    layout = QtWidgets.QVBoxLayout()
    # add the skill labels to the layout
    for skill, symbol in skill_symbols.items():
        label = QtWidgets.QLabel(f"{symbol} {skills[skill]['level']}")
        label.setObjectName(f"{skill}_label")
        label.setTextFormat(QtCore.Qt.TextFormat.RichText)
        font = QtGui.QFont()
        font.setFamilies(["Noto Sans", "Noto Color Emoji"])
        font.setPointSize(11)
        label.setFont(font)
        # set the tool tip to display a message with the XP needed for the next level
        update_skill_tool_tip(label, skill)
        layout.addWidget(label)

    # create a widget to hold the layout and add it to the dock
    widget = QtWidgets.QWidget()
    widget.setLayout(layout)
    dock.setWidget(widget)
    # add the dock to the main window
    mw.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dock)
     
# pop up for debugging purposes
def debug_popup(y):
    # create a pop-up window with the specified message
    popup = QtWidgets.QMessageBox()
    popup.setWindowTitle("Debugging Pop-up")
    #popup.setWindowTitle(x)
    #popup.setText("Debugging Pop-up")
    popup.setText(y)
    popup.exec_()

class MyDialog(QtWidgets.QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        label = QtWidgets.QLabel("""🎯 Focus: Gain compounding XP (+0.5) for consecutive reviews. 90 second time limit per review.

💡 Curiosity: Gain 1-5 XP (randomly) for every card that changes from 'New' to 'Learning'.

♥ Endurance: Gain 1-3 XP (randomly) for every card reviewed.
                 
💾 Recall: Gain XP for recalling cards correctly. Easy = 5 XP, Good = 3 XP, Hard = 1 XP, Again = 0 XP

⚡ Speed: Gain XP for answering quickly. <10 seconds = 5 XP, <15 seconds = 3 XP and <30 seconds = 1 XP. 

The XP needed to level up can be viewed by hovering over the relevant skill symbol.""")
        font = QtGui.QFont()
        font.setFamilies(["Noto Sans", "Noto Color Emoji"])
        font.setPointSize(10)
        label.setFont(font)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)

def add_menu():
    def info():
        mw.dialog = MyDialog()
        mw.dialog.show()
    
    # in case the user closes the dock
    def show_dock():
        # TODO
        pass

    action = QAction("RuneScape Gamification", mw)
    qconnect(action.triggered, info)
    mw.form.menuTools.addAction(action)

# load the saved state of the skills dictionary when the Anki add-on is started
anki.hooks.addHook("profileLoaded", load_skills)
# register a hook to call the display_skills_on_home_screen function when the Anki home screen is displayed
anki.hooks.addHook("profileLoaded", display_skills_on_home_screen)
# create a submenu within the Tools menu
anki.hooks.addHook("profileLoaded", add_menu)
# register a hook to call the on_showQuestion function when a card is first displayed
anki.hooks.addHook("showQuestion", on_show_question)
#gui_hooks.card_will_show.append(on_show_question)
# register a hook to call the on_review_complete function when a review is rated
anki.hooks.addHook("showAnswer", on_show_answer)
# register a hook to call the on_review_complete function when a review is completed
gui_hooks.reviewer_did_answer_card.append(on_answer_button)
gui_hooks.reviewer_will_end.append(reset_consecutive_reviews)
# register a hook to save the skills dictionary when the Anki program is closed
anki.hooks.addHook("unloadProfile", save_skills)


