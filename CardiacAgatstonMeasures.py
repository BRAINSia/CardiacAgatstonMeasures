from __main__ import vtk, qt, ctk, slicer
import SimpleITK as sitk
import sitkUtils as su
import EditorLib
import Editor
import LabelStatistics

#
# CardiacAgatstonMeasures
#

class CardiacAgatstonMeasures:
    def __init__(self, parent):
        parent.title = "Cardiac Agatston Measures"
        parent.categories = ["Cardiac Agatston Measures"]
        parent.dependencies = []
        parent.contributors = ["Jessica Forbes (SINAPSE)",
                               "Hans Johnson (SINAPSE)"]
        parent.helpText = """
                                   This module will auto-segment the calcium deposits in Cardiac CT scans.  The user selects calcium clusters that represent calcium plaques.  The user then selects calcium clusters that do not represent calcium plaques and that should not be included in the final calculations.  Slicer will take the mean, peak, variance, mass and threshold and put the values into an Excel (or Excel compatible) file.
                                   """
        parent.acknowledgementText = """
                                   This file was originally developed by Jessica Forbes and Hans Johnson of the SINAPSE Lab at the University of Iowa.""" # replace with organization, grant and thanks.
        self.parent = parent

#
# CardiacAgatstonMeasuresWidget
#

