from __main__ import vtk, qt, ctk, slicer
import os
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
        self.thresholdValue = None
        self.changeIslandTool = None
        self.editUtil = EditorLib.EditUtil.EditUtil()
        self.inputImageNode = None
        self.calciumLabelNode = None
        self.cardiacLutNode = None
        self.localCardiacEditorWidget = None

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

        self.InputTestImageNode = None

        # import test image
        self.InputTestImageNode = slicer.util.getNode('p1_1')
        if not self.InputTestImageNode:
            slicer.util.loadVolume('/scratch/p1_1.nii.gz')

        # imports custom Slicer lookup color table file
        self.cardiacLutNode = slicer.util.getNode('cardiacLUT')
        if not self.cardiacLutNode:
            slicer.util.loadColorTable('/scratch/cardiacLUT.ctbl')

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
        #self.layout.addWidget(self.labelsCollapsibleButton)

        # Layout within the sample collapsible button
        self.measuresFormLayout = qt.QFormLayout(self.measuresCollapsibleButton)
        self.labelsFormLayout = qt.QFormLayout(self.labelsCollapsibleButton)

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

        # Radio Buttons for Selecting 80 KEV or 120 KEV
        self.RadioButtonsFrame = qt.QFrame(self.measuresCollapsibleButton)
        self.RadioButtonsFrame.setLayout(qt.QHBoxLayout())
        self.measuresFormLayout.addRow(self.RadioButtonsFrame)
        self.KEV80 = qt.QRadioButton("80 KEV", self.RadioButtonsFrame)
        self.KEV80.setToolTip("Select 80 KEV.")
        self.KEV80.checked = False
        self.RadioButtonsFrame.layout().addWidget(self.KEV80)
        self.KEV120 = qt.QRadioButton("120 KEV", self.RadioButtonsFrame)
        self.KEV120.setToolTip("Select 120 KEV.")
        self.KEV120.checked = False
        self.RadioButtonsFrame.layout().addWidget(self.KEV120)

        # Threshold button
        thresholdButton = qt.QPushButton("Threshold Volume")
        thresholdButton.toolTip = "Threshold the selected Input Volume"
        thresholdButton.setStyleSheet("background-color: rgb(230,241,255)")
        self.measuresFormLayout.addRow(thresholdButton)
        thresholdButton.connect('clicked(bool)', self.onThresholdButtonClicked)

        # Add vertical spacer
        self.layout.addStretch(1)
        
        # Set local var as instance attribute
        self.thresholdButton = thresholdButton

    def onThresholdButtonClicked(self):
        if not self.KEV120.checked and not self.KEV80.checked:
            qt.QMessageBox.warning(slicer.util.mainWindow(),
                "Select KEV", "The KEV (80 or 120) must be selected to continue.")
            return

        self.inputImageNode = self.inputSelector.currentNode()
        inputVolumeName = self.inputImageNode.GetName()
        # Sets minimum threshold value based on KEV80 or KEV120
        if self.KEV80.checked:
            self.thresholdValue = 167
            calciumName = "{0}_80KEV_{1}HU_Calcium_Label".format(inputVolumeName, self.thresholdValue)
        elif self.KEV120.checked:
            self.thresholdValue = 130
            calciumName = "{0}_120KEV_{1}HU_Calcium_Label".format(inputVolumeName, self.thresholdValue)

        print "Thresholding at {0}".format(self.thresholdValue)
        inputVolume = su.PullFromSlicer(inputVolumeName)
        thresholdImage = sitk.BinaryThreshold(inputVolume, self.thresholdValue, 4000)
        castedThresholdImage = sitk.Cast(thresholdImage, sitk.sitkInt16)
        su.PushLabel(castedThresholdImage, calciumName)

        # Set the color lookup table (LUT) to the custom cardiacLUT
        self.calciumLabelNode = slicer.util.getNode(calciumName)
        self.cardiacLutNode = slicer.util.getNode('cardiacLUT')
        cardiacLutID = self.cardiacLutNode.GetID()
        calciumDisplayNode = self.calciumLabelNode.GetDisplayNode()
        calciumDisplayNode.SetAndObserveColorNodeID(cardiacLutID)

        # Creates and adds the custom Editor Widget to the module
        self.localCardiacEditorWidget = CardiacEditorWidget(parent=self.parent, showVolumesFrame=False)
        self.localCardiacEditorWidget.setup()

        # Adds Label Statistics Widget to Module
        localLabelStatisticsWidget = CardiacStatisticsWidget(self.KEV120, self.KEV80,
                                                             self.localCardiacEditorWidget,
                                                             parent=self.parent)
        localLabelStatisticsWidget.setup()

    def onReload(self,moduleName="CardiacAgatstonMeasures"):
        """Generic reload method for any scripted module.
            ModuleWizard will subsitute correct default moduleName.
            Note: customized for use in LandmarkRegistration
            """
        import imp, sys, os, slicer
        import SimpleITK as sitk
        import sitkUtils as su
        import EditorLib

        # selects default tool to stop the ChangeIslandTool
        if self.localCardiacEditorWidget:
            self.localCardiacEditorWidget.toolsBox.selectEffect("DefaultTool")

        # clears the mrml scene
        slicer.mrmlScene.Clear(0)

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
    def __init__(self, KEV120, KEV80, localCardiacEditorWidget, parent=None):
        self.chartOptions = ("Agatston Score", "Count", "Volume mm^3", "Volume cc", "Min", "Max", "Mean", "StdDev")
        if not parent:
            self.parent = slicer.qMRMLWidget()
            self.parent.setLayout(qt.QVBoxLayout())
            self.parent.setMRMLScene(slicer.mrmlScene)
        else:
            self.parent = parent
        self.logic = None
        self.grayscaleNode = None
        self.labelNode = None
        self.fileName = None
        self.fileDialog = None
        self.KEV120 = KEV120
        self.KEV80 = KEV80
        self.localCardiacEditorWidget = localCardiacEditorWidget
        if not parent:
            self.setup()
            self.grayscaleSelector.setMRMLScene(slicer.mrmlScene)
            self.labelSelector.setMRMLScene(slicer.mrmlScene)
            self.parent.show()

    def setup(self):

        # Set the grayscaleNode and labelNode to the current active volume and label
        selectionNode = slicer.app.applicationLogic().GetSelectionNode()
        self.grayscaleNode = slicer.util.getNode(selectionNode.GetActiveVolumeID())
        self.labelNode = slicer.util.getNode(selectionNode.GetActiveLabelVolumeID())

        # Apply button
        self.applyButton = qt.QPushButton("Apply")
        self.applyButton.toolTip = "Calculate Statistics."
        self.applyButton.setStyleSheet("background-color: rgb(230,241,255)")
        self.applyButton.enabled = True
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
        self.saveButton.setStyleSheet("background-color: rgb(230,241,255)")
        self.saveButton.enabled = False
        self.parent.layout().addWidget(self.saveButton)

        # Add vertical spacer
        self.parent.layout().addStretch(1)

        # connections
        self.applyButton.connect('clicked()', self.onApply)
        self.chartButton.connect('clicked()', self.onChart)
        self.saveButton.connect('clicked()', self.onSave)

    def onApply(self):
        """Calculate the label statistics
        """
        if not self.volumesAreValid():
            qt.QMessageBox.warning(slicer.util.mainWindow(),
                "Label Statistics", "Volumes do not have the same geometry.")
            return

        # selects default tool to stop the ChangeIslandTool
        self.localCardiacEditorWidget.toolsBox.selectEffect("DefaultTool")

        self.applyButton.text = "Working..."
        # TODO: why doesn't processEvents alone make the label text change?
        self.applyButton.repaint()
        slicer.app.processEvents()
        self.logic = CardiacLabelStatisticsLogic(self.grayscaleNode, self.labelNode, self.KEV120, self.KEV80)
        self.populateStats()
        self.chartFrame.enabled = True
        self.saveButton.enabled = True
        self.applyButton.text = "Apply"

    def onSave(self):
        """save the label statistics
        """
        (inputVolumeAndKev, dirName) = self.createDir()
        # saves the current scene to selected folder
        l = slicer.app.applicationLogic()
        l.SaveSceneToSlicerDataBundleDirectory(dirName, None)

        # saves the csv files to selected folder
        csvFileName = os.path.join(dirName, "{0}_Agatston_Scores.csv".format(inputVolumeAndKev))
        self.logic.saveStats(csvFileName)

    def createDir(self):
        if self.KEV80.checked:
            inputVolumeAndKev = "{0}_80KEV".format(self.grayscaleNode.GetName())
        elif self.KEV120.checked:
            inputVolumeAndKev = "{0}_120KEV".format(self.grayscaleNode.GetName())
        baseDirName = "/Shared/johnsonhj/HDNI/20130422_Sigurdsson/2014PatientDataTestDir/results"
        dirName = os.path.join(baseDirName, inputVolumeAndKev)
        if not os.path.exists(dirName):
            os.mkdir(dirName)
        return inputVolumeAndKev, dirName

    def populateStats(self):
        if not self.logic:
            return
        displayNode = self.labelNode.GetDisplayNode()
        colorNode = displayNode.GetColorNode()
        lut = colorNode.GetLookupTable()
        self.items = []
        self.model = qt.QStandardItemModel()
        self.view.setModel(self.model)
        self.view.verticalHeader().visible = False
        row = 0
        for i in self.logic.labelStats["Labels"]:
            color = qt.QColor()
            rgb = lut.GetTableValue(i)
            color.setRgb(rgb[0]*255,rgb[1]*255,rgb[2]*255)
            item = qt.QStandardItem()
            item.setData(color,qt.Qt.DecorationRole)
            item.setToolTip(colorNode.GetColorName(i))
            self.model.setItem(row,0,item)
            self.items.append(item)
            col = 1
            for k in self.logic.keys:
                item = qt.QStandardItem()
                if k == "Label Name":
                    item.setData(self.logic.labelStats[i,k],qt.Qt.DisplayRole)
                else:
                    # set data as float with Qt::DisplayRole
                    item.setData(float(self.logic.labelStats[i,k]),qt.Qt.DisplayRole)
                item.setToolTip(colorNode.GetColorName(i))
                self.model.setItem(row,col,item)
                self.items.append(item)
                col += 1
            row += 1

        self.view.setColumnWidth(0,30)
        self.model.setHeaderData(0,1," ")
        col = 1
        for k in self.logic.keys:
            self.view.setColumnWidth(col,15*len(k))
            self.model.setHeaderData(col,1,k)
            col += 1

