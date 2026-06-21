## MARCHLAND — Ren'Py options and build configuration.
##
## Distribution note (v0.1.0): Mac only. numpy==2.4.6 ships only a
## cp312-cp312-macosx_11_0_arm64 wheel for Python 3.12. Linux/Windows
## players must run from source with the Ren'Py 8.5.3 SDK.

## ---------------------------------------------------------------------------
## Basics

define config.name = "MARCHLAND"
define config.version = "0.1.0"

## ---------------------------------------------------------------------------
## Sounds / Music (none for v0.1.0)

define config.has_sound = False
define config.has_music = False
define config.has_voice = False

## ---------------------------------------------------------------------------
## Transitions — none; this is a text/data game

define config.enter_transition = None
define config.exit_transition = None

## ---------------------------------------------------------------------------
## Build classification

init python:
    build.name = "marchland"
    build.executable_name = "marchland"

    ## python-packages/ goes in all platform packages
    build.classify("game/python-packages/**", "all")

    ## Exclude dev/source artifacts
    build.classify("**/__pycache__/**", None)
    build.classify("**/*.pyc", None)
    build.classify("**/*.pyo", None)
    build.classify("**/*.dist-info/**", None)
    build.classify("**/.DS_Store", None)
    build.classify("**/*.egg-info/**", None)
