import pygame
from pygame.locals import *
from GUI import *
from PhotonFile import *
from FileDialog import *
from MessageDialog import *

#todo: import set of bitmaps in photon file as template
#todo:   check if import succeeds... make set of images of 2560x1440
#todo: if we cancel on filedialog the next time we open filedialog and click on listbox an error occurs
#todo: Exe/distribution made with
#           cmd.com - prompt, type...
#           pyinstaller --onefile --windowed PhotonViewer.py

########################################################################################################################
##  Setup screen and load Photon file
########################################################################################################################
screen=None
layerimg=None
settingswidth = 200 * 2  # 2 columns
settingsleft = int(1440 / 4)
windowwidth=int(1440 / 4) + settingswidth
windowheight=int(2560 / 4)
controls=[]
layerNr = 0
photonfile=None
menubar=None

def init_pygame_surface():
    global screen
    global layerimg
    global windowwidth
    global windowheight
    global settingsleft
    global settingswidth
    global controls
    global layerNr
    global menubar

    pygame.init()
    pygame.display.set_caption("Photon File Editor")
    # load and set the logo
    # logo = pygame.image.load("logo32x32.png")
    # pygame.display.set_icon(logo)
    pygame.font.init()

    # create a surface on screen width room for settings
    screen = pygame.display.set_mode((windowwidth, windowheight))
    scale = (0.25, 0.25)
    layerimg = pygame.Surface((int(1440 * scale[0]), int(2560 * scale[1])))
    layerimg.fill((0,0,255))

    # create menu
    def infoMessageBox(title,message):
        dialog = MessageDialog(screen, pos=(140, 140),
                               title=title,
                               message=message,
                               parentRedraw=redrawMainWindow)
        dialog.show()
    def errMessageBox(errormessage):
        dialog = MessageDialog(screen, pos=(140, 140),
                               title="Error",
                               message=errormessage,
                               parentRedraw=redrawMainWindow)
        dialog.show()

    def doNothing():
        return
    def saveFile():
        saveHeaderAndCommon2PhotonFile()
        saveLayer2PhotonFile()
        dialog = FileDialog(screen, (40, 40), ext=".photon",title="Save Photon File", defFilename="newfile.photon", parentRedraw=redrawMainWindow)
        filename=dialog.newFile()
        if not filename==None:
            print ("Returned: ",filename)
            try:
                photonfile.writeFile(filename)
            except Exception as err:
                errMessageBox(str(err))
        else:
            print("User Canceled")
        return

    def loadFile():
        dialog = FileDialog(screen, (40, 40), ext=".photon",title="Load Photon File", parentRedraw=redrawMainWindow)
        filename=dialog.getFile()
        if not filename==None:
            print ("Returned: ",filename)
            try:
                openPhotonFile(filename)
            except Exception as err:
                errMessageBox(str(err))
        else:
            print ("User Canceled")
        return

    def replaceBitmaps():
        global photonfile
        if photonfile==None:
            print ("No template loaded!!")
            infoMessageBox("No photon file loaded!","A photonfile is needed as template to load the bitmaps in.")
            return
        dialog = FileDialog(screen, (40, 40), ext=".png", title="Select directory with png files", parentRedraw=redrawMainWindow)
        directory = dialog.getDirectory()
        if not directory == None:
            print("Returned: ", directory)
            try:
                photonfile.replaceBitmaps(directory)
            except Exception as err:
                errMessageBox(str(err))
        else:
            print("User Canceled")
        return

    def about():
        dialog = MessageDialog(screen, pos=(140, 140),
                               title="About PhotonEditor",
                               message="Version Alpha \n Author: Nard Janssens \n License: Free for non-commerical use.",
                               parentRedraw=redrawMainWindow)
        dialog.show()

    menubar=MenuBar(screen)
    menubar.addMenu("File","F")
    menubar.addItem("File","Load",loadFile)
    menubar.addItem("File","Save",saveFile)
    menubar.addMenu("Edit", "E")
    menubar.addItem("Edit","Replace Bitmaps",replaceBitmaps)
    menubar.addMenu("View", "V")
    menubar.addItem("View", "3D",doNothing)
    menubar.addMenu("Help", "H")
    menubar.addItem("Help", "About",about)
    viewport_yoffset=menubar.height+8

    # Add Up/Down Layer Buttons
    layerNr = 0
    def layerDown():
        global layerNr, layerimg, photonfile
        if photonfile == None: return
        saveLayer2PhotonFile()

        layerNr = layerNr - 1
        if layerNr < 0: layerNr = 0
        layerimg= photonfile.getBitmap(layerNr)
        refreshLayerControls()
        return

    def layerUp():
        global layerNr, layerimg, photonfile
        if photonfile == None: return
        saveLayer2PhotonFile()

        maxLayer = PhotonFile.convBytes(photonfile.Header["nLayers"], photonfile.tpInt)
        layerNr = layerNr + 1
        if layerNr == maxLayer: layerNr = maxLayer - 1
        layerimg = photonfile.getBitmap(layerNr)
        refreshLayerControls()
        return

    controls.append(ImgBox(screen, filename="resources/arrow-up.png", filename_hover="resources/arrow-up-hover.png", pos=(20,20+viewport_yoffset), borderhovercolor=(0,0,0),func_on_click=layerUp))
    controls.append(ImgBox(screen, filename="resources/arrow-down.png", filename_hover="resources/arrow-down-hover.png", pos=(20,80+viewport_yoffset), borderhovercolor=(0,0,0),func_on_click=layerDown))

    transTypes={PhotonFile.tpByte: TextBox.HEX,PhotonFile.tpInt: TextBox.INT,PhotonFile.tpFloat: TextBox.FLOAT,PhotonFile.tpChar: TextBox.HEX}
    # Add Header data fields
    row=0
    controls.append(TextBox(screen, text="HEADER", rect=GRect(settingsleft+10,10+row*24+viewport_yoffset,180,16),editable=False,drawBorder=False,backcolor=(128,128,128)))
    for row, (bTitle, bNr, bType, bEditable) in enumerate(PhotonFile.pfStruct_Header,1):#enum start at 1
        controls.append(TextBox(screen, text=bTitle, rect=GRect(settingsleft+10,10+row*24+viewport_yoffset,120,16),editable=False,drawBorder=False))
    for row,  (bTitle, bNr, bType,bEditable) in enumerate(PhotonFile.pfStruct_Header,1):#enum start at 1
        tbType = transTypes[bType]
        bcolor=(255,255,255) if bEditable else (128,128,128)
        controls.append(TextBox(screen, text="", \
                                rect=GRect(settingsleft+130, 10 + row * 24+viewport_yoffset, 60, 16),\
                                editable=bEditable, \
                                backcolor=bcolor, \
                                textcolor=(0,0,0),\
                                inputType=tbType, \
                                onEnter=updateTextBox2PhotonFile, \
                                linkedData={"VarGroup":"Header","Title":bTitle,"NrBytes":bNr,"Type":bType} \
                                ))

    # Add Common data fields
    row=0
    settingsleft = settingsleft+200
    controls.append(TextBox(screen, text="COMMON", rect=GRect(settingsleft+10,10+row*24+viewport_yoffset,180,16),editable=False,drawBorder=False,backcolor=(128,128,128)))
    for row, (bTitle, bNr, bType,bEditable) in enumerate(PhotonFile.pfStruct_Common,1):
        controls.append(TextBox(screen, text=bTitle, rect=GRect(settingsleft+10,10+row*24+viewport_yoffset,120,16),editable=False,drawBorder=False))
    for row, (bTitle, bNr, bType,bEditable) in enumerate(PhotonFile.pfStruct_Common,1):
        tbType = transTypes[bType]
        bcolor = (255, 255, 255) if bEditable else (128, 128, 128)
        controls.append(TextBox(screen, text="", \
                                rect=GRect(settingsleft+130, 10 + row * 24+viewport_yoffset, 60, 16),\
                                editable=bEditable, \
                                backcolor=bcolor, \
                                textcolor=(0, 0, 0), \
                                inputType=tbType, \
                                onEnter=updateTextBox2PhotonFile, \
                                linkedData={"VarGroup": "Common", "Title": bTitle, "NrBytes": bNr, "Type": bType} \
                                ))

    # Add Current Layer meta fields
    row=14
    controls.append(TextBox(screen, text="LAYER", rect=GRect(settingsleft+10,10+row*24+viewport_yoffset,120,16),editable=False,drawBorder=False,backcolor=(128,128,128)))
    for row, (bTitle, bNr, bType,bEditable) in enumerate(PhotonFile.pfStruct_LayerDef,15):
        controls.append(TextBox(screen, text=bTitle, rect=GRect(settingsleft+10,10+row*24+viewport_yoffset,120,16),editable=False,drawBorder=False))
    row=14
    controls.append(TextBox(screen, text=str(layerNr), rect=GRect(settingsleft + 130, 10 + row * 24+viewport_yoffset, 60, 16),editable=False, drawBorder=False,backcolor=(128,128,128)))
    for row, (bTitle, bNr, bType,bEditable) in enumerate(PhotonFile.pfStruct_LayerDef, 15):
        tbType = transTypes[bType]
        bcolor = (255, 255, 255) if bEditable else (128, 128, 128)
        controls.append(TextBox(screen, text="", \
                                rect=GRect(settingsleft + 130, 10 + row * 24+viewport_yoffset, 60, 16),\
                                editable=bEditable, \
                                backcolor=bcolor, \
                                textcolor=(0, 0, 0), \
                                inputType=tbType,\
                                onEnter=updateTextBox2PhotonFile, \
                                linkedData={"VarGroup": "LayerDef", "Title": bTitle, "NrBytes": bNr, "Type": bType} \
                                ))