class CardiacAgatstonMeasuresWidget:
    def __init__(self, parent = None):
        self.currentRegistrationInterface = None
        self.thresholdValue = 130
        self.changeIslandTool = None
        self.editUtil = EditorLib.EditUtil.EditUtil()

        if not parent:
            self.parent = slicer.qMRMLWidget()
            self.parent.setLayout(qt.QVBoxLayout())
            self.parent.setMRMLScene(slicer.mrmlScene)
        else:
            self.parent = parent
        self.layout = self.parent.layout()
        if not parent:
            self.setup()
            self.parent.show()

        # imports custom Slicer lookup color table file
        slicer.util.loadColorTable('/tmp/cardiacLUT.ctbl')

    def setup(self):
        # Instantiate and connect widgets ...
        
        #
        # Reload and Test area
        #
        if True:
            """Developer interface"""
            reloadCollapsibleButton = ctk.ctkCollapsibleButton()
            reloadCollapsibleButton.text = "Advanced - Reload && Test"
            reloadCollapsibleButton.collapsed = False
            self.layout.addWidget(reloadCollapsibleButton)
            reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)
            
            # reload button
            # (use this during development, but remove it when delivering
            #  your module to users)
            self.reloadButton = qt.QPushButton("Reload")
            self.reloadButton.toolTip = "Reload this module."
            self.reloadButton.name = "CardiacAgatstonMeasures Reload"
            reloadFormLayout.addWidget(self.reloadButton)
            #self.reloadButton.connect('clicked(bool)',self.onHelloWorldButtonClicked)
            self.reloadButton.connect('clicked()', self.onReload)

        # Collapsible button for Input Parameters
        self.measuresCollapsibleButton = ctk.ctkCollapsibleButton()
        self.measuresCollapsibleButton.text = "Input Parameters"
        self.layout.addWidget(self.measuresCollapsibleButton)

        # Collapsible button for Label Parameters
        self.labelsCollapsibleButton = ctk.ctkCollapsibleButton()
        self.labelsCollapsibleButton.text = "Label Parameters"
        self.layout.addWidget(self.labelsCollapsibleButton)

        # Collapsible button for Statistics Parameters
        self.statisticsCollapsibleButton = ctk.ctkCollapsibleButton()
        self.statisticsCollapsibleButton.text = "Statistics Parameters"
        self.layout.addWidget(self.statisticsCollapsibleButton)

        # Layout within the sample collapsible button
        self.measuresFormLayout = qt.QFormLayout(self.measuresCollapsibleButton)
        self.labelsFormLayout = qt.QFormLayout(self.labelsCollapsibleButton)
        self.statisticsFormLayout = qt.QFormLayout(self.statisticsCollapsibleButton)

        # The Input Volume Selector
        self.inputFrame = qt.QFrame(self.measuresCollapsibleButton)
        self.inputFrame.setLayout(qt.QHBoxLayout())
        self.measuresFormLayout.addRow(self.inputFrame)
        self.inputSelector = qt.QLabel("Input Volume: ", self.inputFrame)
        self.inputFrame.layout().addWidget(self.inputSelector)
        self.inputSelector = slicer.qMRMLNodeComboBox(self.inputFrame)
        self.inputSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
        self.inputSelector.addEnabled = False
        self.inputSelector.removeEnabled = False
        self.inputSelector.setMRMLScene( slicer.mrmlScene )
        self.inputFrame.layout().addWidget(self.inputSelector)

        # Threshold button
        thresholdButton = qt.QPushButton("Threshold Volume")
        thresholdButton.toolTip = "Threshold the selected Input Volume"
        self.measuresFormLayout.addRow(thresholdButton)
        thresholdButton.connect('clicked(bool)', self.onThresholdButtonClicked)

        # The Input Left Main (LM) Label Selector
        LMchangeIslandButton = qt.QPushButton("LM")
        LMchangeIslandButton.toolTip = "Label - Left Main (LM)"
        self.labelsFormLayout.addRow(LMchangeIslandButton)
        LMchangeIslandButton.connect('clicked(bool)', self.onLMchangeIslandButtonClicked)

        # The Input Left Arterial Descending (LAD) Label Selector
        LADchangeIslandButton = qt.QPushButton("LAD")
        LADchangeIslandButton.toolTip = "Label - Left Arterial Descending (LAD)"
        self.labelsFormLayout.addRow(LADchangeIslandButton)
        LADchangeIslandButton.connect('clicked(bool)', self.onLADchangeIslandButtonClicked)

        # The Input Left Circumflex (LCX) Label Selector
        LCXchangeIslandButton = qt.QPushButton("LCX")
        LCXchangeIslandButton.toolTip = "Label - Left Circumflex (LCX)"
        self.labelsFormLayout.addRow(LCXchangeIslandButton)
        LCXchangeIslandButton.connect('clicked(bool)', self.onLCXchangeIslandButtonClicked)

        # The Input Right Coronary Artery (RCA) Label Selector
        RCAchangeIslandButton = qt.QPushButton("RCA")
        RCAchangeIslandButton.toolTip = "Label - Right Coronary Artery (RCA)"
        self.labelsFormLayout.addRow(RCAchangeIslandButton)
        RCAchangeIslandButton.connect('clicked(bool)', self.onRCAchangeIslandButtonClicked)

        # Quit Label Changer (LX, LAD, LCX, RCA) Button
        quitLabelChanger = qt.QPushButton("Quit Label Changer (LX, LAD, LCX, RCA)")
        quitLabelChanger.toolTip = "Click to stop any of the change label buttons"
        self.labelsFormLayout.addRow(quitLabelChanger)
        quitLabelChanger.connect('clicked(bool)', self.onQuitLabelChangerClicked)

        # localEditBox = CardiacEditBox(parent=self.parent)
        # localEditorWidget = Editor.EditorWidget(parent=self.parent)
        # localEditorWidget.setup()
        localCardiacEditorWidget = CardiacEditorWidget(parent=self.parent)
        localCardiacEditorWidget.setup()

        # Radio Buttons for Selecting 80 KEV or 120 KEV
        self.RadioButtonsFrame = qt.QFrame(self.measuresCollapsibleButton)
        self.RadioButtonsFrame.setLayout(qt.QHBoxLayout())
        self.statisticsFormLayout.addRow(self.RadioButtonsFrame)
        self.KEV80 = qt.QRadioButton("80 KEV", self.RadioButtonsFrame)
        self.KEV80.setToolTip("Select 80 KEV.")
        self.RadioButtonsFrame.layout().addWidget(self.KEV80)
        self.KEV120 = qt.QRadioButton("120 KEV", self.RadioButtonsFrame)
        self.KEV120.setToolTip("Select 120 KEV.")
        self.KEV120.checked = True
        self.RadioButtonsFrame.layout().addWidget(self.KEV120)

        # Adds Label Statistics Widget to Module
        # localLabelStatisticsWidget = CardiacStatisticsWidget(parent=self.parent)
        # localLabelStatisticsWidget.setup()

        # Calculate Statistics Button
        calculateButton = qt.QPushButton("Calculate Statistics")
        calculateButton.toolTip = "Calculating Statistics"
        self.statisticsFormLayout.addRow(calculateButton)
        calculateButton.connect('clicked(bool)', self.onCalculatedButtonClicked)

        # Add vertical spacer
        self.layout.addStretch(1)
        
        # Set local var as instance attribute
        self.thresholdButton = thresholdButton
        self.calculateButton = calculateButton
        self.LMchangeIslandButton = LMchangeIslandButton
        self.LADchangeIslandButton = LADchangeIslandButton
        self.LCXchangeIslandButton = LCXchangeIslandButton
        self.RCAchangeIslandButton = RCAchangeIslandButton
        self.quitLabelChanger = quitLabelChanger

    def onLMchangeIslandButtonClicked(self):
        self.changeIslandButtonClicked(2)

    def onLADchangeIslandButtonClicked(self):
        self.changeIslandButtonClicked(3)

    def onLCXchangeIslandButtonClicked(self):
        self.changeIslandButtonClicked(4)

    def onRCAchangeIslandButtonClicked(self):
        self.changeIslandButtonClicked(5)

    def changeIslandButtonClicked(self, label):
        lm = slicer.app.layoutManager()
        changeIslandOptions = EditorLib.ChangeIslandEffectOptions()
        changeIslandOptions.setMRMLDefaults()
        changeIslandOptions.__del__()
        sliceWidget = lm.sliceWidget('Red')
        self.editUtil.setLabel(label)
        self.changeIslandTool = EditorLib.ChangeIslandEffectTool(sliceWidget)
        self.changeIslandTool.processEvent()

    def onQuitLabelChangerClicked(self):
        print 'onQuitLabelChangerClicked'
        print self.changeIslandTool
        self.changeIslandTool.cleanup()
        changeIslandOptions = EditorLib.ChangeIslandEffectOptions()
        changeIslandOptions.destroy()
        self.changeIslandTool = None

    def onThresholdButtonClicked(self):
        print "Thresholding at {0}".format(self.thresholdValue)
        inputVolumeName = su.PullFromSlicer(self.inputSelector.currentNode().GetName())
        thresholdImage = sitk.BinaryThreshold(inputVolumeName, self.thresholdValue, 2000)
        castedThresholdImage = sitk.Cast(thresholdImage, sitk.sitkInt16)
        su.PushLabel(castedThresholdImage,'calcium')
        colorNode = self.editUtil.getColorNode()
        cardiacLUT = slicer.util.getNode('cardiacLUT')
        cardiacLutTable = cardiacLUT.GetLookupTable()
        colorNode.SetLookupTable(cardiacLutTable)

    def onCalculatedButtonClicked(self):
        #Just temporary code, will calculate statistics and show in table
        print "Calculating Statistics"
        calcium = su.PullFromSlicer('calcium')
        all_labels = [0, 1, 2, 3, 4, 5]
        heart = su.PullFromSlicer(self.inputSelector.currentNode().GetName())
        sliceAgatstonPerLabel = self.ComputeSlicewiseAgatstonScores(calcium, heart, all_labels)
        #print sliceAgatstonPerLabel
        print "-"*50
        self.computeOverallAgatstonScore(sliceAgatstonPerLabel)
        print "-"*50

    def computeOverallAgatstonScore(self, sliceAgatstonPerLabel):
        for (label, scores) in sliceAgatstonPerLabel.items():
            print "Label", label, ": Agatston Score = ", sum(scores)

    def KEV2AgatstonIndex(self, kev):
        AgatstonIndex = 0.0
        if self.KEV120.checked:
            if kev >= 130:   #range = 130-199
                AgatstonIndex = 1.0
            if kev >= 200:   #range = 200-299
                AgatstonIndex = 2.0
            if kev >= 300:   #range = 300-399
                AgatstonIndex = 3.0
            if kev >= 400:   #range >= 400
                AgatstonIndex = 4.0
        elif self.KEV80.checked:
            if kev >= 167:   #range = 167-265
                AgatstonIndex = 1.0
            if kev >= 266:   #range = 266-407
                AgatstonIndex = 2.0
            if kev >= 408:   #range = 408-550
                AgatstonIndex = 3.0
            if kev >= 551:   #range >= 551
                AgatstonIndex = 4.0
        return AgatstonIndex

    def ComputeSlicewiseAgatstonScores(self, calcium, heart, all_labels):
        sliceAgatstonPerLabel=dict() ## A dictionary { labels : [AgatstonValues] }
        ##Initialize Dictionary entries with empty list
        for label in all_labels:
            if label == 0:
                continue
            sliceAgatstonPerLabel[label]=list()

        ImageSpacing = calcium.GetSpacing()
        ImageIndex=range(0,calcium.GetSize()[2])
        for index in ImageIndex:
            slice_calcium = calcium[:,:,index]
            slice_img = heart[:,:,index]
            slice_ls=sitk.LabelStatisticsImageFilter()
            slice_ls.Execute(slice_img,slice_calcium)
            for label in all_labels:
                if label == 0 or label == 5:
                    continue
                AgatstonValue = 0.0
                if slice_ls.HasLabel(label):
                    slice_count = slice_ls.GetCount(label)
                    slice_area = slice_count*ImageSpacing[0]*ImageSpacing[1]
                    #slice_volume = slice_area*ImageSpacing[2]
                    #slice_mean = slice_ls.GetMean(label)
                    slice_max = slice_ls.GetMaximum(label)
                    #print "label: ",label," index: ",index," slice area: ", slice_area," ", slice_max, " ", KEV2AgatstonIndex( slice_max )*slice_area
                    slice_Agatston = slice_area * self.KEV2AgatstonIndex( slice_max )
                    #slice_load = slice_mean
                    AgatstonValue = slice_Agatston

                sliceAgatstonPerLabel[label].append(AgatstonValue)
        return sliceAgatstonPerLabel

    def onReload(self,moduleName="CardiacAgatstonMeasures"):
        """Generic reload method for any scripted module.
            ModuleWizard will subsitute correct default moduleName.
            Note: customized for use in LandmarkRegistration
            """
        import imp, sys, os, slicer
        import SimpleITK as sitk
        import sitkUtils as su
        import EditorLib

        # first, destroy the current plugin, since it will
        # contain subclasses of the RegistrationLib modules
        if self.currentRegistrationInterface:
            self.currentRegistrationInterface.destroy()

        # now reload the RegistrationLib source code
        # - set source file path
        # - load the module to the global space
        filePath = eval('slicer.modules.%s.path' % moduleName.lower())
        p = os.path.dirname(filePath)
        if not sys.path.__contains__(p):
            sys.path.insert(0,p)
        for subModuleName in ("pqWidget", "Visualization", "Landmarks", ):
            fp = open(filePath, "r")
            globals()[subModuleName] = imp.load_module(subModuleName, fp, filePath, ('.py', 'r', imp.PY_SOURCE))
            fp.close()

        # # now reload all the support code and have the plugins
        # # re-register themselves with slicer
        # oldPlugins = slicer.modules.registrationPlugins
        # slicer.modules.registrationPlugins = {}
        # for plugin in oldPlugins.values():
        #     pluginModuleName = plugin.__module__.lower()
        #     if hasattr(slicer.modules,pluginModuleName):
        #         # for a plugin from an extension, need to get the source path
        #         # from the module
        #         module = getattr(slicer.modules,pluginModuleName)
        #         sourceFile = module.path
        #     else:
        #         # for a plugin built with slicer itself, the file path comes
        #         # from the pyc path noted as __file__ at startup time
        #         sourceFile = plugin.sourceFile.replace('.pyc', '.py')
        #     imp.load_source(plugin.__module__, sourceFile)
        # oldPlugins = None

        widgetName = moduleName + "Widget"

        # now reload the widget module source code
        # - set source file path
        # - load the module to the global space
        filePath = eval('slicer.modules.%s.path' % moduleName.lower())
        p = os.path.dirname(filePath)
        if not sys.path.__contains__(p):
            sys.path.insert(0,p)
        fp = open(filePath, "r")
        globals()[moduleName] = imp.load_module(
            moduleName, fp, filePath, ('.py', 'r', imp.PY_SOURCE))
        fp.close()

        # rebuild the widget
        # - find and hide the existing widget
        # - create a new widget in the existing parent
        parent = slicer.util.findChildren(name='%s Reload' % moduleName)[0].parent().parent()
        for child in parent.children():
          try:
            child.hide()
          except AttributeError:
            pass
        # Remove spacer items
        item = parent.layout().itemAt(0)
        while item:
          parent.layout().removeItem(item)
          item = parent.layout().itemAt(0)

        # # delete the old widget instance
        # if hasattr(globals()['slicer'].modules, widgetName):
        #   getattr(globals()['slicer'].modules, widgetName).cleanup()

        # create new widget inside existing parent
        globals()[widgetName.lower()] = eval(
            'globals()["%s"].%s(parent)' % (moduleName, widgetName))
        globals()[widgetName.lower()].setup()
        setattr(globals()['slicer'].modules, widgetName, globals()[widgetName.lower()])

