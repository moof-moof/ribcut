
"""
    Copyright (C) <2008>  <John Thornton>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http:#www.gnu.org/licenses/>.


2008 to 2020: Additions and modifications by the Swarfer et al.
2021-12-20: This specialised version for a rib-cutter by Phugoid Floyd.

"""


 
from tkinter import *
from math import *
from tkinter import font
from tkinter.font import Font
from tkinter.simpledialog import *
from tkinter.filedialog import *
import configparser
from decimal import *
import tkinter.messagebox
import os
import glob
import string
import re
import numpy as np
import sys

########################
version_number = 2.01 ##
########################


class Application(Frame):
    
    
    def __init__(self, master=None):
        Frame.__init__(self, master, bd=1, padx=10)
        self.grid()
        self.pack()
        self.createMenu()
        self.ext = '.nc'
        self.inifile = os.path.join('.','ribbit.ini')
        
        try:
            self.DatDir = self.GetIniData(self.inifile, 'Directories', 'DatFiles')
        except:  # If not exists; use a default value
            self.DatDir = os.path.join('.', 'coord')
            self.WriteIniData(self.inifile, 'Directories', 'DatFiles', self.DatDir)

        try:
            self.NcFileDirectory = self.GetIniData(self.inifile, 'Directories', 'NcFiles')
        except:
            tkinter.messagebox.showinfo('Missing INI Data', 'You must set the\n' \
                'G-code File Directory\n' \
                'before saving a file.\n' \
                'Go to Edit/G-code Directory\n' \
                'in the menu to set this option')
            return
           
        # Pad rows of canvas
        for row in range(1,9):   
            self.rowconfigure(row, pad=5)    
        
        self.createWidgets()
        
        # Centre the window
        self.update_idletasks()
        width           = self.winfo_width()
        frm_width       = self.winfo_rootx() - self.winfo_x()
        win_width       = width + 2 * frm_width
        height          = self.winfo_height()
        titlebar_height = self.winfo_rooty() - self.winfo_y()
        win_height      = height + titlebar_height + frm_width
        x = self.winfo_screenwidth()
        y = self.winfo_screenheight() 

        try:   # Find out autoload preference
            auto = self.GetIniData(self.inifile,'autoload', 'load_or_not')

            print('auto is: ', auto, '\n')
            if auto == '1':
                try:   # Read the last saved model
                    modelname = self.GetIniData(self.inifile,'autoload', 'model')
                    filename  = os.path.join(self.NcFileDirectory, modelname + '.ini')
                    if os.path.exists(filename):
                        self.ReadModel(filename)
                except:
                    pass
        except:
            pass


    def createMenu(self):
        
        self.menu = Menu(self)                                  # Create the Menu base
        self.master.config(menu = self.menu)                    # Add the Menu
        self.FileMenu = Menu(self.menu,tearoff = FALSE)         # Create our File menu
        self.menu.add_cascade(label = 'File', menu = self.FileMenu) # Add our Menu to Base Menu
        self.FileMenu.add_command(label = 'New',                # Add items to the File menu
                                  foreground = 'Silver',  
                                  activeforeground = 'Silver',
                                  activebackground = '#EDECEB',
                                  command=self.Simple
        )
        self.FileMenu.add_command(label = 'Open', 
                                  foreground = 'Silver',  
                                  activeforeground = 'Silver',
                                  activebackground = '#EDECEB',
                                  command=self.Simple
        )
        self.FileMenu.add_separator()
        self.FileMenu.add_command(label = 'Quit', command=self.quit)

        self.EditMenu = Menu(self.menu, tearoff =FALSE)
        self.menu.add_cascade(    label = 'Edit', menu=self.EditMenu)
        self.EditMenu.add_command(label = 'Copy', command=self.CopyClpBd)
        self.EditMenu.add_command(label = 'Select All', command=self.SelectAllText)
        self.EditMenu.add_command(label = 'Delete All', command=self.ClearTextBox)
        self.EditMenu.add_separator()
        self.EditMenu.add_command(label = 'G-Code Directory', command=self.NcFileDirectory)
        self.EditMenu.add_command(label = 'DAT (Airfoils) Directory', command=self.DatFileDirectory)

        self.ModelMenu = Menu(self.menu,tearoff=FALSE)
        self.menu.add_cascade(     label = 'Model', menu=self.ModelMenu)
        self.ModelMenu.add_command(label = 'Load Model', command=self.LoadModel)
        self.ModelMenu.add_command(label = 'Save Model', command=self.SaveModel)


        self.HelpMenu = Menu(self.menu,tearoff =FALSE )
        self.menu.add_cascade(    label = 'Help', menu=self.HelpMenu)
        self.HelpMenu.add_command(label = 'About', command=self.HelpAbout)
    

    def createWidgets(self):
        self.sp1 = Label(self)
        self.sp1.grid(row=0)
        
        """~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Model Name ~~~~~~~"""
        self.st1 = Label(self, text = 'Model name ')
        self.st1.grid(row = 1, column = 0, sticky = E)
        self.ModelNameVar = StringVar()
        self.ModelNameVar.set('default')
        self.ModelName = Entry(self, width = 22, bg = 'white', textvariable=self.ModelNameVar)
        self.ModelName.grid(row = 1, column = 1, sticky = W)
        self.ModelName.focus_set()

        """~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Airfoil data ~~~~~~~~"""
        self.img51 = PhotoImage(file="img/shoutout_square.gif")
        self.img51 = self.img51.subsample(2)
        self.st51 = Label(self, image=self.img51)
        self.st51.image = self.img51
        self.st51.grid(row=4, column=0, sticky = W)
        
        self.st52 = Label(self, text='Airfoildata ')
        self.st52.grid(row = 4, column = 0, sticky = E)
             
        self.rootScrollbar = Scrollbar(self, orient=VERTICAL)
        self.Profilelistbox = Listbox(
            self,
            exportselection = 0, 
            height = 12, 
            width = 22,
            bg = 'white', 
            yscrollcommand = self.rootScrollbar.set
        )
        self.Profilelistbox.grid(row = 4, column = 1, sticky = W)
        self.Profilelistbox.configure(justify = RIGHT, borderwidth = '2', foreground = 'Blue')

        self.profiles = glob.glob(os.path.join(self.DatDir, '*.dat'))
        self.profiles.sort()

        for item in self.profiles:
           nitem = str.replace(item,self.DatDir + os.sep,'') # Erase filepath except actual filename
           self.Profilelistbox.insert(END, nitem)
        if (len(self.profiles) > 0):
           self.Profilelistbox.selection_set(0)
           
        """~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Scrollbar ~~~~~~~~~~"""
        self.rootScrollbar.config(command=self.Profilelistbox.yview)
        self.rootScrollbar.grid(row=4,column=2, sticky=N+S, pady = 5)
        
        """~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Chord ~~~~~~~~~~"""
        self.st3 = Label(self, text='Chord length ')
        self.st3.grid(row=5, column=0, sticky=E)
        self.ChordVar = StringVar()
        self.ChordVar.set('100')
        self.Chord = Entry(self, width=7, bg='white', textvariable=self.ChordVar)
        self.Chord.grid(row=5, column=1, sticky=W)
        self.Chord.configure(justify='right')
        
        """~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Autoload? ~~~~~~~~~"""
        self.aTick = Label(self, text='    Autoload?\n(Needs a Save)')
        self.aTick.grid(row=5, column=1, rowspan=2, sticky=NE)  # rowspan=2 means rows=5+6

        self.AutoVar = IntVar()
        Atick = Checkbutton(self, variable = self.AutoVar, highlightbackground='Black')
        Atick.grid(row=5, column=2, sticky=E)
        
        """~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Trailing Edge ~~~~~~~"""
        self.st9 = Label(self, text='TE thickness  (mm) ')
        self.st9.grid(row=6, column=0, sticky=E)
        self.TrailingEdgeLimitVar = StringVar()
        self.TrailingEdgeLimitVar.set(1)
        self.TrailingEdgeLimit = Entry(
            self, 
            width=7, 
            bg='white', 
            textvariable=self.TrailingEdgeLimitVar)
            
        self.TrailingEdgeLimit.grid(row=6, column=1, sticky=W)
        self.TrailingEdgeLimit.configure(justify='right')
        
        # self.img91 = PhotoImage(file="images/termik23.gif")
        # self.img91 = self.img91.subsample(1)
        # self.st91 = Label(self, image=self.img91)
        # self.st91.image = self.img91
        # self.st91.grid(row=6, column=2, rowspan=2, columnspan=2, sticky=W)
        
        """~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Kerf width ~~~~~~"""
        self.st10 = Label(self, text='Kerf width (mm) ')
        self.st10.grid(row=7, column=0, sticky=E)
        self.KerfWidthVar = StringVar()
        self.KerfWidthVar.set(1)
        self.KerfWidth = Entry(
            self, 
            width=7,
            bg='white', 
            textvariable=self.KerfWidthVar)
                        
           
        self.KerfWidth.grid(row=7, column=1, sticky=W)
        self.KerfWidth.configure(justify='right')
        
        """~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Feedrate ~~~~~~~~"""
        self.st12 = Label(self, text='Feedrate (mm/min) ')
        self.st12.grid(row=8, column=0, sticky=E)
        self.FeedrateVar = StringVar()
        self.FeedrateVar.set(50)
        self.Feedrate = Entry(
            self, 
            width=7, 
            bg='white', 
            textvariable=self.FeedrateVar)
            
        self.Feedrate.grid(row=8, column=1, sticky=W)
        self.Feedrate.configure(justify='right')
        
        """~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ F-words ~~~~~~~~~"""
        self.fTick = Label(self, text='F-words? ')
        self.fTick.grid(row=8, column=1, sticky=E)
        self.FwordVar = IntVar()
        Ftick = Checkbutton(self, variable = self.FwordVar, highlightbackground='Black')
        Ftick.grid(row=8, column=2, sticky=E)

        """~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Units ~~~~~~~~~~"""
        self.st14=Label(self,text='Units for gcode ')
        self.st14.grid(row=9,column=0, sticky=E)
        UnitOptions=[('Inch',1,'E'),('mm',0,'W')]
        self.UnitVar = IntVar()
        for text, value, side in UnitOptions:
            Radiobutton(self, 
                        highlightbackground='black', 
                        text=text,
                        value=value, 
                        variable=self.UnitVar,
                        indicatoron=0, 
                        width=6,
            ).grid(row=9, column=1,sticky=side)
            
        self.UnitVar.set(0)

        self.spacer3 = Label(self, text='')
        self.spacer3.grid(row=10, column=0, columnspan=5)
        
        """~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ gcode block ~~~~~~~"""
        self.monitor = Text(self,width=40,height=15, bg='#BDE5D7', bd=3)
        self.monitor.grid(row=11, column=0, columnspan=4, sticky=E+W+N+S,pady=5)
        self.tbscroll = Scrollbar(self,command = self.monitor.yview)
        self.tbscroll.grid(row=11, column=4, sticky=N+S+W)
        self.monitor.configure(yscrollcommand = self.tbscroll.set)
        

        """~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Bottom Row Buttons ~~~~~~~"""
        ## Assure this list exist, so that pressing [Save] before [Generate] does not cause crash
        self.g_code_candidate = list()

        typo = Font(family = 'DejaVue Sans', size = 10, weight = 'bold')
        
        self.GenButton = Button(
            self, 
            text = '1 Generate Gcode', 
            justify = CENTER, 
            command = self.GenerateGCode, 
            font = typo)
        self.GenButton.grid(row = 12, column = 0)

        self.WriteButton = Button(
            self, 
            text = '2 Write to File', 
            justify = CENTER, 
            command = self.WriteToNcFile, 
            font = typo)
        self.WriteButton.grid(row = 12, column = 1)
        
        self.quitButton = Button(
            self, 
            text = '  Quit  ', 
            justify = CENTER,
            command = self.MyQuit, 
            font = typo)
        self.quitButton.grid(row = 12, column = 3 ,pady = 8)


    def MyQuit(self):
        self.quit()
 

    def Format(self ,val, dec):
        s = '%0.' + str(int(dec)) + 'f'
        return s % val


    def GetWValues(self):
        self.modelname = self.ModelNameVar.get()

        self.chord       = self.FToD(self.ChordVar.get())
        items            = self.Profilelistbox.curselection()
        self.profilefile = self.Profilelistbox.get(items[0])
        self.trail       = self.FToD(self.TrailingEdgeLimitVar.get())
        self.feedrate    = self.FToD(self.FeedrateVar.get())
        if self.feedrate == 0:
           self.feedrate = 1
           self.monitor.insert(END,'WARNING: feedrate cannot be ZERO\n')
        
        self.kerfwidth = self.FToD(self.KerfWidthVar.get())
        self.half_kerf = float(self.KerfWidthVar.get())/2 

        self.unit = self.UnitVar.get()
        if self.unit:
           self.units = 'in.'
        else:
           self.units = 'mm'


    def Header(self,alist):

        if self.UnitVar.get() == 1:  
            dec = 3        # 0.123 "
        else:
            dec = 1        # 0.1 mm
        
        ##alist.append('%\n')        ## Is the % char/symbol recognised by all gcode interpreters?
        alist.append('(LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL)\n')
        alist.append('(Modelname ' + self.modelname + ')\n')
        alist.append('(Foil-file ' + self.profilefile  + ')\n')
        alist.append('(Chord ' + self.Format(self.chord, dec) + ')\n')
        alist.append('(Trail-edge ' + self.Format(self.trail, dec)  + ')\n')
        alist.append('(Kerf width ' + self.Format(self.kerfwidth, dec)  + ')\n')
        
        if self.FwordVar.get() == 1:
            alist.append('(Feedrate ' + self.Format(self.feedrate,dec)  + ')\n')
        if (self.unit == 0):
           alist.append('(Unit millimeter)\n')
        else:
           alist.append('(unit inch)\n')
           
        alist.append('(NOTE 0,0 (origo) is the profile\'s datum point)\n')
        alist.append('(Generated by RibCut.py.)\n(Codebase by David the Swarfer 2017, modified by Fugoid Floyd 2021 )\n')
        alist.append('(LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL)\n')



    def GenerateGCode(self):
        """ Generates the gcode file as a string list, ultimately """
        
        self.g_code_candidate = []
        self.monitor.delete("1.0",END)
        self.GetWValues()
        self.chordlength = self.chord

        self.monitor.insert(END,  "\n   Datafile:          " + self.profilefile + '\n')

        if not(os.path.exists(self.profilefile)):
            self.profilefile =  os.path.join(self.DatDir, self.profilefile)

        """ Start at trailing edge = 0,0,
            then feed top surface,
            then bottom surface,
            then feed out at TE again.              """

        with open(self.profilefile) as f:
            self.profile = f.read().splitlines()

        self.profile = self.stripfile(self.profile) # Clean out comment lines etc, and save as self.profile
        self.RibRipper()                            # Converts the self.profile data and generates the self.rib_ list
        self.stations = len(self.rib_)              # We can now use the self.rib_ data for our mundane purposes
        
        self.monitor.insert(END,    "   # Stations:        " + str(self.stations) + '\n')
        self.monitor.insert(END,    "   Chord:             " + str(self.chordlength) + '\n')
        
        if (self.trail > 0):                        # Trailing edge thickness limit, does not work if number of points is low
            self.monitor.insert(END,"   Trailing edge:     " + str(self.trail) + '\n')
        self.monitor.insert(END,    "   Kerf width:        " + str(self.kerfwidth) + '\n')

        # Start adding some G-Code file content
        self.Header(self.g_code_candidate)

        # Hand-over the rib data for serious kerf-path computation:
        self.KerfStitcher(self.rib_)



    def KerfStitcher(self, nodes):
        """ Examines given polygon-nodes list, 
            finds each line segment and computes 
            the corresponding offset copy           """

        aPPx = []
        aPPy = []
        aNNx = []
        aNNy = []
        NEWx = []
        NEWy = []
        NEWxrp = []
        NEWyrp = []


        for segment in range(len(nodes)):
            
            if segment < len(nodes)-1:
                ppx, ppy, nnx, nny = self.KerfOffsetter(nodes[segment], nodes[segment+1], self.half_kerf)          
            else:
                # Bite my tail! We have gone full circle.
                ppx, ppy, nnx, nny = self.KerfOffsetter(nodes[segment], nodes[0], self.half_kerf)    
                
            # Arrange the input polyline coords for proper computation
            aPPx.append(ppx)    ## aPPx and aPPy is never used anywhere!
            aPPy.append(ppy)    ## Thus they are superfluous ... (Unless we desire a Matplot view or something)
            
            # Arrange all offset segments coordinates similarly
            aNNx.append(nnx)
            aNNy.append(nny)


        # Extends all offset segments to their pair-wise intersection points,\ 
        # effectively fusing the desired offset polygonal path:
        for i in range(len(nodes)-1):
            
            try:
                new_x, new_y = self.get_intersection(aNNx[i][0], aNNy[i][0], aNNx[i][1], aNNy[i][1],  aNNx[i+1][0], aNNy[i+1][0], aNNx[i+1][1], aNNy[i+1][1])

                NEWx.append(new_x)
                NEWy.append(new_y)
                
            except (TypeError, ZeroDivisionError):
                print("     -- You don't say!\n")
                pass

        # In order to close the path (more or less) we have to "manually" add reasonable\
        # (default) values to the offset polylines's first and last nodes, like so:
        NEWx.insert(0, aNNx[0][0])      # First
        NEWy.insert(0, aNNy[0][0])
        NEWx.append(   aNNx[-1][1])     # Last
        NEWy.append(   aNNy[-1][1])
        


        # Finally we save the newly constructed offset path's coordinates to a corrected list-of-lists:
        for x in NEWx:
            xr = round(x, 5)            # Round to five significant decimals.
            xrp = f'{xr:9.5f}'          # Pad decimals with trailing zeroes, and total of nine spaces.
            NEWxrp.append(xrp)
              
        for y in NEWy:
            yr = round(y, 5)
            yrp = f'{yr:9.5f}'
            NEWyrp.append(yrp)
           
        NEWzp = zip(NEWxrp, NEWyrp)     # Zipping up the corrected X and Y lists
        
        points = list()
        pt = 0

        for node in NEWzp:
            node = list(node) 
            if len(node):
                x = float(node[0])
                y = float(node[1])
                points.append( [0,0] )  # Adding new list-item to the points list, 
                points[pt][0] = x       # then immediately updating its values.
                points[pt][1] = y
                pt = pt + 1

        print("\n\n _________ Final points _____________\n")
        print(points)                            # Show the output list-of-lists in console (as string)
        
        # Time to plot!
        self.plot(points, self.g_code_candidate)  #,  self.sp) 
        
        


    def KerfOffsetter(self, node1, node2, hk):
    
        P1x, P1y = node1
        P2x, P2y = node2

        # Coordinate diffs:
        Dx = P2x - P1x
        Dy = P2y - P1y 

        L = np.sqrt(Dx*Dx + Dy*Dy)      # Hypothenuse length == segment length
        
        if L == 0:
            L = 0.00001                 # Cunningly void division by zero

        # Normalize to "Unit length"
        U = 1/L 
        
        U = U * hk                    

        # Find scaled normal to segment line
        OFFx = Dy * U
        OFFy = Dx * U * (-1)            # Note sign-inversion for offset vector's Y-component

        # Define the new line's endpoints
        N1x = P1x - OFFx
        N1y = P1y - OFFy

        N2x = P2x - OFFx
        N2y = P2y - OFFy

        # Original line-segment's coords, for possible Matplot-style plotting:
        PPx = [P1x, P2x]
        PPy = [P1y, P2y]

        # New line's coordinates for further processing (formatted as if for Matlab plotting):
        NNx = [N1x, N2x]
        NNy = [N1y, N2y]
        
        return(PPx, PPy, NNx, NNy)


    
    def get_intersection(self, A1x, A1y, A2x, A2y, B1x, B1y, B2x, B2y):
        
        d = (B2y - B1y) * (A2x - A1x) - (B2x - B1x) * (A2y - A1y)
        if d:
            uA = ((B2x - B1x) * (A1y - B1y) - (B2y - B1y) * (A1x - B1x)) / d
            uB = ((A2x - A1x) * (A1y - B1y) - (A2y - A1y) * (A1x - B1x)) / d
        else:
            """ Happens occasionally for unobvious (but perhaps non-random) reasons. Probably caused by
                rounding errors that result in non-overlapping endpoints at a microscopic level. 
                In fact, tentatively adding even a miniscule decimal value to one of the failing input node
                pair's coordinates often circumvents this computing bug.
                However, the cleanest solution is to just catch and ignore errors triggered here,
                and the actual output quality does not suffer noticeably. """
        
            print('\n     No intersection found')
            return

        x = A1x + uA * (A2x - A1x)
        y = A1y + uA * (A2y - A1y)
        
        return(x, y)

    


    def plot(self, afdata, gclist):
        """ afdata is the airfoil data
            gclist is the list itself    """

        if (self.unit):   
            gclist.append( "G20                               ; inch\n");   # imperial mode
            prec = '%0.4f'                                                  # thous/10 for inch mode
        else:   
            gclist.append( "G21                               ; mm\n")      # metric mode
            prec = '%0.3f'                                                  # 1/1000 mm for metric mode

        gclist.append(     "G17                               ; xy plane\n")
        gclist.append(     "G90                               ; abs dist mode\n")


        # Must create the format string before using it      
        if self.FwordVar.get() == 1: 
            fmt = "G01 X"+prec+" Y"+prec+" F%0.1f\n"
        else:
            fmt = "G01 X"+prec+" Y"+prec+"\n" 


        # Plotting afdata points, formatted as gcode, to gclist (self.g_code_candidate)
        start = 0
        end = len(afdata)
        step = 1

        gclist.append("(doing profile now)\n" )

        if self.FwordVar.get() == 1:
            for i in range(start, end, step):
                gclist.append(fmt % (afdata[i][0], afdata[i][1], self.feedrate)) 
        else:
            for i in range(start, end, step):
                gclist.append(fmt % (afdata[i][0], afdata[i][1])) 

        gclist.append("(Closing path at trailing edge)\n" )        
        gclist.append("M2                              ; END of program\n")  ## M2 : End of program
        ##gclist.append("%\n")                                                 ## %  : ditto

        status_bar_update("Gcode generated")





    def SaveModel(self):
        """ Save an ini file formatted like this:
        
            [moddle]
            foilfile = moddle.dat
            chord = 100
            trail = 1
            kerf = 0.8
            feedrate = 200
            inch = 0            """

        try:     # Save the *.ini in the nc folder
            self.NcFileDirectory = self.GetIniData(self.inifile,'Directories','NcFiles')
        except:
            tkinter.messagebox.showinfo('Missing INI Data', 'You must set the\n' \
                'NC File Directory\n' \
                'before saving a file.\n' \
                'Go to Edit/NC Directory\n' \
                'in the menu to set this option')
            return

        modelname = self.ModelNameVar.get()
        modelname = modelname.strip()
        if (modelname == ''):
            tkinter.messagebox.showinfo('Need a model name in order to save a model')
            return

        inifile = self.NcFileDirectory +'/'+ modelname + '.ini'

        config = configparser.ConfigParser()
        config.add_section(modelname)
        items = self.Profilelistbox.curselection()
        item  = self.Profilelistbox.get(items[0])
        config.set(modelname, 'foilfile', item)
        config.set(modelname, 'chord',    self.ChordVar.get())
        config.set(modelname, 'trail',    self.TrailingEdgeLimitVar.get())
        config.set(modelname, 'kerf',     self.KerfWidthVar.get())
        config.set(modelname, 'feedrate', self.FeedrateVar.get())
        unit = self.UnitVar.get()
        config.set(modelname, 'inch',     str(unit))

        # Writing our configuration file
        with open(inifile, 'w') as configfile:
            config.write(configfile)
        self.monitor.insert(END, '\nSaved model\n')
      
        # Each time a "model" is saved, we also check the autoload option tick box for updates
        if self.AutoVar.get() == 1:   
            self.WriteIniData(self.inifile, 'autoload', 'load_or_not', '1')
        else:
            self.WriteIniData(self.inifile, 'autoload', 'load_or_not', '0')
        
        # We write modelname to the ini file, regardless of startup autoload status
        self.WriteIniData(self.inifile,'autoload','model', modelname)
      
        status_bar_update("Model Settings Saved as " + modelname)


    def ReadModel(self, filename):
        config = configparser.ConfigParser()
        config.read(filename)

        # Get the model name from the filename
        modelname = os.path.splitext(os.path.basename(filename))[0]
        if (config.has_section(modelname)):
            self.ModelNameVar.set(modelname)
            item = config.get(modelname, 'foilfile')
            item = os.path.join(self.DatDir, item)
            last = len(self.profiles) - 1
            self.Profilelistbox.selection_clear(0, last)
            self.Profilelistbox.selection_set(self.profiles.index(item))
            self.TrailingEdgeLimitVar.set( config.get(modelname, 'trail'))
            self.KerfWidthVar.set(config.get(modelname,  'kerf'))
            self.FeedrateVar.set(          config.get(modelname, 'feedrate'))
            self.UnitVar.set(   config.getint(modelname, 'inch'))
            self.monitor.insert(END, '\n >> Loaded model ' + modelname + ". Alright!\n")
            self.monitor.insert(END, '\n*** This is RibCut version number: ' + str(version_number) + ' ***\n')
            self.modelname = modelname
            return 1
        else:
            return 0


    def LoadModel(self):
        try:
            self.NcFileDirectory = self.GetIniData(self.inifile,'Directories', 'NcFiles')
        except:
            tkinter.messagebox.showinfo('Missing INI Data', 'You must set the\n' \
                'NC File Directory\n' \
                'before saving a file.\n' \
                'Go to Edit/NC Directory\n' \
                'in the menu to set this option')
            return

        filename = askopenfilename(initialdir=self.NcFileDirectory,defaultextension='.ini',filetypes=[('INI','*.ini')])
        self.ReadModel(filename)


    def FToD(self,s): ## Float To Decimal (only used for formatting entry-box widgets inputs)
        """
        Returns a decimal with 4 place precision
        valid imputs are any fraction, whole number space fraction
        or decimal string. The input must be a string!
        """
        s = s.strip(' ')        # Remove any leading and trailing spaces
        if s == '':             # Make sure it does not crash on empty string
            s = '0'
        D = Decimal             # Saves on typing
        P = D('0.000001')       # Set the precision wanted
        if ' ' in s:            # If it is a whole number with a fraction
            w, f = s.split(' ',1)
            w = w.strip(' ')    # Make sure there are no extra spaces
            f = f.strip(' ')
            n, d = f.split('/',1)
            ret = D(D(n)/D(d)+D(w)).quantize(P)
            return float(ret)
        elif '/' in s:          # If it is just a fraction
            n, d = s.split('/',1)
            ret =  D(D(n)/D(d)).quantize(P)
            return float(ret)
        ret = D(s).quantize(P)  # If it is a decimal number already
        return float(ret)


    def GetIniData(self,FileName,SectionName,OptionName):
        """
        Returns the data in the file, section, option, if it exists,
        of an .ini type file created with ConfigParser.write()
        If the file is not found or a section or an option is not found
        returns an exception
        """
        self.cp = configparser.ConfigParser()
        try:
            self.cp.read(FileName)
            try:
                self.cp.has_section(SectionName)
                try:
                    IniData = self.cp.get(SectionName, OptionName)
                except configparser.NoOptionError:
                    raise Exception('NoOptionError')
            except configparser.NoSectionError:
                raise Exception('NoSectionError')
        except IOError:
            raise Exception('NoFileError')
        return IniData


    def WriteIniData(self, FileName, SectionName, OptionName, OptionData):
        """
        Pass the file name, section name, option name and option data. 
        When complete returns 'sucess'
        """
        self.cp = configparser.ConfigParser()
        self.cp.read(FileName)  # read existing stuff and add to it
        if not self.cp.has_section(SectionName):
            self.cp.add_section(SectionName)
        self.cp.set(SectionName, OptionName, OptionData)
        with open(FileName, 'w') as configfile:
           self.cp.write(configfile)


    def GetDirectory(self):
        self.DirName = askdirectory(initialdir='/home',title='Please select a directory')
        if len(self.DirName) > 0:
            return self.DirName


    def CopyClpBd(self):
        self.monitor.clipboard_clear()
        self.monitor.clipboard_append(self.monitor.get(0.0, END))


    def WriteToNcFile(self):
        try:
            self.NcFileDirectory = self.GetIniData(self.inifile,'Directories','NcFiles')
        except:
            tkinter.messagebox.showinfo('Missing INI', 'You must set the\n' \
                'G-code File Directory\n' \
                'before saving a file.\n' \
                'Go to Edit/G-code Directory\n' \
                'in the menu to set this option')

        tag1 = '_kerf'
        tag2 = '_none'
        
        if self.kerfwidth > 0:
            fname = os.path.join(self.NcFileDirectory, self.modelname + tag1 + self.ext)
        else:
            fname = os.path.join(self.NcFileDirectory, self.modelname + tag2 + self.ext)

        of = open(fname,'w')
        for line in self.g_code_candidate:
            of.write(line)
        of.close()
        self.monitor.insert(END, '\n   Cartesian written:\n ' + fname + '\n')
        status_bar_update("Gcode was saved to nc-file!")


    def NcFileDirectory(self):
        DirName = self.GetDirectory()
        if len(DirName) > 0:
            self.WriteIniData(self.inifile,'Directories', 'NcFiles', DirName)


    def DatFileDirectory(self):
        DirName = self.GetDirectory()
        if len(DirName) > 0:
            self.WriteIniData(self.inifile,'Directories', 'DatFiles', DirName)


    def Simple(self):
        tkinter.messagebox.showinfo('Feature', 'Sorry this Feature has\nnot been programmed yet.')


    def ClearTextBox(self):
        self.monitor.delete(1.0, END)


    def SelectAllText(self):
        self.monitor.tag_add(SEL, '1.0', END)


    def SelectCopy(self):
        self.SelectAllText()
        self.CopyClpBd()


    def HelpAbout(self):
        
        typeDV = font.Font(name = 'TkCaptionFont', exists = True)
        typeDV.config(family = 'DejaVue Sans', size = 10)

        tkinter.messagebox.showinfo('Help About', 'Original code by '
            'the Swarfer.\n\nrcKeith adaped to Python3\nand GRBL compatibilty.\n\nSimplified and reformatted as ' 
            'an application for generating\n2D rib-cutting gcode by\nMartin Bergman.\n\n'
            'Version %0.2f' % (version_number))

    
    def stripfile(self, thefile):
        """ 
        Takes an array read from a dat file and strip out all comments 
        so we only have the co-ord numbers on return  
        """
        done = 0
        while not(done):
            done = 1
            bits = 0
            for key in range(0, len(thefile)-1):
                line = thefile[key]
                bits = str.strip(line) 
                bits = str.split(bits) #(preg_split('/[ ]+|\t/',trim(self.line));
                for idx in range(0, len(bits)-1): # prevent losing lines like '0 0'
                    if (bits[idx] == '0'):
                      bits[idx] = '0.0'
                if (len(bits) == 3) and (re.search('[a-d]|[f-z]', line) == None ): # some files have 3 fields, remove first one, the line number
                    bits.remove( bits[0])
                if ( re.search('[a-d]|[f-z]|[A-D]|[F-Z]',line) != None ):
                    thefile.remove(line)
                    done = 0
                    break
                if ( line == ''):
                    thefile.remove(line)
                    done = 0
                    break
                thefile[key] = str.strip(line)
        return thefile


    
    def RibRipper(self): 
        """ 
        Reads self.profile and builds self.rib_ array of (un-kerfed) cordinates  """

        idx = 0
        self.rib_ = list()
        div = 0.0   # Initialising. (Can't divide by zero anyway!).\ 
                    # If first value (x) in the profile-file is not exactly 1.0 then \
                    # use that value so that all values can be scaled to 1.
      
        for line in self.profile:         
            bits = line.split() 
            if len(bits):

                # Scaling -- Some dat files are 0..1 and some are 0..100
                if div == 0.0:
                    div = float(bits[0])

                x = 1 - float(bits[0]) / div    # Inverting all x values: from '1->0->1' to '0->1->0'
                y =     float(bits[1]) / div
                self.rib_.append( [0,0] )       # Adding new list-item to the list, then updating its values next!
                self.rib_[idx][0] = x * self.chordlength    # Scaling to required chordlength
                self.rib_[idx][1] = y * self.chordlength
                idx = idx + 1



app = Application()
app.master.title('[RibCut %0.2f]' % (version_number))
## We mustn't set window-dimensions here (they are not static), only its offset on screen:
app.master.geometry('+100+400') 
app.master.iconphoto(False, PhotoImage(file='./img/ribcut-favicon-32x32.png'))


# Status Bar(could be part of Application object, but isn't...)
status_bar = Label(app.master, text="Ready   ", anchor=E,)
status_bar.pack(fill=X, side=BOTTOM, ipady=5)
typemono = Font(family='DejaVu Sans Mono', size=10,  slant='italic')

def status_bar_update(status_mgs): 
    
    status_bar.config(text = " > " + status_mgs + "      ", 
                    anchor      = W, 
                    foreground  = "Black", 
                    background  = "#F6F152", 
                    font        = typemono,
                    borderwidth = 1,
                    relief      = 'solid'  )
    return
    
    

app.mainloop()
