import numpy as np
import time
import pyqtgraph as pg
import dicom as di
import pydicom_series as diSeries
from pyqtgraph.Qt import QtCore, QtGui

def dataSlicing(dataPath, masks=None):
    #Gui init
    startTime = time.time()
    global app, win, imv1, imv2, imv3, hLine1, hLine2, hLine3, vLine1, vLine2, vLine3
    app = QtGui.QApplication([])
    win = QtGui.QMainWindow()
    win.setWindowTitle('DataSlicing')
    win.resize(600,800)
    cw = QtGui.QWidget()
    win.setCentralWidget(cw)
    l = QtGui.QGridLayout()
    cw.setLayout(l)
    imv1 = pg.ImageView()
    imv2 = pg.ImageView()
    imv3 = pg.ImageView()
    l.addWidget(imv1, 0, 0)
    l.addWidget(imv2, 1, 0)
    l.addWidget(imv3, 2, 0)
    win.show()  

    #Get 3D data
    vol = diSeries.read_files(dataPath)
    data = vol[0].get_pixel_array()

    img1RGBA = np.zeros((data.shape[0],data.shape[1],4),dtype=np.ubyte)
    img2RGBA = np.zeros((data.shape[0],data.shape[2],4),dtype=np.ubyte)
    img3RGBA = np.zeros((data.shape[1],data.shape[2],4),dtype=np.ubyte)
    
    #input mask is a np array with numbered regions, 0 specifies no colour
    if masks is not None:                
        alpha = int(255/float(len(masks)))        
        #every mask in the list gets its own lookup table to avoid problems
        #with reset numbering of regions in different masks and 
        # different number of regions in each of the masks
        masksCol = []
        for j in range(len(masks)):
            if data.shape != masks[j].shape:
                raise Exception('The dimensions of the mask%d and data do not match.',j)
            #command np.unique(someArray) returns list of unique values in array
            colCount = len(np.unique(masks[j]))
            lookupTable = np.zeros((colCount,4),dtype=np.ubyte)
            lookupTable[0] = [0,0,0,0]

            for i in range(1,colCount):
                lookupTable[i]=np.random.randint(1,256,size=3).tolist()+[alpha]
                
            masksCol.append(pg.applyLookupTable(masks[j],lookupTable))

        maskBack = masksCol.pop(0)
        mask = np.zeros(maskBack.shape,dtype=np.ubyte)
        for m in masksCol:
            
            mask[:,:,:,3]=((m[:,:,:,3].astype(float)/255)+(maskBack[:,:,:,3].astype(float)/255)*(1-(m[:,:,:,3].astype(float)/255)))*255
            #when the alpha is zero, RGBs should be zero too
            #dividing by large number in float will produce int zero values
            mask[mask==0]=1000
            mask[:,:,:,0]=(m[:,:,:,0]*(m[:,:,:,3].astype(float)/255)+maskBack[:,:,:,0]*(maskBack[:,:,:,3].astype(float)/255)*(1-(m[:,:,:,3].astype(float)/255)))/(mask[:,:,:,3].astype(float)/255)
            mask[:,:,:,1]=(m[:,:,:,1]*(m[:,:,:,3].astype(float)/255)+maskBack[:,:,:,1]*(maskBack[:,:,:,3].astype(float)/255)*(1-(m[:,:,:,3].astype(float)/255)))/(mask[:,:,:,3].astype(float)/255)
            mask[:,:,:,2]=(m[:,:,:,2]*(m[:,:,:,3].astype(float)/255)+maskBack[:,:,:,2]*(maskBack[:,:,:,3].astype(float)/255)*(1-(m[:,:,:,3].astype(float)/255)))/(mask[:,:,:,3].astype(float)/255)
            maskBack = mask
        
        maskBack[maskBack==0]=255
        maskCol = maskBack
    else:
        maskCol = None

    #creates crosshairs, positioned in the middle of the picture, limited by
    #dimensions of the picture
    hLine1 = pg.InfiniteLine(angle=0, movable=True, pos=img1RGBA.shape[1]/2, bounds=[0,img1RGBA.shape[1]-1])
    vLine1 = pg.InfiniteLine(angle=90, movable=True, pos=img1RGBA.shape[0]/2, bounds=[0,img1RGBA.shape[0]-1])

    hLine2 = pg.InfiniteLine(angle=0, movable=True, pos=img2RGBA.shape[1]/2, bounds=[0,img2RGBA.shape[1]-1])
    vLine2 = pg.InfiniteLine(angle=90, movable=True, pos=img2RGBA.shape[0]/2, bounds=[0,img2RGBA.shape[0]-1])

    hLine3 = pg.InfiniteLine(angle=0, movable=True, pos=img3RGBA.shape[1]/2, bounds=[0,img3RGBA.shape[1]-1])
    vLine3 = pg.InfiniteLine(angle=90, movable=True, pos=img3RGBA.shape[0]/2, bounds=[0,img3RGBA.shape[0]-1])

    imv1.addItem(vLine1)
    imv1.addItem(hLine1)
    imv2.addItem(vLine2)
    imv2.addItem(hLine2)
    imv3.addItem(vLine3)
    imv3.addItem(hLine3)
    
    #{v,h}Line{1,2,3}.value() gives only one value, since the angle of lines is
    #zero or right
    #left upper corner of the picture is [0,0] coordinate
    
    def updateV1(): 
    #updates image views that get affected by dragging in imv1 in vertical dimension
        global imv3, img3, img3RGBA, vLine1, vLine2
        vLine2.setValue(vLine1.value()) 
        img3 = data[vLine1.value(),:,:]
        img3RGBA = pg.makeRGBA(img3,levels=[np.amin(img3),np.amax(img3)])[0]
        if maskCol is not None:
            maskSlice = maskCol[vLine1.value(),:,:,:]
            img3RGBA[:,:,0:3] = maskSlice[:,:,0:3].astype(float)/255*img3RGBA[:,:,0:3]
            img3RGBA[:,:,3] = 255

        imv3.setImage(img3RGBA.astype(int))

    def updateH1():
    #updates image views that get affected by dragging in imv1 in horizontal
    #dimension
        global img2, img2RGBA, imv2, hLine1, vLine3
        vLine3.setValue(hLine1.value())
        img2 = data[:,hLine1.value(),:]
        img2RGBA = pg.makeRGBA(img2,levels=[np.amin(img2),np.amax(img2)])[0]
        if maskCol is not None:
            maskSlice = maskCol[:,hLine1.value(),:,:]
            img2RGBA[:,:,0:3] = maskSlice[:,:,0:3].astype(float)/255*img2RGBA[:,:,0:3]
            img2RGBA[:,:,3] = 255

        imv2.setImage(img2RGBA.astype(int))

    vLine1.sigDragged.connect(updateV1)
    hLine1.sigDragged.connect(updateH1)
        
    def updateV2():
        global imv3, img3, img3RGBA, vLine2, vLine1
        vLine1.setValue(vLine2.value())
        img3 = data[vLine2.value(),:,:]
        img3RGBA = pg.makeRGBA(img3,levels=[np.amin(img3),np.amax(img3)])[0]
        if maskCol is not None:
            maskSlice = maskCol[vLine2.value(),:,:,:]
            img3RGBA[:,:,0:3] = maskSlice[:,:,0:3].astype(float)/255*img3RGBA[:,:,0:3]
            img3RGBA[:,:,3] = 255;

        imv3.setImage(img3RGBA.astype(int))

    def updateH2():
        global imv1, img1, img1RGBA, hLine2, hLine3
        hLine3.setValue(hLine2.value())
        img1 = data[:,:,hLine2.value()]
        img1RGBA = pg.makeRGBA(img1,levels=[np.amin(img1),np.amax(img1)])[0]
        if maskCol is not None:
            maskSlice = maskCol[:,:,hLine2.value(),:]
            img1RGBA[:,:,0:3] = maskSlice[:,:,0:3].astype(float)/255*img1RGBA[:,:,0:3]
            img1RGBA[:,:,3] = 255

        imv1.setImage(img1RGBA.astype(int))

    vLine2.sigDragged.connect(updateV2)
    hLine2.sigDragged.connect(updateH2)

    def updateV3():
        global imv2, img2, img2RGBA, vLine3, hLine1
        hLine1.setValue(vLine3.value())
        img2 = data[:,vLine3.value(),:]
        img2RGBA = pg.makeRGBA(img2,levels=[np.amin(img2),np.amax(img2)])[0]
        if maskCol is not None:
            maskSlice = maskCol[:,vLine3.value(),:,:]
            img2RGBA[:,:,0:3] = maskSlice[:,:,0:3].astype(float)/255*img2RGBA[:,:,0:3]
            img2RGBA[:,:,3] = 255

        imv2.setImage(img2RGBA.astype(int))

    def updateH3():
        global imv1, img1, img1RGBA, hLine3, hLine2
        hLine2.setValue(hLine3.value())
        img1 = data[:,:,hLine3.value()]
        img1RGBA = pg.makeRGBA(img1,levels=[np.amin(img1),np.amax(img1)])[0]
        if maskCol is not None:
            maskSlice = maskCol[:,:,hLine3.value(),:]
            img1RGBA[:,:,0:3] = maskSlice[:,:,0:3].astype(float)/255*img1RGBA[:,:,0:3]
            img1RGBA[:,:,3]

        imv1.setImage(img1RGBA.astype(int))

    vLine3.sigDragged.connect(updateV3)
    hLine3.sigDragged.connect(updateH3)
    
    #sets initial images, when script starts
    updateV1()
    updateH1()
    updateH2()
    endTime = time.time()
    elapsed = endTime - startTime
    print "time elapsed: ", elapsed

## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    import numpy as np
    if (len(sys.argv)<2 or len(sys.argv)>3):
        print """Please use script as follows: dataSlicingMasks arg1 arg2
    arg1: path to folder containing dicom images
    arg2: path to npz archive containing masks"""

    elif (len(sys.argv)==2):        
        dataSlicing(sys.argv[1])
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()
    else:
        npzData = np.load(sys.argv[2])
        masks = []
        for i in nzpData.files:
            masks.append(nzpData[i])
        dataSlicing(sys.argv[1],masks)
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()
#    mask1 = np.zeros((160,512,512),dtype=np.ubyte)
#    mask2 = np.zeros((160,512,512),dtype=np.ubyte)
#    mask3 = np.zeros((160,512,512),dtype=np.ubyte)
#    mask2[20:120,:,:]=1
#    mask3[:,200:300,:]=1
#    mask1[50:70,:,:]=1
#    masks=[mask1,mask2,mask3]