def updateTextBox2PhotonFile(textbox, val,linkedData):
    global photonfile
    #print ("updateTextBox2PhotonFile")
    #print ("data: ",val, linkedData)
    for control in controls:
        if control==textbox:
            pVarGroup=linkedData["VarGroup"]
            pTitle= linkedData["Title"]
            pBNr = linkedData["NrBytes"]
            pType = linkedData["Type"]
            pLayerNr = None
            if "LayerNr" in linkedData:linkedData["LayerNr"]
            bytes=None
            #do some check if val is of correct type and length
            if pType == PhotonFile.tpChar:bytes=PhotonFile.hex_to_bytes(val)
            if pType == PhotonFile.tpByte:bytes = PhotonFile.hex_to_bytes(val)
            if pType == PhotonFile.tpInt: bytes = PhotonFile.int_to_bytes(int(val))
            if pType == PhotonFile.tpFloat: bytes = PhotonFile.float_to_bytes(float(val))
            if not len(bytes)==pBNr:
                print ("Error: Data size not expected in PhotonViewer.updateTextBox2PhotonFile!")
                return
            if pVarGroup=="Header":photonfile.Header[pTitle]=bytes
            if pVarGroup=="Common":photonfile.Common[pTitle]=bytes
            if pVarGroup=="LayerDef": photonfile.LayerDefs[layerNr][pTitle] = bytes
            #print ("Found. New Val: ",val,linkedData)

    return

