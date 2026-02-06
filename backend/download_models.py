
import sys
import subprocess

def install_model(model_name):
    print(f"Downloading {model_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "spacy", "download", model_name])
        print(f"Successfully downloaded {model_name}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to download {model_name}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    models = ["en_core_web_sm", "ru_core_news_sm"]
    for model in models:
        install_model(model)
