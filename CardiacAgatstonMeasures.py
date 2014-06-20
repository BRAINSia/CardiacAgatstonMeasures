from __main__ import vtk, qt, ctk, slicer
import unittest
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
        parent.categories = ["Testing.TestCases"]
        parent.dependencies = []
        parent.contributors = ["Jessica Forbes (SINAPSE)",
                               "Hans Johnson (SINAPSE)"]
        parent.helpText = """This module will auto-segment the calcium
        deposits in Cardiac CT scans. The user first opens an image using
        either "Add Data" or "DICOM".  Then selects the radio button for
        either 80 KEV or 120 KEV. Then select the "Threshold Volume"
        button. A thesholded label image will be created using a lower
        threshold of 130 for 120 KEV or 167 for 80 KEV.  The user then
        selects one of the five colored buttons: 1) Default - default
        color of thresholded pixels, 2) LM - Left Main, 3) LAD - Left
        Arterial Descending, 4) LCX - Left Circumflex, 5) RCA - Right
        Coronary Artery. Note that the numbers 1-5 can also be used as
        shortcut keys for these five buttons. The user selects "Apply"
        to calculate the Agatston Scores and Label Statistics for each
        label and all labels combined. These table values can then be
        saved in an Excel (or Excel compatible) file using the "Save"
        button."""
        parent.acknowledgementText = """This file was originally developed
         by Jessica Forbes and Hans Johnson of the SINAPSE Lab at the
         University of Iowa.""" # replace with organization, grant and thanks.
        self.parent = parent

        # Add this test to the SelfTest module's list for discovery when the module
        # is created.  Since this module may be discovered before SelfTests itself,
        # create the list if it doesn't already exist.
        try:
            slicer.selfTests
        except AttributeError:
            slicer.selfTests = {}
        slicer.selfTests['CardiacAgatstonMeasures'] = self.runTest

    def runTest(self):
        tester = CardiacAgatstonMeasuresTest()
        tester.runTest()

#
# CardiacAgatstonMeasuresWidget
#

class CardiacAgatstonMeasuresWidget:
    def __init__(self, parent = None):
        self.currentRegistrationInterface = None
        self.changeIslandTool = None
        self.editUtil = EditorLib.EditUtil.EditUtil()
        self.inputImageNode = None
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
            self.reloadButton.connect('clicked()', self.onReload)

            # reload and test button
            # (use this during development, but remove it when delivering
            #  your module to users)
            self.reloadAndTestButton = qt.QPushButton("Reload and Test")
            self.reloadAndTestButton.toolTip = "Reload this module and then run the self tests."
            reloadFormLayout.addWidget(self.reloadAndTestButton)
            self.reloadAndTestButton.connect('clicked()', self.onReloadAndTest)

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

        # sets the layout to Red Slice Only
        layoutManager = slicer.app.layoutManager()
        layoutManager.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)

    def onThresholdButtonClicked(self):
        if not self.KEV120.checked and not self.KEV80.checked:
            qt.QMessageBox.warning(slicer.util.mainWindow(),
                "Select KEV", "The KEV (80 or 120) must be selected to continue.")
            return

        self.inputImageNode = self.inputSelector.currentNode()
        inputVolumeName = self.inputImageNode.GetName()

        self.CardiacAgatstonMeasuresLogic = CardiacAgatstonMeasuresLogic(
            self.KEV80.checked, self.KEV120.checked, inputVolumeName)
        self.CardiacAgatstonMeasuresLogic.runThreshold()

        self.thresholdButton.enabled = False

        # Creates and adds the custom Editor Widget to the module
        self.localCardiacEditorWidget = CardiacEditorWidget(parent=self.parent, showVolumesFrame=False)
        self.localCardiacEditorWidget.setup()
        self.localCardiacEditorWidget.enter()

        # Adds Label Statistics Widget to Module
        self.localLabelStatisticsWidget = CardiacStatisticsWidget(self.KEV120, self.KEV80,
                                                             self.localCardiacEditorWidget,
                                                             parent=self.parent)
        self.localLabelStatisticsWidget.setup()

    def onReload(self,moduleName="CardiacAgatstonMeasures"):
        """Generic reload method for any scripted module.
            ModuleWizard will subsitute correct default moduleName.
            Note: customized for use in CardiacAgatstonModule
            """
        import imp, sys, os, slicer

        # selects default tool to stop the ChangeIslandTool
        if self.localCardiacEditorWidget:
            self.localCardiacEditorWidget.exit()

        # clears the mrml scene
        slicer.mrmlScene.Clear(0)

        globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)

    def onReloadAndTest(self,moduleName="CardiacAgatstonMeasures"):
        try:
            self.onReload()
            evalString = 'globals()["%s"].%sTest()' % (moduleName, moduleName)
            tester = eval(evalString)
            tester.runTest()
        except Exception, e:
            import traceback
            traceback.print_exc()
            qt.QMessageBox.warning(slicer.util.mainWindow(),
              "Reload and Test", 'Exception!\n\n' + str(e) +
                                 "\n\nSee Python Console for Stack Trace")