def saveHeaderAndCommon2PhotonFile():
    #print ("saveHeaderAndCommon2PhotonFile")
    global photonfile
    if photonfile==None:return
    # Header data fields
    for row, (bTitle, bNr, bType,bEditable) in enumerate(PhotonFile.pfStruct_Header,22):#enum start at 22
        if bEditable:
            textBox=controls[row]
            updateTextBox2PhotonFile(textBox,textBox.text,{"VarGroup": "Header", "Title": bTitle, "NrBytes": bNr, "Type": bType})
    # Common data fields
    for row, (bTitle, bNr, bType,bEditable) in enumerate(PhotonFile.pfStruct_Common,54):
        if bEditable:
            textBox=controls[row]
            updateTextBox2PhotonFile(textBox,textBox.text,{"VarGroup": "Common", "Title": bTitle, "NrBytes": bNr, "Type": bType})

def saveLayer2PhotonFile():
    #print ("saveLayer2PhotonFile")
    global photonfile
    global layerNr
    if photonfile == None: return
    # Current Layer meta fields
    for row, (bTitle, bNr, bType, bEditable) in enumerate(PhotonFile.pfStruct_LayerDef, 74):
        if bEditable:
            textBox=controls[row]
    #        print (row,bTitle,textBox.text)
            updateTextBox2PhotonFile(textBox,textBox.text,{"VarGroup": "LayerDef", "Title": bTitle, "NrBytes": bNr, "Type": bType})