class CardiacStatisticsWidget(LabelStatistics.LabelStatisticsWidget):

    def setup(self):
        #
        # the grayscale volume selector
        #
        self.grayscaleSelectorFrame = qt.QFrame(self.parent)
        self.grayscaleSelectorFrame.setLayout(qt.QHBoxLayout())
        self.parent.layout().addWidget(self.grayscaleSelectorFrame)

        self.grayscaleSelectorLabel = qt.QLabel("Grayscale Volume: ", self.grayscaleSelectorFrame)
        self.grayscaleSelectorLabel.setToolTip( "Select the grayscale volume (background grayscale scalar volume node) for statistics calculations")
        self.grayscaleSelectorFrame.layout().addWidget(self.grayscaleSelectorLabel)

        self.grayscaleSelector = slicer.qMRMLNodeComboBox(self.grayscaleSelectorFrame)
        self.grayscaleSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
        self.grayscaleSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 0 )
        self.grayscaleSelector.selectNodeUponCreation = False
        self.grayscaleSelector.addEnabled = False
        self.grayscaleSelector.removeEnabled = False
        self.grayscaleSelector.noneEnabled = True
        self.grayscaleSelector.showHidden = False
        self.grayscaleSelector.showChildNodeTypes = False
        self.grayscaleSelector.setMRMLScene( slicer.mrmlScene )
        # TODO: need to add a QLabel
        # self.grayscaleSelector.SetLabelText( "Master Volume:" )
        self.grayscaleSelectorFrame.layout().addWidget(self.grayscaleSelector)

        #
        # the label volume selector
        #
        self.labelSelectorFrame = qt.QFrame()
        self.labelSelectorFrame.setLayout( qt.QHBoxLayout() )
        self.parent.layout().addWidget( self.labelSelectorFrame )

        self.labelSelectorLabel = qt.QLabel()
        self.labelSelectorLabel.setText( "Label Map: " )
        self.labelSelectorFrame.layout().addWidget( self.labelSelectorLabel )

        self.labelSelector = slicer.qMRMLNodeComboBox()
        self.labelSelector.nodeTypes = ( "vtkMRMLScalarVolumeNode", "" )
        self.labelSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", "1" )
        # todo addAttribute
        self.labelSelector.selectNodeUponCreation = False
        self.labelSelector.addEnabled = False
        self.labelSelector.noneEnabled = True
        self.labelSelector.removeEnabled = False
        self.labelSelector.showHidden = False
        self.labelSelector.showChildNodeTypes = False
        self.labelSelector.setMRMLScene( slicer.mrmlScene )
        self.labelSelector.setToolTip( "Pick the label map to edit" )
        self.labelSelectorFrame.layout().addWidget( self.labelSelector )

        # Apply button
        self.applyButton = qt.QPushButton("Apply")
        self.applyButton.toolTip = "Calculate Statistics."
        self.applyButton.enabled = False
        self.parent.layout().addWidget(self.applyButton)

        # model and view for stats table
        self.view = qt.QTableView()
        self.view.sortingEnabled = True
        self.parent.layout().addWidget(self.view)

        # Chart button
        self.chartFrame = qt.QFrame()
        self.chartFrame.setLayout(qt.QHBoxLayout())
        self.parent.layout().addWidget(self.chartFrame)
        self.chartButton = qt.QPushButton("Chart")
        self.chartButton.toolTip = "Make a chart from the current statistics."
        self.chartFrame.layout().addWidget(self.chartButton)
        self.chartOption = qt.QComboBox()
        self.chartOption.addItems(self.chartOptions)
        self.chartFrame.layout().addWidget(self.chartOption)
        self.chartIgnoreZero = qt.QCheckBox()
        self.chartIgnoreZero.setText('Ignore Zero')
        self.chartIgnoreZero.checked = False
        self.chartIgnoreZero.setToolTip('Do not include the zero index in the chart to avoid dwarfing other bars')
        self.chartFrame.layout().addWidget(self.chartIgnoreZero)
        self.chartFrame.enabled = False

        # Save button
        self.saveButton = qt.QPushButton("Save")
        self.saveButton.toolTip = "Calculate Statistics."
        self.saveButton.enabled = False
        self.parent.layout().addWidget(self.saveButton)

        # Add vertical spacer
        self.parent.layout().addStretch(1)

        # connections
        self.applyButton.connect('clicked()', self.onApply)
        self.chartButton.connect('clicked()', self.onChart)
        self.saveButton.connect('clicked()', self.onSave)
        self.grayscaleSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onGrayscaleSelect)
        self.labelSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onLabelSelect)

