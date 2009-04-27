from PyQt4.QtCore import *
from PyQt4.QtGui import *

from Vispa.Main.VispaWidget import *
from Vispa.Main.PortConnection import *

class PortWidget(VispaWidget):
    """ This widget is used to dispay sink and source port of ConnectableWidget.
    """
    # Overridden attibutes
    WIDTH = 6
    HEIGHT = WIDTH
    BACKGROUND_SHAPE = 'RECT'
    TITLEFIELD_FONTSIZE = 10
    
    # New attributes
    PORT_TYPE = ''
    CONNECTIONPOINT_X = 3
    CONNECTIONPOINT_Y = 3
    CONNECTION_DIRECTION = PointToPointConnection.ConnectionDirection.UNDEFINED    # Default
    DRAG_PORT_TEXT = 'connect port'         # Text shown while dragging. The drop event is verified by this string, so should not be empty.
    
    def __init__(self, parent=None, name='default'):
        """ Constructor.
        """
        VispaWidget.__init__(self, parent)
        self.setName(name)
        self._connectionDirection = self.CONNECTION_DIRECTION
        self._startDragPosition = None
        self.setDragable(True)
        self._aimConnection = None
        
    def setDragable(self,dragable):
        """ Set whether user can grab the port and connect it to others.
        """
        VispaWidget.setDragable(self,False)
        self._dragablePort=dragable
        self.setAcceptDrops(dragable)
    
    def isDragable(self):
        return self._dragablePort
    
    def setName(self, name):
        """ Sets name of port.
        
        Name will be shown as tooltip unless a descriptions is set.
        See setDescription().
        """
        #self._initTitleField()
        #self.titleField().setAutoscale(True, False)
        self.setTitle(name)
        self.setToolTip(name)
        
    def name(self):
        """ Returns name of this port.
        """
        if self.titleIsSet():
            return self.title()
        return ''
    
    def setDescription(self, description):
        """ Sets description text of this port.
        
        Description will be shown as tooltip.
        """
        self.setText(description)
    
    def description(self):
        """ Returns description text.
        """
        if self.textFieldIsSet():
            return self.textField.getText()
        return ''
    
    def portType(self):
        """ Return type of this port.
        
        The value has to be set by inheriting classes.
        """
        return self.PORT_TYPE

    def connectionPoint(self):
        """ Returns point within this port from which attached connections should start.
        """
        return self.parent().mapToParent(self.pos() + QPoint(self.CONNECTIONPOINT_X, self.CONNECTIONPOINT_Y) * self.scale())
    
    def connectionDirection(self):
        """ Returns the direction in which an attached connection should start.
        """
        return self._connectionDirection
    
    def moduleParent(self):
        """ Returns parent of this port's parent.
        
        As the port should belong to a ConnectableWidget the function returns the QWidget in which the ConnectableWidget lives.
        """ 
        # Port belongs to module
        # Think of better solution. Port shall not create PortConnection.
        if self.parent():
            return self.parent().parent()
        else:
            return None
    
    def drawTitle(self, painter):
        """ Overwrite VispaWidget.drawTitle()
        
        Do not show title, instead ConnectableWidget will show title/name.
        """
        pass
    
    def drawTextField(self, painter):
        """ Overwrite VispaWidget.drawTextField()
        
        Do not show text field, just using the text for tooltip.
        """
        pass
    
    def mousePressEvent(self, event):
        """ Registers position for starting drag.
        """
        if self._dragablePort and event.button() == Qt.LeftButton:
            self._startDragPosition = QPoint(event.pos())
        VispaWidget.mousePressEvent(self, event)
            
    def mouseMoveEvent(self, event):
        """ If minimum distance from mousePressEvent is reached initiates dragging.
        """
        #logging.debug(self.__class__.__name__ +": mouseMoveEvent()")
        if self._dragablePort and self._startDragPosition:
            if not self._aimConnection and (event.pos() - self._startDragPosition).manhattanLength() >= QApplication.startDragDistance():
                self._aimConnection = PointToPointConnection(self.moduleParent(), self.connectionPoint(), self.mapTo(self.moduleParent(), event.pos()))
                self._aimConnection.show()
