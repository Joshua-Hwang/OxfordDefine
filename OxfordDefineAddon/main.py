import os
import json

from . import oxford
from anki.hooks import addHook
from aqt.utils import showInfo, tooltip

KEY_FIELD = 0 # already contains word and must append audio
DEFINITION_FIELD = 1
PRIMARY_SHORTCUT = "ctrl+alt+d"

def insertDefinition(editor):
    # Get the word
    word = ""
    try:
        word = editor.note.fields[0]
        if word == "" or word.isspace():
            raise KeyError() # Purely to jump to the tooltip here
    except (AttributeError, KeyError) as e:
        tooltip("OxfordDefine: No text found in note fields.")
        return

    wordInfos = oxford.getEntry(word)
    if not wordInfos:
        lemmas = oxford.getLemmas(word)
        try:
            wordInfos = oxford.getEntry(lemmas[0])
        except KeyError as e:
            tooltip(f"OxfordDefine: Could not root words for {word}.")
            return

    definition = ""
    allSounds = []
    for wordInfo in wordInfos['results']:
        ################# Audio #################
        if "pronunciations" in wordInfo:
            allSounds = [editor.urlToLink(url).strip() for url in wordInfo["pronunciations"]]

        ########## Definition format ##########
        definition += '<b>' + wordInfo['lexicalCategory'] + '.</b><br>'
        definition += '<br>'.join(wordInfo['definitions']) + '<br>'
        if 'example' in wordInfo:
            definition += 'e.g. ' + f'"{wordInfo["example"]}"' + '<br>'
        if 'etymologies' in wordInfo:
            definition += '<br>'.join(wordInfo['etymologies']) + '<br>'
        definition += "<br>"

    ############# Output ##############
    editor.note.fields[KEY_FIELD] = wordInfos["id"] + '<br>'.join(set(allSounds))
    editor.note.fields[DEFINITION_FIELD] = definition
    editor.loadNote()

def addMyButton(buttons, editor):
    oxfordButton = editor.addButton(icon=os.path.join(os.path.dirname(__file__), "images", "books16.png"),
                                    cmd="OxDict",
                                    func=insertDefinition,
                                    tip=f"Oxford Define Word {PRIMARY_SHORTCUT}",
                                    toggleable=False,
                                    label="",
                                    keys=PRIMARY_SHORTCUT,
                                    disables=False)
    buttons.append(oxfordButton)
    return buttons

addHook("setupEditorButtons", addMyButton)