class CardiacEditorWidget(Editor.EditorWidget):
    def createEditBox(self):
        self.editBoxFrame = qt.QFrame(self.effectsToolsFrame)
        self.editBoxFrame.objectName = 'EditBoxFrame'
        self.editBoxFrame.setLayout(qt.QVBoxLayout())
        self.effectsToolsFrame.layout().addWidget(self.editBoxFrame)
        self.toolsBox = CardiacEditBox(self.editBoxFrame, optionsFrame=self.effectOptionsFrame)

class CardiacEditBox(EditorLib.EditBox):
    # create the edit box
    def create(self):

        self.findEffects()

        self.mainFrame = qt.QFrame(self.parent)
        self.mainFrame.objectName = 'MainFrame'
        vbox = qt.QVBoxLayout()
        self.mainFrame.setLayout(vbox)
        self.parent.layout().addWidget(self.mainFrame)

        #
        # the buttons
        #
        self.rowFrames = []
        self.actions = {}
        self.buttons = {}
        self.icons = {}
        self.callbacks = {}

        # create all of the buttons
        # createButtonRow() ensures that only effects in self.effects are exposed,
        self.createButtonRow( ("DefaultTool", "IdentifyIslandsEffect", "ChangeIslandEffect", "RemoveIslandsEffect", "SaveIslandEffect","ThresholdEffect", "ChangeLabelEffect", "MakeModelEffect") )

        extensions = []
        for k in slicer.modules.editorExtensions:
          extensions.append(k)
        self.createButtonRow( extensions )

        self.createButtonRow( ("PreviousCheckPoint", "NextCheckPoint"), rowLabel="Undo/Redo: " )

        #
        # the labels
        #
        self.toolsActiveToolFrame = qt.QFrame(self.parent)
        self.toolsActiveToolFrame.setLayout(qt.QHBoxLayout())
        self.parent.layout().addWidget(self.toolsActiveToolFrame)
        self.toolsActiveTool = qt.QLabel(self.toolsActiveToolFrame)
        self.toolsActiveTool.setText( 'Active Tool:' )
        self.toolsActiveTool.setStyleSheet("background-color: rgb(232,230,235)")
        self.toolsActiveToolFrame.layout().addWidget(self.toolsActiveTool)
        self.toolsActiveToolName = qt.QLabel(self.toolsActiveToolFrame)
        self.toolsActiveToolName.setText( '' )
        self.toolsActiveToolName.setStyleSheet("background-color: rgb(232,230,235)")
        self.toolsActiveToolFrame.layout().addWidget(self.toolsActiveToolName)

        vbox.addStretch(1)

        self.updateUndoRedoButtons()