#                print "start dragging"
#                drag = QDrag(self)
#                mimeData = QMimeData()
#                mimeData.setText(self.DRAG_PORT_TEXT)
#                drag.setMimeData(mimeData)
#                dropAction = drag.exec_()
            elif self._aimConnection:
                #print "update target point"
                self._aimConnection.updateTargetPoint(self.mapTo(self.moduleParent(), event.pos()))
        VispaWidget.mouseMoveEvent(self, event)
        
    def mouseReleaseEvent(self, event):
        """ Calls realeseMouse() to make sure the widget does not grab the mouse.
        
        Necessary because ConnectableWidgetOwner.propagateEventUnderConnectionWidget() may call grabMouse() on this widget.
        """
        logging.debug(self.__class__.__name__ +": mouseReleaseEvent()")
        self.releaseMouse()
        if self._dragablePort:
            if self._aimConnection:
                self._aimConnection.hide()  # don't appear as childWidget()
                self._aimConnection.delete()
                self._aimConnection = None
            
            moduleParentPosition = self.mapTo(self.moduleParent(), event.pos())
            #widget = self.moduleParent().childAt(moduleParentPosition)
            widget = None
            for child in reversed(self.moduleParent().children()):
                if child.isVisible() and child.geometry().contains(moduleParentPosition) and not isinstance(child, PortConnection):
                    widget = child
                    break
        
            if hasattr(widget, "dropAreaPort"):
                self.moduleParent().tabController().createPortConnection(self,
                                                                     widget.dropAreaPort(widget.mapFrom(self.moduleParent(),
                                                                                                        moduleParentPosition)
                                                                                        )
                                                                     )
            elif isinstance(widget, PortWidget):
                self.moduleParent().tabController().createPortConnection(self, widget)
            
        VispaWidget.mouseReleaseEvent(self, event)
        
#TODO: When it's certain that drag and drop functionality is not needed any more, remove drag n drop code.         
    def dragEnterEvent(self, event):
        """ Accepts drag enter event if event's mimeData has set self.DRAG_PORT_TEXT as text.
        """
        if self._dragablePort and event.mimeData().text() == self.DRAG_PORT_TEXT:
            event.acceptProposedAction()
        
    def dropEvent(self, event):
        """ Handle drop of another port.
        
        Tells tab controller to create a port connection between other port and this one.
        """
        if self._dragablePort and event.mimeData().text() == self.DRAG_PORT_TEXT:
            if self.moduleParent().tabController().createPortConnection(event.source(), self):
                event.acceptProposedAction()

class SinkPort(PortWidget):
    """ Class for sink port of ConnectableWidgets.
    
    Sets colors, port type and connection direction.
    """
    
    PEN_COLOR = QColor()
    FILL_COLOR1 = QColor(0, 150, 0)
    FILL_COLOR2 = QColor(0, 100, 0)
    PORT_TYPE = 'sink'
    CONNECTION_DIRECTION = PointToPointConnection.ConnectionDirection.LEFT
    TITLE_COLOR = FILL_COLOR1
    
#    def __init__(self, parent=None, name='default'):
#        """ Constructor.
#        """
#        PortWidget.__init__(self, parent, name)


class SourcePort(PortWidget):
    """ Class for sink port of ConnectableWidgets.
    
    Sets colors, port type and connection direction.

    """
    
    PEN_COLOR = QColor()
    FILL_COLOR1 = QColor(150, 0, 0)
    FILL_COLOR2 = QColor(100, 0, 0)
    PORT_TYPE = 'source'
    CONNECTION_DIRECTION = PointToPointConnection.ConnectionDirection.RIGHT
    TITLE_COLOR = FILL_COLOR1
    
#    def __init__(self, parent=None, name='default'):
#        """ Constructor.
#        """
#        PortWidget.__init__(self, parent, name)
        