def refreshHeaderAndCommonControls():
    global photonfile
    if photonfile==None:return
    # Header data fields
    for row, (bTitle, bNr, bType,bEditable) in enumerate(PhotonFile.pfStruct_Header,22):#enum start at 22
        nr=PhotonFile.convBytes(photonfile.Header[bTitle],bType)
        if bType==PhotonFile.tpFloat:nr=round(nr,4) #round floats to 4 decimals
        controls[row].setText(str(nr))

    # Common data fields
    for row, (bTitle, bNr, bType,bEditable) in enumerate(PhotonFile.pfStruct_Common,54):
        nr=PhotonFile.convBytes(photonfile.Common[bTitle],bType)
        if bType == PhotonFile.tpFloat: nr = round(nr, 4) #round floats to 4 decimals
        controls[row].setText(str(nr))

def refreshLayerControls():
    global photonfile
    global layerNr
    if photonfile==None:return
    # Current Layer meta fields
    row=73
    controls[row].setText(str(layerNr))
    #print (layerNr)
    for row, (bTitle, bNr, bType,bEditable) in enumerate(PhotonFile.pfStruct_LayerDef,74):
        nr=PhotonFile.convBytes(photonfile.LayerDefs[layerNr][bTitle],bType)
        if bType == PhotonFile.tpFloat: nr = round(nr, 4) #round floats to 4 decimals
        controls[row].setText(str(nr))


def openPhotonFile(filename):
    global photonfile, layerimg
    # read file
    photonfile = PhotonFile(filename)
    photonfile.readFile()
    layerimg=photonfile.getBitmap(0)
    refreshHeaderAndCommonControls()
    refreshLayerControls()


# initialize the pygame module
init_pygame_surface()

########################################################################################################################
##  Drawing/Event-Polling Loop
########################################################################################################################

# define a variable to control the main loop
running = True

def redrawMainWindow():
    screen.fill((0,0,0))
    if not photonfile==None:
        if not photonfile.isDrawing:
            screen.blit(layerimg, (0, 0))
    else:#also if we have no photonfile we need to draw to cover up menu/filedialog etc
        screen.blit(layerimg, (0, 0))

    for ctrl in controls:
        ctrl.redraw()

    menubar.redraw()


# main loop
while running:
    # redraw photonfile

    redrawMainWindow()
    pygame.display.flip()
    pygame.time.Clock().tick(60)

    # event handling, gets all event from the eventqueue
    for event in pygame.event.get():
        pos = pygame.mouse.get_pos()
        # only do something if the event is of type QUIT
        if event.type == pygame.QUIT:
            # change the value to False, to exit the main loop
            running = False
        if event.type == pygame.MOUSEBUTTONUP:
            menubar.handleMouseUp(pos,event.button)
            for ctrl in controls:
                ctrl.handleMouseUp(pos,event.button)

        if event.type == pygame.MOUSEBUTTONDOWN:
            menubar.handleMouseDown(pos,event.button)
            for ctrl in controls:
                ctrl.handleMouseDown(pos,event.button)

            #print (event.button)


        if event.type == pygame.MOUSEMOTION:
            menubar.handleMouseMove(pos)
            for ctrl in controls:
                ctrl.handleMouseMove(pos)

        if event.type == pygame.KEYDOWN :

            if event.key == pygame.K_ESCAPE :
              print ("Escape key pressed down.")
              running = False
            else:
                for ctrl in controls:
                    ctrl.handleKeyDown(event.key,event.unicode)

        #elif event.type == pygame.KEYUP :

pygame.quit()

