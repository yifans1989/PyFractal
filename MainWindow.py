import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade
import time
import threading
import gobject
from SyntaxFractal import SyntaxFractal
#from BlankFractal import BlankFractal
from IFSFractal import IFSFractal
from JuliaSet import JuliaSet
from Mandelbrot import Mandelbrot

class MainWindow:
    drawing_thread = None
    refreshing_thread = None
    wTree = None
    drawArea = None
    offImage = None
    selectorCombo = None
    fractal = None
    fractalList = None
    drawButton = None
    draging = False
    dragingStartP = (0, 0)
    dragingEndP = (0, 0)
    
    def registerFractals(self):
        self.fractalList = []
        self.fractalList.append(SyntaxFractal())
        #self.fractalList.append(BlankFractal())
        self.fractalList.append(IFSFractal())
        self.fractalList.append(JuliaSet())
        self.fractalList.append(Mandelbrot())
        return
    
    
    def showWindow(self):
        # show main window
        self.gladefile = "glade/MainWindow.glade"
        self.wTree = gtk.glade.XML(self.gladefile)
        callbackDic = { "on_mainWindow_destroy" : lambda x: gtk.main_quit(),
                        "on_drawButton_clicked" : self.on_drawButton_clicked,
                        "on_drawingArea_expose_event" : self.on_drawingArea_expose_event, 
                        "on_selectorCombo_changed" : self.on_selectorCombo_changed,
                        "on_drawingArea_button_press_event": self.on_drawingArea_button_press_event,
                        "on_drawingArea_button_release_event": self.on_drawingArea_button_release_event,
                        "on_drawingArea_motion_notify_event": self.on_drawingArea_motion_notify_event
                         }
        self.wTree.signal_autoconnect(callbackDic)
        self.wTree.get_widget('mainWindow').show()
        
        # save button widget
        self.drawButton = self.wTree.get_widget('drawButton')
        
        # make off-screen image
        self.drawArea = self.wTree.get_widget('drawingArea')
        self.offImage = gtk.gdk.Pixmap(self.drawArea.window, 600, 600, -1)
        colorMap = gtk.gdk.colormap_get_system()
        color = colorMap.alloc_color("white")
        gc = self.offImage.new_gc(color)
        self.offImage.draw_rectangle(gc, True, 0, 0, 600, 600)
        
        # make the combo box
        self.selectorCombo = self.wTree.get_widget('selectorCombo')
        #self.selectorCombo.append_text('Select a template')
        for i in range(0, len(self.fractalList)):
            self.selectorCombo.append_text(self.fractalList[i].getName())
         
        # set control panel
        self.controlPanelContainer = self.wTree.get_widget('controlPanelContainer')
        return
    
    def __init__(self):
        self.registerFractals()
        self.showWindow()
        return
    
    def on_selectorCombo_changed(self, widget):
        if (self.drawing_thread != None) and (self.drawing_thread.isAlive() == True):
            return
        index = widget.get_active()
        if (index == 0) or (index > len(self.fractalList)):
            return
        fractal = self.fractalList[index - 1]
        self.fractal = fractal
        
        existingComponents = self.controlPanelContainer.get_children()
        if len(existingComponents) != 0:
            self.controlPanelContainer.remove(existingComponents[0])
        self.controlPanelContainer.pack_start(self.fractal.getControlPanel(), False, False, 0)
        return
        
    def on_drawButton_clicked(self, widget):
        if self.fractal == None:
            return

        if (self.drawing_thread != None) and (self.drawing_thread.isAlive() == True):
            widget.set_label("Draw")
            self.fractal.stopDrawing()
            return

        self.drawing_thread = threading.Thread(target=self.fractal.drawing)

        colorMap = gtk.gdk.colormap_get_system()
        color = colorMap.alloc_color("white")
        gc = self.offImage.new_gc(color)
        self.offImage.draw_rectangle(gc, True, 0, 0, 600, 600)
        
        print "on_drawButton_clicked"
        self.refreshing_thread = threading.Thread(target=self.refreshing)
        self.drawing_thread.start()
        self.refreshing_thread.start()
        widget.set_label("Stop")

        #self.drawing_thread.join()
        #self.refreshing_thread.join()
        return

    def refreshing(self):
        gc = self.offImage.new_gc()
        while (True):
            time.sleep(0.05)
            self.drawArea.window.draw_drawable(gc, self.fractal.getDrawable(), 0, 0, 0, 0, 600, 600)
            if self.drawing_thread.isAlive() == False:
                self.drawButton.set_label("Draw")
                break
        return
    
    def on_drawingArea_expose_event(self, area, event):
        if (self.fractal != None) and (self.drawing_thread != None) and (self.drawing_thread.isAlive() == False):
            gc = self.offImage.new_gc()
            self.drawArea.window.draw_drawable(gc, self.fractal.getDrawable(), 0, 0, 0, 0, 600, 600)
        return
    
    def on_drawingArea_button_press_event(self, widget, event):
        print "button ", event.button, " pressed"
        self.draging = True
        self.dragingStartP = (event.x, event.y)
        return True
    
    def on_drawingArea_button_release_event(self, widget, event):
        print "button ", event.button, " released"
        self.draging = False
        self.dragingEndP = (event.x, event.y)
        
        if ((self.drawing_thread != None) and (self.drawing_thread.isAlive() == True)) or (self.fractal == None):
            return
        
        needToRedraw = False    
        if event.button == 1:
            # zoom in
            # determine draging area
            # note, this area will be mapped into standard coordinates, p0(x0, y0) is the left-bottom,
            # so the logic of y and x is different
            if self.dragingStartP[0] < self.dragingEndP[0]:
                x0 = self.dragingStartP[0]
                x1 = self.dragingEndP[0]
            else:
                x1 = self.dragingStartP[0]
                x0 = self.dragingEndP[0]
            if self.dragingStartP[1] > self.dragingEndP[1]:
                y0 = self.dragingStartP[1]
                y1 = self.dragingEndP[1]
            else:
                y1 = self.dragingStartP[1]
                y0 = self.dragingEndP[1]
            if x0 != x1 and y0 != y1:
                print "call fractal zoomIn"
                print x0, " ", y0, " ", x1, " ", y1
                needToRedraw = self.fractal.zoomIn(x0, y0, x1, y1)
        elif event.button == 3:
            # zoom out
            needToRedraw = self.fractal.zoomOut()
        if needToRedraw == True:
            # will start new thread and redraw
            print "will re-draw"
            self.on_drawButton_clicked(self.drawButton)
        return
    
    def on_drawingArea_motion_notify_event(self, widget, event):
        #print "pointer at ", event.x, ", ", event.y
        return
    
if __name__ == '__main__':
    c = MainWindow()
    gobject.threads_init()
    gtk.main()
    pass