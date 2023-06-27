import shutil
from pathlib import Path

REQUIRED_CODE_FILES = [
    "wolfgang.py",
    "similarity.py",
]

def update_from_original_repo():
    streamlit_path = Path(__file__).parent
    tutor_path = streamlit_path.parent / "simply_tutor"
    
    shutil.copytree(tutor_path / "faiss_index", streamlit_path / "faiss_index", dirs_exist_ok=True)
    shutil.copy(tutor_path / "prompts" / "master.txt", streamlit_path / "prompt.txt")
    
    for filename in REQUIRED_CODE_FILES:
        shutil.copy(tutor_path / "src" / filename, streamlit_path / filename)
    
    
if __name__ == "__main__":
    update_from_original_repo()