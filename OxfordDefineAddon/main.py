import os
import sys
import json

from anki.hooks import addHook
from aqt import mw
from aqt.utils import showInfo, tooltip
from requests.exceptions import HTTPError

from .oxford import setOxfordKey, getLemmas, getEntry

KEY_FIELD = 0 # already contains word and must append audio
DEFINITION_FIELD = 1

WHAT_TO_INSERT = "all"
PRIMARY_SHORTCUT = "ctrl+alt+d"

def getConfig():
    global WHAT_TO_INSERT
    global PRIMARY_SHORTCUT
    config = mw.addonManager.getConfig(__name__) # type: ignore
    setOxfordKey(config["APP_ID"], config["APP_KEY"]) # type: ignore

    WHAT_TO_INSERT = config["WHAT_TO_INSERT"] # type: ignore
    # This won't actually be updated for the button
    PRIMARY_SHORTCUT = config["PRIMARY_SHORTCUT"] # type: ignore

def insertDefinition(editor):
    # update config
    getConfig()

    # Get the word
    word = ""
    try:
        word = editor.note.fields[0]
        if word == "" or word.isspace():
            raise KeyError() # Purely to jump to the tooltip here
    except (AttributeError, KeyError) as e:
        tooltip("OxfordDefine: No text found in note fields.")
        return

    try:
        wordInfos = getEntry(word)
        if not wordInfos:
            raise HTTPError() # jump to exception handling
    except HTTPError as e:
        try:
            lemmas = getLemmas(word)
            wordInfos = getEntry(lemmas[0])
        except (HTTPError, KeyError) as e:
            tooltip(f"OxfordDefine: Could not root words for {word}.")
            return

    # Format word
    definition = ""
    soundURLs = set()
    for result in wordInfos['results']:
        for lexical in result:
            ########## Definition format ##########
            definition += '<hr>'
            definition += '<b>' + lexical['lexicalCategory'] + '.</b><br>'
            for entry in lexical['entries']:
                if "pronunciations" in entry: # sounds saved for later
                    soundURLs.update(entry["pronunciations"])

                for sense in entry['senses']:
                    definition += '<p>'
                    definition += '<br>'.join(sense['definitions']) + '<br>'
                    if 'example' in sense:
                        definition += '<b>e.g.</b> ' + '"' + sense['example'] + '"' + '<br>'
                    if 'notes' in entry:
                        definition += '<b>notes:</b> ' + '<br>'.join(entry['notes']) + '<br>'
                    definition += '</p>'

                if 'etymologies' in entry:
                    definition += '<h5>Origins:</h5> '
                    definition += '<br>'.join(entry['etymologies']) + '<br>'
                if 'notes' in entry:
                    definition += '<h5>Notes:</h5> '
                    definition += '<br>'.join(entry['notes']) + '<br>'

    ############# Output ##############
    if WHAT_TO_INSERT == 'all' or WHAT_TO_INSERT == 'pronunciation':
        sounds = [editor.urlToLink(url).strip() for url in soundURLs]
        editor.note.fields[KEY_FIELD] = wordInfos["word"] + ''.join(sounds)
    if WHAT_TO_INSERT == 'all' or WHAT_TO_INSERT == 'text':
        editor.note.fields[DEFINITION_FIELD] = definition
    editor.loadNote()

    # Focus back on zero field
    if editor.web:
        editor.web.eval("focusField(0);")

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

getConfig()
addHook("setupEditorButtons", addMyButton)
