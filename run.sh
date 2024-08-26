#!/bin/sh
app_name="ti_lpc"


#./"$app_name" 

#kill `pidof bash_gc`				#kill Geany started bash_gc shell, set Geany, Edit, Preferences, Tool, Terminal: /usr/bin/urxvt -e bash_gc %c

#kill `pidof sh_gc`				#kill Geany started bash_gc shell, set Geany, Edit, Preferences, Tool, Terminal: /usr/bin/urxvt -e bash_gc %c
kill `pidof "$app_name"`

sleep 0.2

#ubuntu
gnome-terminal -e ./"$app_name"

