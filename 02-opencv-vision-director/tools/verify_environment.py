import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vision.core import version_evidence
import cv2
out=Path(__file__).resolve().parents[1]/'runtime';out.mkdir(exist_ok=True)
evidence=version_evidence();(out/'version.json').write_text(json.dumps(evidence,indent=2));(out/'opencv-build.txt').write_text(cv2.getBuildInformation());print(json.dumps(evidence,indent=2))