#
# CardiacAgatstonMeasuresLogic
#

class CardiacAgatstonMeasuresLogic:
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget
    """
    def __init__(self, KEV80=False, KEV120=False, inputVolumeName=None):
        self.lowerThresholdValue = None
        self.upperThresholdValue = 5000
        self.editUtil = EditorLib.EditUtil.EditUtil()
        self.KEV80 = KEV80
        self.KEV120 = KEV120
        self.inputVolumeName = inputVolumeName
        self.calciumLabelNode = None

        # imports custom Slicer lookup color table file
        self.cardiacLutNode = slicer.util.getNode('cardiacLUT')
        if not self.cardiacLutNode:
            slicer.util.loadColorTable('/scratch/cardiacLUT.ctbl')

    def runThreshold(self):

        # Sets minimum threshold value based on KEV80 or KEV120
        if self.KEV80:
            self.lowerThresholdValue = 167
            calciumName = "{0}_80KEV_{1}HU_Calcium_Label".format(self.inputVolumeName, self.lowerThresholdValue)
        elif self.KEV120:
            self.lowerThresholdValue = 130
            calciumName = "{0}_120KEV_{1}HU_Calcium_Label".format(self.inputVolumeName, self.lowerThresholdValue)

        print "Thresholding at {0}".format(self.lowerThresholdValue)
        inputVolume = su.PullFromSlicer(self.inputVolumeName)
        thresholdImage = sitk.BinaryThreshold(inputVolume, self.lowerThresholdValue, self.upperThresholdValue)
        castedThresholdImage = sitk.Cast(thresholdImage, sitk.sitkInt16)
        su.PushLabel(castedThresholdImage, calciumName)

        self.assignLabelLUT(calciumName)
        self.setLowerPaintThreshold()

    def assignLabelLUT(self, calciumName):
        # Set the color lookup table (LUT) to the custom cardiacLUT
        self.calciumLabelNode = slicer.util.getNode(calciumName)
        self.cardiacLutNode = slicer.util.getNode(pattern='cardiacLUT')
        cardiacLutID = self.cardiacLutNode.GetID()
        calciumDisplayNode = self.calciumLabelNode.GetDisplayNode()
        calciumDisplayNode.SetAndObserveColorNodeID(cardiacLutID)

    def setLowerPaintThreshold(self):
        # sets parameters for paint specific to KEV threshold level
        parameterNode = self.editUtil.getParameterNode()
        parameterNode.SetParameter("LabelEffect,paintOver","1")
        parameterNode.SetParameter("LabelEffect,paintThreshold","1")
        parameterNode.SetParameter("LabelEffect,paintThresholdMin","{0}".format(self.lowerThresholdValue))
        parameterNode.SetParameter("LabelEffect,paintThresholdMax","{0}".format(self.upperThresholdValue))

    def hasImageData(self,volumeNode):
        """This is a dummy logic method that
        returns true if the passed in volume
        node has valid image data
        """
        if not volumeNode:
            print('no volume node')
            return False
        if volumeNode.GetImageData() == None:
            print('no image data')
            return False
        return True

    def hasCorrectLUTData(self,lutNode):
        """This is a dummy logic method that
        returns true if the passed in LUT
        node has valid LUT table data
        """
        if not lutNode:
            print('no Cardiac LUT node')
            return False
        number = lutNode.GetLookupTable().GetNumberOfAvailableColors()
        if number == 7:
            return True
        else:
            print('there should be 7 colors in LUT table, there are %s'%number)
            return False

    def delayDisplay(self,message,msec=1000):
        #
        # logic version of delay display
        #
        print(message)
        self.info = qt.QDialog()
        self.infoLayout = qt.QVBoxLayout()
        self.info.setLayout(self.infoLayout)
        self.label = qt.QLabel(message,self.info)
        self.infoLayout.addWidget(self.label)
        qt.QTimer.singleShot(msec, self.info.close)
        self.info.exec_()

    def takeScreenshot(self,name,description,type=-1):
        # show the message even if not taking a screen shot
        self.delayDisplay(description)

        if self.enableScreenshots == 0:
            return

        lm = slicer.app.layoutManager()
        # switch on the type to get the requested window
        widget = 0
        if type == -1:
            # full window
            widget = slicer.util.mainWindow()
        elif type == slicer.qMRMLScreenShotDialog().FullLayout:
            # full layout
            widget = lm.viewport()
        elif type == slicer.qMRMLScreenShotDialog().ThreeD:
            # just the 3D window
            widget = lm.threeDWidget(0).threeDView()
        elif type == slicer.qMRMLScreenShotDialog().Red:
            # red slice window
            widget = lm.sliceWidget("Red")
        elif type == slicer.qMRMLScreenShotDialog().Yellow:
            # yellow slice window
            widget = lm.sliceWidget("Yellow")
        elif type == slicer.qMRMLScreenShotDialog().Green:
            # green slice window
            widget = lm.sliceWidget("Green")

        # grab and convert to vtk image data
        qpixMap = qt.QPixmap().grabWidget(widget)
        qimage = qpixMap.toImage()
        imageData = vtk.vtkImageData()
        slicer.qMRMLUtils().qImageToVtkImageData(qimage,imageData)

        annotationLogic = slicer.modules.annotations.logic()
        annotationLogic.CreateSnapShot(name, description, type, self.screenshotScaleFactor, imageData)

    def run(self,inputVolume,outputVolume,enableScreenshots=0,screenshotScaleFactor=1):
        """
        Run the actual algorithm
        """

        self.delayDisplay('Running the aglorithm')

        self.enableScreenshots = enableScreenshots
        self.screenshotScaleFactor = screenshotScaleFactor

        self.takeScreenshot('CardiacAgatstonMeasures-Start','Start',-1)

        return True

class CardiacAgatstonMeasuresTest(unittest.TestCase):
    """
    This is the test case for your scripted module.
    """

    def delayDisplay(self,message,msec=1000):
        """This utility method displays a small dialog and waits.
        This does two things: 1) it lets the event loop catch up
        to the state of the test so that rendering and widget updates
        have all taken place before the test continues and 2) it
        shows the user/developer/tester the state of the test
        so that we'll know when it breaks.
        """
        print(message)
        self.info = qt.QDialog()
        self.infoLayout = qt.QVBoxLayout()
        self.info.setLayout(self.infoLayout)
        self.label = qt.QLabel(message,self.info)
        self.infoLayout.addWidget(self.label)
        qt.QTimer.singleShot(msec, self.info.close)
        self.info.exec_()

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        self.delayDisplay("Closing the scene")
        layoutManager = slicer.app.layoutManager()
        layoutManager.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_CardiacAgatstonMeasures1()
        self.test_CardiacAgatstonMeasures2()
        self.test_CardiacAgatstonMeasures3()

    def test_CardiacAgatstonMeasures1(self):
        """ Ideally you should have several levels of tests.  At the lowest level
        tests sould exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting Test Part 1 - Importing heart scan")

        try:
            #
            # first, get some data
            #
            import urllib
            # downloads = (
            #     ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
            #     )
            #
            # for url,name,loader in downloads:
            #   filePath = slicer.app.temporaryPath + '/' + name
            #   if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
            #     print('Requesting download %s from %s...\n' % (name, url))
            #     urllib.urlretrieve(url, filePath)
            #   if loader:
            #     print('Loading %s...\n' % (name,))
            #     loader(filePath)

            slicer.util.loadVolume('/scratch/p1_1.nii.gz')  #added tmp because slicer.kitware.com download not working
            self.delayDisplay('Finished with download and loading\n')

            volumeNode = slicer.util.getNode(pattern="p1_1") #added tmp because slicer.kitware.com download not working
            # volumeNode = slicer.util.getNode(pattern="FA")
            logic = CardiacAgatstonMeasuresLogic()
            self.assertTrue( logic.hasImageData(volumeNode) )
            self.delayDisplay('Test Part 1 passed!')
        except Exception, e:
            import traceback
            traceback.print_exc()
            self.delayDisplay('Test caused exception!\n' + str(e))

    def test_CardiacAgatstonMeasures2(self):
        """ Level two test. Tests if the thresholded label
        image is created and if CardiacLUT file was
        imported correctly.
        """
        self.delayDisplay("Starting Test Part 2 - Thresholding")

        try:
            m = slicer.util.mainWindow()
            m.moduleSelector().selectModule('CardiacAgatstonMeasures')

            widget = slicer.modules.CardiacAgatstonMeasuresWidget
            self.delayDisplay("Opened CardiacAgatstonMeasuresWidget")

            widget.KEV120.setChecked(1)
            self.delayDisplay("Checked the KEV120 button")

            widget.onThresholdButtonClicked()
            self.delayDisplay("Threshold button selected")

            logic = CardiacAgatstonMeasuresLogic()

            labelNode = slicer.util.getNode(pattern="p1_1_120KEV_130HU_Calcium_Label")
            self.assertTrue( logic.hasImageData(labelNode) )
            self.delayDisplay("Thresholded label created and pushed to Slicer")

            lutNode = slicer.util.getNode(pattern="cardiacLUT")
            self.assertTrue( logic.hasCorrectLUTData(lutNode) )
            self.delayDisplay("Cardiac LUT imported into Slicer")

            self.delayDisplay('Test Part 2 passed!')
        except Exception, e:
            import traceback
            traceback.print_exc()
            self.delayDisplay('Test caused exception!\n' + str(e))

    def test_CardiacAgatstonMeasures3(self):
        """ Level three test. Tests if the Editor tools
        and five label buttons work properly.
        """
        self.delayDisplay("Starting Test Part 3 - Paint and Statistics")

        try:
            widget = slicer.modules.CardiacAgatstonMeasuresWidget
            self.delayDisplay("Opened CardiacAgatstonMeasuresWidget")

            # toolsBox = widget.localCardiacEditorWidget.toolsBox
            # toolsBox.onLCXchangeIslandButtonClicked()

            #
            # got to the editor and do some drawing
            #
            self.delayDisplay("Paint some things")
            editUtil = EditorLib.EditUtil.EditUtil()
            lm = slicer.app.layoutManager()
            paintEffect = EditorLib.PaintEffectOptions()
            paintEffect.setMRMLDefaults()
            paintEffect.__del__()
            sliceWidget = lm.sliceWidget('Red')
            paintTool = EditorLib.PaintEffectTool(sliceWidget)
            editUtil.setLabel(5)
            (x, y) = self.rasToXY((38,165,-122), sliceWidget)
            paintTool.paintAddPoint(x, y)
            paintTool.paintApply()
            editUtil.setLabel(3)
            (x, y) = self.rasToXY((12.5,171,-122), sliceWidget)
            paintTool.paintAddPoint(x, y)
            paintTool.paintApply()
            paintTool.cleanup()
            paintTool = None
            self.delayDisplay("Painted calcium for LAD and RCA labels")

            self.delayDisplay("Apply pressed - calculating Agatston scores/statistics")
            widget.localLabelStatisticsWidget.onApply()

            scores = widget.localLabelStatisticsWidget.logic.AgatstonScoresPerLabel
            testScores = {0: 0, 1: 0, 2: 0, 3: 2.8703041076660174,
                          4: 0, 5: 45.22903442382816, 6: 48.099338531494176}
            self.assertTrue( scores == testScores )
            self.delayDisplay("Agatston scores/statistics are correct")

            self.delayDisplay("Test Part 3 passed!")

        except Exception, e:
            import traceback
            traceback.print_exc()
            self.delayDisplay('Test caused exception!\n' + str(e))

    def rasToXY(self, rasPoint, sliceWidget):
        sliceLogic = sliceWidget.sliceLogic()
        sliceNode = sliceLogic.GetSliceNode()
        rasToXY = vtk.vtkMatrix4x4()
        rasToXY.DeepCopy(sliceNode.GetXYToRAS())
        rasToXY.Invert()
        xyzw = rasToXY.MultiplyPoint(rasPoint+(1,))
        x = int(round(xyzw[0]))
        y = int(round(xyzw[1]))
        return x, y

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
        if not self.fileDialog:
            self.fileDialog = qt.QFileDialog(self.parent)
            self.fileDialog.options = self.fileDialog.DontUseNativeDialog
            self.fileDialog.acceptMode = self.fileDialog.AcceptOpen
            self.fileDialog.fileMode = self.fileDialog.DirectoryOnly
            self.fileDialog.connect("fileSelected(QString)", self.onDirSelected)
        self.fileDialog.show()

    def onDirSelected(self, dirName):
        # saves the current scene to selected folder
        l = slicer.app.applicationLogic()
        l.SaveSceneToSlicerDataBundleDirectory(dirName, None)

        # saves the csv files to selected folder
        csvFileName = os.path.join(dirName, "{0}_Agatston_Scores.csv".format(os.path.split(dirName)[1]))
        self.logic.saveStats(csvFileName)

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

        for i in xrange(lo,7):
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
            if i != 6:
                thresholder.ThresholdBetween(i,i)
            else: # label 6 is the total calcium pixels in labels 2, 3, 4 and 5
                thresholder.ThresholdBetween(2,5)
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
        self.computeOverallAgatstonScore(sliceAgatstonPerLabel)

    def computeOverallAgatstonScore(self, sliceAgatstonPerLabel):
        self.AgatstonScoresPerLabel = {}
        # labels 0 and 1 should not have an Agatston score
        self.AgatstonScoresPerLabel[0] = 0
        self.AgatstonScoresPerLabel[1] = 0
        for (label, scores) in sliceAgatstonPerLabel.items():
            labelScore =  sum(scores)
            self.AgatstonScoresPerLabel[label] = labelScore
        # label 6 is the total of all of labels 2 - 5
        self.AgatstonScoresPerLabel[6] = sum(self.AgatstonScoresPerLabel.values())

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

        for label in all_labels:
            if label == 0 or label == 1:
                continue
            binaryThresholdFilterImage = sitk.BinaryThreshold(calcium, label, label)
            ConnectedComponentImage = sitk.ConnectedComponent(binaryThresholdFilterImage)
            RelabeledComponentImage = sitk.RelabelComponent(ConnectedComponentImage)
            ImageSpacing = RelabeledComponentImage.GetSpacing()
            ImageIndex = range(0, RelabeledComponentImage.GetSize()[2])
            for index in ImageIndex:
                slice_calcium = RelabeledComponentImage[:,:,index]
                slice_img = heart[:,:,index]
                slice_ls = sitk.LabelStatisticsImageFilter()
                slice_ls.Execute(slice_img,slice_calcium)
                if sitk.Version().MajorVersion() > 0 or sitk.Version().MinorVersion() >= 9:
                    compontent_labels = slice_ls.GetLabels()
                else: #if sitk version < 0.9 then use older function call GetValidLabels
                    compontent_labels = slice_ls.GetValidLabels()
                for sublabel in compontent_labels:
                    if sublabel == 0:
                        continue
                    AgatstonValue = 0.0
                    if slice_ls.HasLabel(sublabel):
                        slice_count = slice_ls.GetCount(sublabel)
                        slice_area = slice_count*ImageSpacing[0]*ImageSpacing[1]
                        slice_max = slice_ls.GetMaximum(sublabel)
                        slice_Agatston = slice_area * self.KEV2AgatstonIndex( slice_max )
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
            ('1', self.toolsBox.onDefaultChangeIslandButtonClicked),
            ('2', self.toolsBox.onLMchangeIslandButtonClicked),
            ('3', self.toolsBox.onLADchangeIslandButtonClicked),
            ('4', self.toolsBox.onLCXchangeIslandButtonClicked),
            ('5', self.toolsBox.onRCAchangeIslandButtonClicked),
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

        # The Default Label Selector
        defaultChangeIslandButton = qt.QPushButton("Default")
        defaultChangeIslandButton.toolTip = "Label - Default"
        defaultChangeIslandButton.setStyleSheet("background-color: rgb(81,208,35)")
        self.mainFrame.layout().addWidget(defaultChangeIslandButton)
        defaultChangeIslandButton.connect('clicked(bool)', self.onDefaultChangeIslandButtonClicked)

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

        # create all of the buttons
        # createButtonRow() ensures that only effects in self.effects are exposed,
        self.createButtonRow( ("PreviousCheckPoint", "NextCheckPoint",
                               "DefaultTool", "PaintEffect"),
                              rowLabel="Undo/Redo/Default: " )

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