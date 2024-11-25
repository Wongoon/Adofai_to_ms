from tkinter import Tk, filedialog
import json, os
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString

def upload_file():
    root = Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title = "파일을 선택하세요",
        filetypes = [
            ("All Files", "*.*"),
            ("JSON Files", "*.json"),
            ("Text Files", "*.txt"),
        ],
    )

    if file_path:
        file_name = os.path.basename(file_path)
        print(f"선택된 파일 경로: {file_path}")
        return file_path, file_name
    else:
        print("파일이 선택되지 않았습니다.")
        return None


def calculate_perceived_bpm(currentTile, next, bpm, isSwing):
    angle = (currentTile - next + 540) % 360
    if isSwing:
        angle = 360 - angle
    if angle == 0:
        angle = 360
    rbpm = bpm / (angle / 180)
    rbpms.append(rbpm)

def angle_to_ms(rbpms):
  global current
  msList = []
  for i in range(0, len(rbpms)):
    rbpm = rbpms[i]
    ms = ((60 / rbpm) * 1000)
    current += ms
    msList.append(current)
  return msList

def create_full_xml(msList, bpm_list):
    root = ET.Element("root")

    bpm_parent = ET.SubElement(root, "bpm")
    for bpm_info in bpm_list:
        bpm = ET.SubElement(bpm_parent, "bpm")
        bpm.set("tick", str(bpm_info["tick"]))
        bpm.set("bpm", str(bpm_info["bpm"]))

    note_list_parent = ET.SubElement(root, "note_list")
    for idx, ms in enumerate(msList):
        note = ET.SubElement(note_list_parent, "note")
        note.set("tick", f"{ms:.2f}")
        note.set("line", "1")

    tree = ET.ElementTree(root)
    return tree

def format_xml(file_path):
    """포맷팅된 XML 파일 저장"""
    with open(file_path, "r", encoding="utf-8") as file:
        rough_string = file.read()
    
    parsed = parseString(rough_string)
    pretty_xml = parsed.toprettyxml(indent="  ")

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(pretty_xml)
    print(f"포맷팅된 XML이 저장되었습니다: {file_path}")

if __name__ == "__main__":
    file_path, file_name = upload_file()
    
    names = file_name.split('.')
    name = names[0]

    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(e)
        except Exception as e:
            print(e)

    bpm = data["settings"]["bpm"]
    initBpm = bpm
    angledatas = data["angleData"]
    isSwing = False
    rbpms = []
    actions = data["actions"]
    eventSwing = ""
    eventSpeed = ""
    current = 0

    for i in range(0, len(angledatas)):
        eventSwing = ""
        eventSpeed = ""
        for j in range(0, len(actions)):
            if actions[j]['floor'] == i:
                if actions[j]['eventType'] == 'SetSpeed':
                    eventSpeed = actions[j]
                elif actions[j]['eventType'] == 'Twirl':
                    eventSwing = actions[j]
        if type(eventSpeed) == dict:
            if eventSpeed.get('speedType') == 'Bpm':
                bpm = eventSpeed.get('beatsPerMinute')
            elif eventSpeed.get('speedType') == 'Multiplier':
                bpm = bpm * eventSpeed.get('bpmMultiplier')
        if type(eventSwing) == dict:
            isSwing = not isSwing
        if i == 0:
            calculate_perceived_bpm(0, angledatas[i], bpm, isSwing)
            continue
        calculate_perceived_bpm(angledatas[i - 1], angledatas[i], bpm, isSwing)

    msList = angle_to_ms(rbpms)

    bpm_list = [
        {"tick": 0, "bpm": initBpm}
    ]

    xml_tree = create_full_xml(msList, bpm_list)

    output_file = name + ".xml"
    xml_tree.write(output_file, encoding="utf-8", xml_declaration=True)
    
    format_xml(output_file)