class CardiacLabelStatisticsLogic(LabelStatistics.LabelStatisticsLogic):
    """Implement the logic to calculate label statistics.
      Nodes are passed in as arguments.
      Results are stored as 'statistics' instance variable.
      """

    def __init__(self, grayscaleNode, labelNode, KEV120, KEV80, fileName=None):
        #import numpy

        self.keys = ("Index", "Label Name", "Agatston Score", "Count", "Volume mm^3", "Volume cc", "Min", "Max", "Mean", "StdDev")
        cubicMMPerVoxel = reduce(lambda x,y: x*y, labelNode.GetSpacing())
        ccPerCubicMM = 0.001

        # TODO: progress and status updates
        # this->InvokeEvent(vtkLabelStatisticsLogic::StartLabelStats, (void*)"start label stats")

        self.labelStats = {}
        self.labelStats['Labels'] = []

        stataccum = vtk.vtkImageAccumulate()
        if vtk.VTK_MAJOR_VERSION <= 5:
            stataccum.SetInput(labelNode.GetImageData())
        else:
            stataccum.SetInputConnection(labelNode.GetImageDataConnection())
        stataccum.Update()
        lo = int(stataccum.GetMin()[0])
        hi = int(stataccum.GetMax()[0])

        displayNode = labelNode.GetDisplayNode()
        colorNode = displayNode.GetColorNode()

        self.labelNode = labelNode
        self.grayscaleNode = grayscaleNode
        self.KEV80 = KEV80
        self.KEV120 = KEV120
        self.calculateAgatstonScores()

        for i in xrange(lo,hi+1):
            # skip indices 0 (background) and 1 (default threshold pixels)
            # because these are not calcium and do not have an Agatston score
            if i == 0 or i == 1:
                continue

            # this->SetProgress((float)i/hi);
            # std::string event_message = "Label "; std::stringstream s; s << i; event_message.append(s.str());
            # this->InvokeEvent(vtkLabelStatisticsLogic::LabelStatsOuterLoop, (void*)event_message.c_str());

            # logic copied from slicer3 LabelStatistics
            # to create the binary volume of the label
            # //logic copied from slicer2 LabelStatistics MaskStat
            # // create the binary volume of the label
            thresholder = vtk.vtkImageThreshold()
            if vtk.VTK_MAJOR_VERSION <= 5:
                thresholder.SetInput(labelNode.GetImageData())
            else:
                thresholder.SetInputConnection(labelNode.GetImageDataConnection())
            thresholder.SetInValue(1)
            thresholder.SetOutValue(0)
            thresholder.ReplaceOutOn()
            thresholder.ThresholdBetween(i,i)
            thresholder.SetOutputScalarType(grayscaleNode.GetImageData().GetScalarType())
            thresholder.Update()

            # this.InvokeEvent(vtkLabelStatisticsLogic::LabelStatsInnerLoop, (void*)"0.25");

            #  use vtk's statistics class with the binary labelmap as a stencil
            stencil = vtk.vtkImageToImageStencil()
            if vtk.VTK_MAJOR_VERSION <= 5:
                stencil.SetInput(thresholder.GetOutput())
            else:
                stencil.SetInputConnection(thresholder.GetOutputPort())
            stencil.ThresholdBetween(1, 1)

            # this.InvokeEvent(vtkLabelStatisticsLogic::LabelStatsInnerLoop, (void*)"0.5")

            stat1 = vtk.vtkImageAccumulate()
            if vtk.VTK_MAJOR_VERSION <= 5:
                stat1.SetInput(grayscaleNode.GetImageData())
            else:
                stat1.SetInputConnection(grayscaleNode.GetImageDataConnection())
            stat1.SetStencil(stencil.GetOutput())
            stat1.Update()

            # this.InvokeEvent(vtkLabelStatisticsLogic::LabelStatsInnerLoop, (void*)"0.75")

            if stat1.GetVoxelCount() > 0:
                # add an entry to the LabelStats list
                self.labelStats["Labels"].append(i)
                self.labelStats[i,"Index"] = i
                self.labelStats[i,"Label Name"] = colorNode.GetColorName(i)
                self.labelStats[i,"Agatston Score"] = self.AgatstonScoresPerLabel[i]
                self.labelStats[i,"Count"] = stat1.GetVoxelCount()
                self.labelStats[i,"Volume mm^3"] = self.labelStats[i,"Count"] * cubicMMPerVoxel
                self.labelStats[i,"Volume cc"] = self.labelStats[i,"Volume mm^3"] * ccPerCubicMM
                self.labelStats[i,"Min"] = stat1.GetMin()[0]
                self.labelStats[i,"Max"] = stat1.GetMax()[0]
                self.labelStats[i,"Mean"] = stat1.GetMean()[0]
                self.labelStats[i,"StdDev"] = stat1.GetStandardDeviation()[0]

            # this.InvokeEvent(vtkLabelStatisticsLogic::LabelStatsInnerLoop, (void*)"1")

        # this.InvokeEvent(vtkLabelStatisticsLogic::EndLabelStats, (void*)"end label stats")

    def calculateAgatstonScores(self):

        #Just temporary code, will calculate statistics and show in table
        print "Calculating Statistics"
        calcium = su.PullFromSlicer(self.labelNode.GetName())
        all_labels = [0, 1, 2, 3, 4, 5, 6]
        heart = su.PullFromSlicer(self.grayscaleNode.GetName())
        sliceAgatstonPerLabel = self.computeSlicewiseAgatstonScores(calcium, heart, all_labels)
        #print sliceAgatstonPerLabel
        print "-"*50
        self.computeOverallAgatstonScore(sliceAgatstonPerLabel)
        print "-"*50

    def computeOverallAgatstonScore(self, sliceAgatstonPerLabel):
        self.AgatstonScoresPerLabel = {}
        # labels 0 and 1 should not have an Agatston score
        self.AgatstonScoresPerLabel[0] = 0
        self.AgatstonScoresPerLabel[1] = 0
        for (label, scores) in sliceAgatstonPerLabel.items():
            labelScore =  sum(scores)
            print "Label", label, ": Agatston Score = ", labelScore
            self.AgatstonScoresPerLabel[label] = labelScore
        print "\nTOTAL Agatston Score = ", sum(self.AgatstonScoresPerLabel.values())

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

    def computeSlicewiseAgatstonScores(self, calcium, heart, all_labels):
        sliceAgatstonPerLabel=dict() ## A dictionary { labels : [AgatstonValues] }
        ##Initialize Dictionary entries with empty list
        for label in all_labels:
            if label == 0 or label == 1:
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
                if label == 0 or label == 1:
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

