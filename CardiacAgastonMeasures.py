from __main__ import vtk, qt, ctk, slicer

#
# CardiacAgastonMeasures
#

class CardiacAgastonMeasures:
    def __init__(self, parent):
        parent.title = "Cardiac Agaston Measures"
        parent.categories = ["Cardiac Agaston Measures"]
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
# CardiacAgastonMeasuresWidget
#

class CardiacAgastonMeasuresWidget:
    def __init__(self, parent = None):
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
        
        # Collapsible button
        sampleCollapsibleButton = ctk.ctkCollapsibleButton()
        sampleCollapsibleButton.text = "A collapsible button"
        self.layout.addWidget(sampleCollapsibleButton)
        
        # Layout within the sample collapsible button
        sampleFormLayout = qt.QFormLayout(sampleCollapsibleButton)
        
        # HelloWorld button
        helloWorldButton = qt.QPushButton("Hello world")
        helloWorldButton.toolTip = "Print 'Hello world' in standard output"
        sampleFormLayout.addWidget(helloWorldButton)
        helloWorldButton.connect('clicked(bool)',self.onHelloWorldButtonClicked)
        
        
        # Add vertical spacer
        self.layout.addStretch(1)
        
        # Set local var as instance attribute
        self.helloWorldButton = helloWorldButton
        
    def onHelloWorldButtonClicked(self):
        print "Hey World !"
        qt.QMessageBox.information( slicer.util.mainWindow(), 'Slicer Python', 'Hello There!!!')

