#!/bin/sh

cd RuneScape-Gamification && zip -r ../RuneScape-Gamification.ankiaddon * -x "*skills.json" -x "*__pycache__*" -x "*meta.json" 