class CardiacEditorWidget(Editor.EditorWidget):

    def createEditBox(self):
        self.editLabelMapsFrame.collapsed = False
        self.editBoxFrame = qt.QFrame(self.effectsToolsFrame)
        self.editBoxFrame.objectName = 'EditBoxFrame'
        self.editBoxFrame.setLayout(qt.QVBoxLayout())
        self.effectsToolsFrame.layout().addWidget(self.editBoxFrame)
        self.toolsBox = CardiacEditBox(self.editBoxFrame, optionsFrame=self.effectOptionsFrame)
        self.turnOffLightboxes()
        self.installShortcutKeys()

    def installShortcutKeys(self):
        """Turn on editor-wide shortcuts.  These are active independent
        of the currently selected effect."""
        Key_Escape = 0x01000000 # not in PythonQt
        Key_Space = 0x20 # not in PythonQt
        self.shortcuts = []
        keysAndCallbacks = (
            ('z', self.toolsBox.undoRedo.undo),
            ('y', self.toolsBox.undoRedo.redo),
            ('h', self.editUtil.toggleCrosshair),
            ('o', self.editUtil.toggleLabelOutline),
            ('t', self.editUtil.toggleForegroundBackground),
            (Key_Escape, self.toolsBox.defaultEffect),
            ('p', lambda : self.toolsBox.selectEffect('PaintEffect')),
            ('1', self.toolsBox.onLMchangeIslandButtonClicked),
            ('2', self.toolsBox.onLADchangeIslandButtonClicked),
            ('3', self.toolsBox.onLCXchangeIslandButtonClicked),
            ('4', self.toolsBox.onRCAchangeIslandButtonClicked),
            ('5', self.toolsBox.onDefaultChangeIslandButtonClicked),
            )
        for key,callback in keysAndCallbacks:
            shortcut = qt.QShortcut(slicer.util.mainWindow())
            shortcut.setKey( qt.QKeySequence(key) )
            shortcut.connect( 'activated()', callback )
            self.shortcuts.append(shortcut)

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

        # The Input Left Main (LM) Label Selector
        LMchangeIslandButton = qt.QPushButton("LM")
        LMchangeIslandButton.toolTip = "Label - Left Main (LM)"
        LMchangeIslandButton.setStyleSheet("background-color: rgb(220,0,250)")
        self.mainFrame.layout().addWidget(LMchangeIslandButton)
        LMchangeIslandButton.connect('clicked(bool)', self.onLMchangeIslandButtonClicked)

        # The Input Left Arterial Descending (LAD) Label Selector
        LADchangeIslandButton = qt.QPushButton("LAD")
        LADchangeIslandButton.toolTip = "Label - Left Arterial Descending (LAD)"
        LADchangeIslandButton.setStyleSheet("background-color: rgb(246,243,48)")
        self.mainFrame.layout().addWidget(LADchangeIslandButton)
        LADchangeIslandButton.connect('clicked(bool)', self.onLADchangeIslandButtonClicked)

        # The Input Left Circumflex (LCX) Label Selector
        LCXchangeIslandButton = qt.QPushButton("LCX")
        LCXchangeIslandButton.toolTip = "Label - Left Circumflex (LCX)"
        LCXchangeIslandButton.setStyleSheet("background-color: rgb(94,170,200)")
        self.mainFrame.layout().addWidget(LCXchangeIslandButton)
        LCXchangeIslandButton.connect('clicked(bool)', self.onLCXchangeIslandButtonClicked)

        # The Input Right Coronary Artery (RCA) Label Selector
        RCAchangeIslandButton = qt.QPushButton("RCA")
        RCAchangeIslandButton.toolTip = "Label - Right Coronary Artery (RCA)"
        RCAchangeIslandButton.setStyleSheet("background-color: rgb(222,60,30)")
        self.mainFrame.layout().addWidget(RCAchangeIslandButton)
        RCAchangeIslandButton.connect('clicked(bool)', self.onRCAchangeIslandButtonClicked)

        # The Default Label Selector
        defaultChangeIslandButton = qt.QPushButton("Default")
        defaultChangeIslandButton.toolTip = "Label - Default"
        defaultChangeIslandButton.setStyleSheet("background-color: rgb(81,208,35)")
        self.mainFrame.layout().addWidget(defaultChangeIslandButton)
        defaultChangeIslandButton.connect('clicked(bool)', self.onDefaultChangeIslandButtonClicked)

        # create all of the buttons
        # createButtonRow() ensures that only effects in self.effects are exposed,
        self.createButtonRow( ("PreviousCheckPoint", "NextCheckPoint", "DefaultTool", "PaintEffect"), rowLabel="Undo/Redo/Default: " )

        extensions = []
        for k in slicer.modules.editorExtensions:
            extensions.append(k)
        self.createButtonRow( extensions )
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

        self.LMchangeIslandButton = LMchangeIslandButton
        self.LADchangeIslandButton = LADchangeIslandButton
        self.LCXchangeIslandButton = LCXchangeIslandButton
        self.RCAchangeIslandButton = RCAchangeIslandButton
        self.defaultChangeIslandButton = defaultChangeIslandButton

        vbox.addStretch(1)

        self.updateUndoRedoButtons()

    def onLMchangeIslandButtonClicked(self):
        self.changeIslandButtonClicked(2)

    def onLADchangeIslandButtonClicked(self):
        self.changeIslandButtonClicked(3)

    def onLCXchangeIslandButtonClicked(self):
        self.changeIslandButtonClicked(4)

    def onRCAchangeIslandButtonClicked(self):
        self.changeIslandButtonClicked(5)

    def onDefaultChangeIslandButtonClicked(self):
        self.changeIslandButtonClicked(1)

    def changeIslandButtonClicked(self, label):
        self.selectEffect("ChangeIslandEffect")
        self.editUtil.setLabel(label)
