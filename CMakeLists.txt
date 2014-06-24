cmake_minimum_required(VERSION 2.8.9)

project(CardiacAgastonMeasures)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://www.example.com/Slicer/Extensions/CardiacAgastonMeasures")
set(EXTENSION_CATEGORY "Cardiac")
set(EXTENSION_CONTRIBUTORS "Jessica Forbes (UIowa), Hans Johnson (UIowa)")
set(EXTENSION_DESCRIPTION "This module will auto-segment the coronary calcium in Cardiac CT scans and then calculate the Agatston score and label statistics")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/CardiacAgastonMeasures/CardiacAgastonMeasures.png")
set(EXTENSION_SCREENSHOTURLS "http://www.na-mic.org/Wiki/images/6/63/CardiacAgatstonMeasuresModuleScreenshot.jpg")

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(CardiacAgatstonMeasures)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
